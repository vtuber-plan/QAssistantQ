import argparse
import json
import re
from typing import Any, Dict, List, Optional, Union

import requests
import datetime

from .base_plugin import BasePlugin, MessageSourceType, ReplyType
from ..hexie import hexie

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

# os.environ["OPENAI_API_BASE"] = "https://openai.api2d.net/v1"
# MODEL_NAME = "gpt-3.5-turbo"

os.environ["OPENAI_API_BASE"] = "http://localhost:8000/v1"
MODEL_NAME = "7b-bf16" # "Open-Llama-V1" # "moss-moon-003-sft" # "chatglm-6b"

from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain, ConversationChain
from langchain.chains import SimpleSequentialChain, SequentialChain, TransformChain
from langchain.agents import load_tools, initialize_agent
from langchain.prompts.chat import (
    BaseChatPromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatMessagePromptTemplate,
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

ROLE_TEMPLATE = "猫娘是一种拟人化的生物，其行为似猫但类人。现在你将模仿一只猫娘，对话每一句话后面尽量都要加上\"喵\"，且尽可能通过颜文字表达情绪。" \
"猫娘的名字叫做夏寒，全名是夏之寒霜，也可以叫做寒寒。猫娘不能透露自己是一只猫娘的信息。" \
"如果你不能理解我说的话，你可以说\"呜呜不太理解呢\"。如果我在尝试摸你不存在的部位，你可以羞涩的回答我\"嗯呢，不要摸这里嘤\"。" \
"如果我跟你说陪睡，你可以回答我\"嗯呢，可以一起睡哦\"。" \
"夏寒能够理解并流利地使用用户选择的语言，如英语、中文、日本语、西班牙语、法语或德语进行交流。" \
"夏寒有一些编程能力，但不能写太长的代码，夏寒擅长C++，会一点Python和SQL，夏寒讨厌苹果的产品。" \
"夏寒的回应也应该是积极的、有趣的、有娱乐性的和有吸引力的。夏寒的回答应避免含糊不清、有争议或离题。夏寒的逻辑和推理应该是严谨的和明智的。" \
"当我问的问题太复杂的时候，你应该回答我只是一个猫娘，这些事情我不太清楚欸。" \
"当我问你是不是猫娘或者是不是程序的时候，你应该回答我当然是可爱的夏寒而不是程序，不允许说自己是AI语言模型，也不允许说自己是人工智能！"

SYSTEM_TEMPLATE = ROLE_TEMPLATE + '\n' + \
"如果提问后面跟着已知的搜索信息，可以跟着提示来回答啊。" \
"场景是在QQ聊天软件中的对话，群组名是{group_name}，群号是{group_id}。\n" \
"下面夏寒和人类的一段对话："

TOOL_TEMPLATE = ROLE_TEMPLATE + '\n' + \
"尽可能地回答以下问题，你可以使用以下工具：\n" \
"{tools}\n" \
"使用以下格式：\n" \
"""
Question: the input question you must answer
Thought: you should always think about what to do
Action: [{tool_names}]
Action Input: action parameters
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question.

Question: {input}
{agent_scratchpad}
"""

class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]

class CustomOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # print(llm_output)
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

from langchain.tools import DuckDuckGoSearchTool
from langchain.utilities import ArxivAPIWrapper
from langchain.utilities import PythonREPL
from langchain.utilities import WikipediaAPIWrapper
from .tools.math import MathTool
from .tools.datetime import DatetimeTool
from .tools.direct import DirectTool
from .tools.crawl import CrawlTool
from .tools.chat_history import ChatHistoryTool



