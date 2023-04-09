

import json
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypeVar
from .base_plugin import BasePlugin, MessageSourceType

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Group
from graia.ariadne.message.element import Element, Quote, Source, AtAll, At

Element_T = TypeVar("Element_T", bound=Element)

def get_first_or_none(message: MessageChain, element_class: Element_T) -> Optional[Element_T]:
    lst = message.get(element_class)
    if len(lst) == 0:
        return None
    else:
        return lst[0]

class PingPongPlugin(BasePlugin):
    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id=bot_id)
        self.enable()
    
    def enter_plugin(self):
        pass

    def is_asking_me(self, message: MessageChain) -> bool:
        quote = get_first_or_none(message, Quote)
        at = get_first_or_none(message, At)

        if quote is not None and quote.sender_id == self.bot_id:
            return True
        
        if at is not None and at.target == self.bot_id:
            return True
        
        return False

    def do_plugin(self, type: MessageSourceType, message: MessageChain,
                member: Optional[Member]=None,
                group: Optional[Group]=None,
                friend: Optional[Friend]=None
            ) -> Optional[List[Any]]:
        if type == "group":
            if self.is_asking_me(message):
                print("hi")
        elif type == "group":
            if self.is_asking_me(message):
                print("hi")



    def exit_plugin(self):
        pass