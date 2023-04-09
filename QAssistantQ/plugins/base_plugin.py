

from typing import Any, Dict, List, Literal, Optional, Union

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Group, Client, Stranger
from graia.ariadne.message import Quote
from graia.ariadne.app import Source

MessageSourceType = Literal["group", "friend", "temp"]

class BasePlugin(object):
    def __init__(self, bot_id: int) -> None:
        self.bot_id = bot_id
        self.is_activated = False

    def enable(self):
        self.is_activated = True
    
    def disable(self):
        self.is_activated = False
    
    def enter_plugin(self):
        pass

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                    sender: Union[Friend, Member, Client, Stranger],
                    source: Source, quote: Optional[Quote] = None
            ) -> Optional[List[Any]]:
        pass

    def exit_plugin(self):
        pass

