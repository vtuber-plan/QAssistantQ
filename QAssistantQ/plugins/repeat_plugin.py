
from collections import defaultdict
import json
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, TypeVar, Union
from .base_plugin import BasePlugin, MessageSourceType, ReplyType

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Group, Client, Stranger
from graia.ariadne.message.element import Element, Quote, Source, AtAll, At, Plain
from graia.ariadne.event.message import MessageEvent, FriendMessage, GroupMessage

class RepeatPlugin(BasePlugin):
    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id=bot_id)
        self.enable()
        self.history = defaultdict(list)
    
    def enter_plugin(self):
        pass

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                    sender: Union[Friend, Member, Client, Stranger],
                    source: Source, quote: Optional[Quote] = None
            ) -> Optional[List[ReplyType]]:
        if type != "group":
            return
        
        group_id = sender.group.id
        history = self.history[group_id]

        history.append(message)
        if len(history) > 5:
            history.pop(0)
        
        if len(history) >= 3 and history[-1] == history[-2] and history[-2] == history[-3]:
            return [sender.group, history[-1], False]

    def exit_plugin(self):
        pass