

import json
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, TypeVar, Union
from .base_plugin import BasePlugin, MessageSourceType, ReplyType

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Group, Client, Stranger
from graia.ariadne.message.element import Element, Quote, Source, AtAll, At, Plain
from graia.ariadne.event.message import MessageEvent, FriendMessage, GroupMessage

def get_text(message: MessageChain) -> str:
    return "".join([plain.text for plain in message.get(Plain)])

class PingPongPlugin(BasePlugin):
    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id=bot_id)
        self.enable()
    
    def enter_plugin(self):
        pass

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                    sender: Union[Friend, Member, Client, Stranger],
                    source: Source, quote: Optional[Quote] = None
            ) -> Optional[List[ReplyType]]:
        if type == "group":
            if self.is_asking_me(message, quote) and get_text(message).strip() == "ping":
                return [sender.group, Plain("pong"), source]
        elif type == "friend":
            if self.is_asking_me(message, quote) and get_text(message).strip() == "ping":
                return [sender, Plain("pong"), False]

    def exit_plugin(self):
        pass