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

conv_xiahan = Conversation(
    system="A chat between a curious human and an artificial intelligence assistant. "
           "The assistant gives helpful, detailed, and polite answers to the human's questions."
           "The name of assistant is XiaHan."
           "助手的名字叫做夏寒.",
    roles=("Human", "Assistant"),
    messages=(
        ("Human", "What are the key differences between renewable and non-renewable energy sources?"),
        ("Assistant",
            "Renewable energy sources are those that can be replenished naturally in a relatively "
            "short amount of time, such as solar, wind, hydro, geothermal, and biomass. "
            "Here are some key differences between renewable and non-renewable energy sources:\n"
            "1. Availability: Renewable energy sources are virtually inexhaustible, while non-renewable "
            "energy sources are finite and will eventually run out.\n"
            "2. Environmental impact: Renewable energy sources have a much lower environmental impact "
            "than non-renewable sources, which can lead to air and water pollution, greenhouse gas emissions, "
            "and other negative effects.\n"
            "3. Cost: Renewable energy sources can be more expensive to initially set up, but they typically "
            "have lower operational costs than non-renewable sources."),
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


class ChatPlugin(BasePlugin):
    def __init__(self, bot_id: int) -> None:
        self.bot_id = bot_id
        self.convs = {}

        self.enable()
    
    def enter_plugin(self):
        pass

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                    sender: Union[Friend, Member, Client, Stranger],
                    source: Source, quote: Optional[Quote] = None
            ) -> Optional[List[ReplyType]]:
        
        if type == "group":
            if self.is_asking_me(message, quote):
                question = get_text(message).strip()
                group_id = sender.group.id
                if group_id not in self.convs:
                    self.convs[group_id] = conv_xiahan.copy()
                answer = self._query(self.convs[group_id], sender.name, question)
                return [sender.group, Plain(answer), source]
        elif type == "friend":
            if self.is_asking_me(message, quote):
                question = get_text(message).strip()
                friend_id = sender.id
                if friend_id not in self.convs:
                    self.convs[friend_id] = conv_xiahan.copy()
                answer = self._query(self.convs[friend_id], sender.nickname, question)
                return [sender, Plain(answer), source]

    def _query(self, conv: Conversation, memberName: str, question: str) -> str:
        if len(conv.messages) > 23:
            conv.messages = conv.messages[:16] + conv.messages[len(conv.messages) - 20 + 16:]

        model_name = "vicuna-13b"
        max_new_tokens = 256
        worker_addr = "http://127.0.0.1:21002"

        conv.append_message(conv.roles[0] + f"({memberName})", question)
        prompt = conv.get_prompt()

        headers = {"User-Agent": "fastchat Client"}
        pload = {
            "model": model_name,
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "temperature": 0.7,
            "stop": conv.sep,
        }
        response = requests.post(worker_addr + "/worker_generate_stream", headers=headers,json=pload, stream=True)

        answer = ""
        for chunk in response.iter_lines(chunk_size=8192, decode_unicode=False, delimiter=b"\0"):
            if chunk:
                data = json.loads(chunk.decode("utf-8"))
                output = data["text"].split(conv.sep)[-1]
                # print(output, end="\r")
                answer = output

        remove_assistant = remove_prefix(answer.lstrip(), "Assistant: ")
        remove_human = remove_prefix(remove_assistant, "Human: ")
        conv.append_message(conv.roles[1], remove_human)
        return remove_human.rstrip()

    def exit_plugin(self):
        pass

