

from typing import Any, Dict, List, Literal, Optional, Tuple, TypeVar, Union

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Group, Client, Stranger
from graia.ariadne.message import Quote
from graia.ariadne.app import Source
from graia.ariadne.message.element import Element, Quote, Source, AtAll, At
from graia.ariadne.event.message import MessageEvent, FriendMessage, GroupMessage

MessageSourceType = Literal["group", "friend", "client", "stranger"]


Element_T = TypeVar("Element_T", bound=Element)

def get_first_or_none(message: MessageChain, element_class: Element_T) -> Optional[Element_T]:
    lst = message.get(element_class)
    if len(lst) == 0:
        return None
    else:
        return lst[0]



ReplyType = Tuple[
    Union[MessageEvent, Group, Friend, Member],
    MessageChain,
    Union[bool, int, Source, MessageChain]
]
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
            ) -> Optional[List[ReplyType]]:
        pass

    def exit_plugin(self):
        pass

    def is_asking_me(self, message: MessageChain, quote: Optional[Quote]=None) -> bool:
        at = get_first_or_none(message, At)
        if quote is not None and quote.sender_id == self.bot_id:
            return True
        
        if at is not None and at.target == self.bot_id:
            return True
        return False
    
    def is_at_me(self, message: MessageChain, quote: Optional[Quote]=None) -> bool:
        at = get_first_or_none(message, At)
        if at is not None and at.target == self.bot_id:
            return True
        return False

    def is_replying_me(self, message: MessageChain, quote: Optional[Quote]=None) -> bool:
        if quote is not None and quote.sender_id == self.bot_id:
            return True
        return False
