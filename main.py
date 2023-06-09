from typing import List, Optional, Union
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import config, HttpClientConfig
from graia.ariadne.model import Friend, Member, Group, Client, Stranger
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message import Quote
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.app import Source
import json

from QAssistantQ.plugins.base_plugin import BasePlugin
from QAssistantQ.plugins.chat_plugin import ChatPlugin
from QAssistantQ.plugins.chatgpt_plugin import ChatGPTPlugin
from QAssistantQ.plugins.langchain_plugin import LangChainPlugin
from QAssistantQ.plugins.log_plugin import LogPlugin
from QAssistantQ.plugins.pingpong_plugin import PingPongPlugin
from QAssistantQ.plugins.repeat_plugin import RepeatPlugin

with open("config.json", "r", encoding="utf-8") as f:
    bot_config = json.loads(f.read())

app = Ariadne(
    config(
        bot_config["account"], bot_config["verify_key"], HttpClientConfig(host=bot_config["host"])
    )
)

BOT_QQ_ID = bot_config["account"]


plugins: List[BasePlugin] = [
    LogPlugin(BOT_QQ_ID),
    PingPongPlugin(BOT_QQ_ID),
    ChatGPTPlugin(BOT_QQ_ID),
    RepeatPlugin(BOT_QQ_ID),
]

async def message_listener(app: Ariadne, chat_type:str, message: MessageChain, 
                           sender: Union[Friend, Member, Client, Stranger],
                           source: Source, quote: Optional[Quote] = None):
    reply_messages = []

    for plugin in plugins:
        if not plugin.is_activated:
            continue
        plugin.enter_plugin()
    
    for plugin in plugins:
        if not plugin.is_activated:
            continue
        plugin_ret = plugin.do_plugin(chat_type, message, sender, source, quote)
        if plugin_ret is not None:
            reply_messages.append(plugin_ret)
    
    for plugin in plugins:
        if not plugin.is_activated:
            continue
        plugin.exit_plugin()
    
    for target, reply, quote_reply in reply_messages:
        await app.send_message(target, reply, quote=quote_reply)

@app.broadcast.receiver("GroupMessage")
async def group_message_listener(app: Ariadne, message: MessageChain, 
                           sender: Union[Friend, Member, Client, Stranger],
                           source: Source, quote: Optional[Quote] = None):
    await message_listener(app, "group", message, sender, source, quote)

@app.broadcast.receiver("FriendMessage")
async def friend_message_listener(app: Ariadne, message: MessageChain, 
                           sender: Union[Friend, Member, Client, Stranger],
                           source: Source, quote: Optional[Quote] = None):
    await message_listener(app, "friend", message, sender, source, quote)

@app.broadcast.receiver("TempMessage")
async def temp_message_listener(app: Ariadne, message: MessageChain, 
                           sender: Union[Friend, Member, Client, Stranger],
                           source: Source, quote: Optional[Quote] = None):
    await message_listener(app, "temp", message, sender, source, quote)

@app.broadcast.receiver("StrangerMessage")
async def stranger_message_listener(app: Ariadne, message: MessageChain, 
                           sender: Union[Friend, Member, Client, Stranger],
                           source: Source, quote: Optional[Quote] = None):
    await message_listener(app, "stranger", message, sender, source, quote)


Ariadne.launch_blocking()