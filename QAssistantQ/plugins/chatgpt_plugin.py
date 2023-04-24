import argparse
import json
from typing import Any, List, Optional, Union

import requests

from .base_plugin import BasePlugin, MessageSourceType, ReplyType

from ..conversation import default_conversation, conv_templates, SeparatorStyle, Conversation

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Group, Client, Stranger
from graia.ariadne.message import Quote
from graia.ariadne.app import Source
from graia.ariadne.message.element import Element, Quote, Source, AtAll, At, Plain
from graia.ariadne.event.message import MessageEvent, FriendMessage, GroupMessage

import requests
import pytz
from datetime import datetime
import re

with open("openai_key.txt", "r", encoding="utf-8") as f:
    OPENAI_KEY = f.read()

conv_xiahan = Conversation(
    system="A chat between a curious human and an artificial intelligence assistant. "
           "The assistant gives helpful, detailed, and polite answers to the human's questions."
           "助手的名字叫做夏寒。",
    roles=("user", "assistant"),
    messages=(
        ("user", "你好"),
        ("assistant", "你好")
    ),
    offset=2,
    sep_style=SeparatorStyle.SINGLE,
    sep="###",
)

def remove_prefix(text: str, prefix: str):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def get_text(message: MessageChain) -> str:
    return "".join([plain.text for plain in message.get(Plain)])


class ChatGPTPlugin(BasePlugin):
    def __init__(self, bot_id: int) -> None:
        self.bot_id = bot_id
        self.convs = {}
        self.url = "https://openai.api2d.net/v1/chat/completions"
        self.enable()
    
    def enter_plugin(self):
        pass

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                    sender: Union[Friend, Member, Client, Stranger],
                    source: Source, quote: Optional[Quote] = None
            ) -> Optional[List[ReplyType]]:
        
        question = get_text(message).strip()
        if type == "group":
            group_id = sender.group.id
            if group_id not in self.convs:
                self.convs[group_id] = conv_xiahan.copy()
            conv = self.convs[group_id]
            if self.is_asking_me(message, quote):
                answer = self._query(conv, sender.name, question)
                return [sender.group, Plain(answer), source]
        elif type == "friend":
            friend_id = sender.id
            if friend_id not in self.convs:
                self.convs[friend_id] = conv_xiahan.copy()
            if self.is_asking_me(message, quote):
                answer = self._query(self.convs[friend_id], sender.nickname, question)
                return [sender, Plain(answer), source]

    def _query(self, conv: Conversation, memberName: str, question: str) -> str:
        if len(conv.messages) >= 12:
            conv.messages = conv.messages[-8:]
            # conv.messages = conv.messages[:conv_xiahan.offset] + conv.messages[len(conv.messages) - 8 + conv_xiahan.offset:]
        # print(conv.messages)
        conv.append_message(conv.roles[0], question)

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + OPENAI_KEY
        }
        json_data = {
            "model": "gpt-3.5-turbo",
            "stream": False,
            "temperature": 0.8,
            "max_tokens": 128,
            "messages": conv.to_openai_messages()
        }
        print(headers)
        print(json_data)
        response = requests.post(self.url, headers=headers, json=json_data, timeout=30)
        response_json = json.loads(response.text)
        if "object" in response_json and response_json["object"] == "error":
            print(response_json)
            return "OpenAI API 发生错误，详细信息：\n" + json.dumps(response_json)
        print(response_json)
        choices = response_json["choices"]
        first_choice = choices[0]
        message = first_choice["message"]
        answer = message["content"]
        answer = remove_prefix(answer.lstrip(), conv.roles[1] + ": ").rstrip()

        # def evaluate(match):
        #     return str(eval(match.group(1)))
        # answer = re.sub(r"{{(.*?)}}", evaluate, answer)

        conv.append_message(conv.roles[1], answer)
        return answer

    def exit_plugin(self):
        pass

