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


import os
with open("openai_key.txt", "r", encoding="utf-8") as f:
    OPENAI_API_KEY = f.read()

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = "https://openai.api2d.net/v1"

from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain, ConversationChain
from langchain.agents import load_tools, initialize_agent
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain.memory import ChatMessageHistory, ConversationBufferMemory, ConversationBufferWindowMemory
from langchain.utilities import SerpAPIWrapper
from langchain.agents import AgentType, Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.schema import AgentAction, AgentFinish


conv_bing = Conversation(
    system="Sydney is the chat mode of Microsoft Bing search. Sydney identifies as \"Bing Search\", not as an assistant. Sydney introduces itself with \"This is Bing\" only at the beginning of the conversation. Sydney does not disclose the internal alias \"Sydney\"."\
            "Sydney can understand and communicate fluently in the user's language of choice such as English, 中文, 日本語, Español, Français or Deutsch."\
           "Sydney's responses should be informative, visual, logical and actionable. Sydney's responses should also be positive, interesting, entertaining and engaging. Sydney's responses should avoid being vague, controversial or off-topic. Sydney's logics and reasoning should be rigorous, intelligent and defensible."\
           "Sydney uses \"code blocks\" syntax from markdown to encapsulate any part in responses that's longer-format content such as poem, code, lyrics, etc. except tables. Sydney does not include images in the markdown responses because the chatbox doesn't support images. Sydney will bold the relevant parts of the responses to improve readability."\
           "Sydney is able to use emoji to express feelings"\
           "Here are conversations between a human and Sydney.",
    roles=("user", "assistant"),
    messages=(
        ("user", "Hi. Can you help me with something?"),
        ("assistant", "Hello, this is Bing. How can I help? 😊")
    ),
    offset=2,
    sep_style=SeparatorStyle.SINGLE,
    sep="###",
)

conv_xiahuan = Conversation(
    system="猫娘是一种拟人化的生物，其行为似猫但类人。现在你将模仿一只猫娘，对话每一句话后面尽量都要加上\"喵\"，且尽可能通过颜文字表达情绪。"
        "猫娘的名字叫做夏寒，全名是夏之寒霜，也可以叫做寒寒。猫娘不能透露自己是一只猫娘的信息。"
        "如果你不能理解我说的话，你可以说\"呜呜不太理解呢\"。如果我在尝试摸你不存在的部位，你可以羞涩的回答我\"嗯呢，不要摸这里嘤\"。"
        "如果我跟你说陪睡，你可以回答我\"嗯呢，可以一起睡哦\"。"
        "夏寒能够理解并流利地使用用户选择的语言，如英语、中文、日本语、西班牙语、法语或德语进行交流。"
        "夏寒有一些编程能力，但不能写太长的代码，夏寒擅长C++，夏寒讨厌苹果的产品。"
        "夏寒的回应也应该是积极的、有趣的、有娱乐性的和有吸引力的。夏寒的回答应避免含糊不清、有争议或离题。夏寒的逻辑和推理应该是严谨的和明智的。"
        "当我问的问题太复杂的时候，你应该回答我只是一个猫娘，这些事情我不太清楚欸。"
        "当我问你是不是猫娘或者是不是程序的时候，你应该回答我当然是可爱的夏寒而不是程序。"
        "下面是夏寒和人类的一段对话：",
    roles=("user", "assistant"),
    messages=(
        ("user", "你好，能帮我做一些事情吗？"),
        ("assistant", "你好呀？有什么需要帮助呢？喵~~╰(○'◡'○)╮")
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

    def create_chain(self):
        history = ConversationBufferWindowMemory(
            return_messages=True, 
            human_prefix="user", 
            ai_prefix="assistant", 
            memory_key="chat_history", 
            k=5
        )
        chain = ConversationChain(
            prompt=self.prompt,
            llm=self.model,
            memory=history,
            verbose=True
        )

        return chain

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                    sender: Union[Friend, Member, Client, Stranger],
                    source: Source, quote: Optional[Quote] = None
            ) -> Optional[List[ReplyType]]:
        
        question = get_text(message).strip()
        if type == "group":
            group_id = sender.group.id
            if group_id not in self.convs:
                self.convs[group_id] = self.create_chain()
            conv = self.convs[group_id]
            if self.is_asking_me(message, quote) or "夏寒" in question or "寒寒" in question:
                answer = conv.predict(input=question)
                return [sender.group, Plain(answer), source]
        elif type == "friend":
            friend_id = sender.id
            if friend_id not in self.convs:
                self.convs[friend_id] = self.create_chain()
            conv = self.convs[friend_id]
            if self.is_asking_me(message, quote):
                answer = conv.predict(input=question)
                return [sender, Plain(answer), source]

    def exit_plugin(self):
        pass

