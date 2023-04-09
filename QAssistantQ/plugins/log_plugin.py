

import json
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from .base_plugin import BasePlugin, MessageSourceType, ReplyType

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Group, Client, Stranger
from graia.ariadne.message import Quote
from graia.ariadne.app import Source
from graia.ariadne.event.message import MessageEvent, FriendMessage, GroupMessage


class LogPlugin(BasePlugin):
    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id=bot_id)
        self.enable()
    
    def enter_plugin(self):
        pass

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                    sender: Union[Friend, Member, Client, Stranger],
                    source: Source, quote: Optional[Quote] = None
            ) -> Optional[List[ReplyType]]:
        log_object = {
            "type": type, 
            "message": message.as_persistent_string(),
            "sender": sender.id,
            "group": sender.group.id if isinstance(sender, Member) else None,
            "source": {"id": source.id, "time": source.time.strftime("%Y-%m-%d %H:%M:%S")},
            "quote": quote.as_persistent_string() if quote is not None else None,
        }
        with open("qaq.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_object, ensure_ascii=False) + '\n')

    def exit_plugin(self):
        pass