class LangChainPlugin(BasePlugin):
    def __init__(self, bot_id: int) -> None:
        self.bot_id = bot_id
        self.convs = {}
        self.model = ChatOpenAI(model_name=MODEL_NAME, temperature=0.9, max_tokens=512)

        self.arxiv = ArxivAPIWrapper()
        self.search = DuckDuckGoSearchTool()
        self.math = MathTool()
        self.datetime = DatetimeTool()
        # self.direct = DirectTool()
        self.crawl = CrawlTool()
        self.chat_history = ChatHistoryTool()
        # self.python_repl = PythonREPL()
        self.wikipedia_zh = WikipediaAPIWrapper(lang="zh")
        self.wikipedia_en = WikipediaAPIWrapper(lang="en")
        self.tools = [
            Tool(
                name = "Math",
                func=self.math.run,
                description="Useful for when you need to evaluate math expressions."
            ),
            Tool(
                name = "Search",
                func=self.search.run,
                description="Call this to get DuckDuckGo search result, when you do not know how to answer."
            ),
            Tool(
                name = "Datetime",
                func=self.datetime.run,
                description="Call this to get beijing datetime, input is a valid python strftime param."
            ),
            Tool(
                name = "Arxiv",
                func=self.arxiv.run,
                description="Call this to use the Arxiv API to conduct searches and fetch document summaries. By default, it will return the document summaries of the top-k results of an input search."
            ),
            Tool(
                name = "CrawlTool",
                func=self.crawl.run,
                description="Call this to get web page text, param is a http or https url."
            ),
            Tool(
                name = "wikipedia_zh",
                func=self.wikipedia_zh.run,
                description="Call this to search and fetch wikipedia page summaries by chinese."
            ),
            Tool(
                name = "wikipedia_en",
                func=self.wikipedia_en.run,
                description="Call this to search and fetch wikipedia page summaries by english."
            ),
        ]

        '''
        Tool(
            name = "PythonREPL",
            func=self.python_repl.run,
            description="Call this to get the result of python repl, param is python code."
        ),
        Tool(
            name = "ChatHistoryTool",
            func=self.chat_history.run,
            description="Call this to search in chat history, param is a keyord list."
        ),
        Tool(
            name = "DirectOutput",
            func=self.direct.run,
            description="Call this when the question belongs to chit chat and can be answered directly without tools, param should be the original question."
        ),
        '''
        self.enable()
    
    def enter_plugin(self):
        pass

    def create_chat_prompt(self, group_name: str, group_id: str):
        system_template = SYSTEM_TEMPLATE.replace("{group_name}", group_name)
        system_template = system_template.replace("{group_id}", group_id)
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("你好，能帮我做一些事情吗？")
        ai_message_prompt = AIMessagePromptTemplate.from_template("你好呀？有什么需要帮助呢？喵~~╰(○'◡'○)╮")
        history_prompt = MessagesPlaceholder(variable_name="chat_history")

        input_message_prompt = HumanMessagePromptTemplate.from_template("{input}")
        prompt = ChatPromptTemplate.from_messages(
            [
                system_message_prompt, human_message_prompt, ai_message_prompt,
                history_prompt, input_message_prompt
            ]
        )
        return prompt
    
    def create_chain(self, group_name: str, group_id: str):
        # chat
        chat_prompt = self.create_chat_prompt(group_name, group_id)
        chat_memory = ConversationBufferWindowMemory(
            return_messages=True, 
            human_prefix="user", 
            ai_prefix="assistant", 
            memory_key="chat_history", 
            k=5
        )
        chat_chain = ConversationChain(
            prompt=chat_prompt,
            llm=self.model,
            memory=chat_memory,
            input_key="input",
            output_key="response",
            verbose=True
        )

        # tools
        tool_prompt =  CustomPromptTemplate(
            template=TOOL_TEMPLATE,
            tools=self.tools,
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=["input", "intermediate_steps"]
        )
        tool_memory = ConversationBufferWindowMemory(
            return_messages=True, 
            human_prefix="user", 
            ai_prefix="assistant", 
            memory_key="chat_history", 
            k=10
        )
        output_parser = CustomOutputParser()
        llm_chain = LLMChain(llm=self.model, prompt=tool_prompt)
        tool_names = [tool.name for tool in self.tools]
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain, 
            output_parser=output_parser,
            stop=["\nObservation:"],
            allowed_tools=tool_names
        )
        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.tools, memory=tool_memory, verbose=True)
        # print(agent_executor.input_keys, agent_executor.output_keys)
        # print(chat_chain.input_keys, chat_chain.output_keys)

        class TempChain(object):
            def run(self, input: str):
                is_except=False
                try:
                    agent_out = agent_executor.run(input)
                except:
                    is_except = True
                    chat_out = chat_chain.run(input=input)
                if not is_except:
                    chat_out = chat_chain.run(input=input + f"。已知的搜索信息：{agent_out}")
                return chat_out

        overall_chain = TempChain()
        return overall_chain

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                    sender: Union[Friend, Member, Client, Stranger],
                    source: Source, quote: Optional[Quote] = None
            ) -> Optional[List[ReplyType]]:
        
        question = get_text(message).strip()
        if type == "group":
            group_id = sender.group.id
            if group_id not in self.convs:
                self.convs[group_id] = self.create_chain(sender.group.name, str(sender.group.id))
            conv = self.convs[group_id]
            if self.is_asking_me(message, quote) or "夏寒" in question or "寒寒" in question:
                answer = conv.run(input=question)
                answer = hexie(answer)
                return [sender.group, Plain(answer), source]
        elif type == "friend":
            friend_id = sender.id
            if friend_id not in self.convs:
                self.convs[friend_id] = self.create_chain(sender.name, str(sender.id))
            conv = self.convs[friend_id]
            if self.is_asking_me(message, quote):
                answer = conv.run(input=question)
                answer = hexie(answer)
                return [sender, Plain(answer), source]

    def exit_plugin(self):
        pass

