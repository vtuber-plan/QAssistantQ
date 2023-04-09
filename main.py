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
from QAssistantQ.plugins.log_plugin import LogPlugin
from QAssistantQ.plugins.pingpong_plugin import PingPongPlugin

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
]


@app.broadcast.receiver("GroupMessage")
async def message_listener(app: Ariadne, message: MessageChain, 
                           sender: Union[Friend, Member, Client, Stranger],
                           source: Source, quote: Optional[Quote] = None):
    # await app.send_message(group, "Hello, World!")
    reply_messages = []

    for plugin in plugins:
        if not plugin.is_activated:
            continue
        plugin.enter_plugin()
    
    for plugin in plugins:
        if not plugin.is_activated:
            continue
        if isinstance(sender, Friend):
            t = "friend"
        elif isinstance(sender, Group):
            t = "group"
        elif isinstance(sender, Client):
            t = "client"
        elif isinstance(sender, Stranger):
            t = "stranger"
        else:
            t = None
        plugin_ret = plugin.do_plugin(t, message, sender, source, quote)
        if plugin_ret is not None:
            reply_messages.append(plugin_ret)
    
    for plugin in plugins:
        if not plugin.is_activated:
            continue
        plugin.exit_plugin()

Ariadne.launch_blocking()