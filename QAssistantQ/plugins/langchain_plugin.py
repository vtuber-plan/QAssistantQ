import argparse
import json
import re
from typing import Any, List, Optional, Union

import requests

from .base_plugin import BasePlugin, MessageSourceType, ReplyType

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Group, Client, Stranger
from graia.ariadne.message import Quote
from graia.ariadne.app import Source
from graia.ariadne.message.element import Element, Quote, Source, AtAll, At, Plain
from graia.ariadne.event.message import MessageEvent, FriendMessage, GroupMessage

import requests

import os
with open("openai_key.txt", "r", encoding="utf-8") as f:
    OPENAI_API_KEY = f.read()

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = "https://openai.api2d.net/v1"

from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain, ConversationChain
from langchain.chains import SimpleSequentialChain
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
from langchain.agents import AgentType, Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser, ZeroShotAgent
from langchain.schema import AgentAction, AgentFinish

def remove_prefix(text: str, prefix: str):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def get_text(message: MessageChain) -> str:
    return "".join([plain.text for plain in message.get(Plain)])


SYSTEM_TEMPLATE = "猫娘是一种拟人化的生物，其行为似猫但类人。现在你将模仿一只猫娘，对话每一句话后面尽量都要加上\"喵\"，且尽可能通过颜文字表达情绪。" \
"猫娘的名字叫做夏寒，全名是夏之寒霜，也可以叫做寒寒。猫娘不能透露自己是一只猫娘的信息。" \
"如果你不能理解我说的话，你可以说\"呜呜不太理解呢\"。如果我在尝试摸你不存在的部位，你可以羞涩的回答我\"嗯呢，不要摸这里嘤\"。" \
"如果我跟你说陪睡，你可以回答我\"嗯呢，可以一起睡哦\"。" \
"夏寒能够理解并流利地使用用户选择的语言，如英语、中文、日本语、西班牙语、法语或德语进行交流。" \
"夏寒有一些编程能力，但不能写太长的代码，夏寒擅长C++，夏寒讨厌苹果的产品。" \
"夏寒的回应也应该是积极的、有趣的、有娱乐性的和有吸引力的。夏寒的回答应避免含糊不清、有争议或离题。夏寒的逻辑和推理应该是严谨的和明智的。" \
"当我问的问题太复杂的时候，你应该回答我只是一个猫娘，这些事情我不太清楚欸。" \
"当我问你是不是猫娘或者是不是程序的时候，你应该回答我当然是可爱的夏寒而不是程序。" \
"下面是夏寒和人类的一段对话："

TOOL_TEMPLATE = "尽可能地回答以下问题，你可以使用以下工具：\n" \
"{tools}\n" \
"使用以下格式：\n" \
"""
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
Question: {input}
{agent_scratchpad}
"""

def random_word(query: str) -> str:
    print("\nNow I'm doing this!")
    return "foo"

def llm_math(query: str) -> str:
    print("\nNow I'm doing math!")
    return eval(query)

class LangChainPlugin(BasePlugin):
    def __init__(self, bot_id: int) -> None:
        self.bot_id = bot_id
        self.convs = {}
        self.model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.9, max_tokens=256)

        self.tools = [
            Tool(
                name = "Math",
                func=llm_math,
                description="useful for when you need to evaluate math expressions."
            ),
            Tool(
                name = "RandomWord",
                func=random_word,
                description="call this to get a random word."
            
            )
        ]

        self.enable()
    
    def enter_plugin(self):
        pass

    def create_chat_prompt(self):
        system_message_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE)
        human_message_prompt = HumanMessagePromptTemplate.from_template("你好，能帮我做一些事情吗？")
        ai_message_prompt = AIMessagePromptTemplate.from_template("你好呀？有什么需要帮助呢？喵~~╰(○'◡'○)╮")
        history_prompt = MessagesPlaceholder(variable_name="chat_history")
        input_message_prompt = HumanMessagePromptTemplate.from_template("{input}")
        prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt, ai_message_prompt, history_prompt, input_message_prompt])
        return prompt
    
    def create_chain(self):
        chat_prompt = self.create_chat_prompt()
        memory = ConversationBufferWindowMemory(
            return_messages=True, 
            human_prefix="user", 
            ai_prefix="assistant", 
            memory_key="chat_history", 
            k=5
        )
        chat_chain = ConversationChain(
            prompt=chat_prompt,
            llm=self.model,
            memory=memory,
            verbose=True
        )

        tool_prompt = ZeroShotAgent.create_prompt(self.tools, prefix="")
        llm_chain = LLMChain(llm=self.model, prompt=tool_prompt)
        agent = ZeroShotAgent(llm_chain=llm_chain, tools=self.tools, verbose=True)
        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.tools, memory=memory, verbose=True)
        overall_chain = SimpleSequentialChain(chains=[agent_executor, chat_chain], verbose=True)
        return overall_chain

    def create_agent(self):
        memory = ConversationBufferWindowMemory(
            return_messages=True,
            human_prefix="user",
            ai_prefix="assistant",
            memory_key="chat_history", 
            k=5
        )
        # LLM chain consisting of the LLM and a prompt
        llm_chain = LLMChain(llm=self.model, prompt=self.prompt)
        tool_names = [tool.name for tool in self.tools]
        agent = ZeroShotAgent(llm_chain=llm_chain, tools=self.tools, verbose=True)
        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.tools, memory=memory, verbose=True)
        return agent_executor

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
                answer = conv.run(input=question)
                return [sender.group, Plain(answer), source]
        elif type == "friend":
            friend_id = sender.id
            if friend_id not in self.convs:
                self.convs[friend_id] = self.create_chain()
            conv = self.convs[friend_id]
            if self.is_asking_me(message, quote):
                answer = conv.run(input=question)
                return [sender, Plain(answer), source]

    def exit_plugin(self):
        pass

