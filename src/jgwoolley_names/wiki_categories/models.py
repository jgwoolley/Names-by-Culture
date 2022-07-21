from pydantic import BaseModel, validator
import dataclasses
from typing import Callable, List, Optional, Dict

from ..model import WikiRecord

import sqlmodel, requests

@dataclasses.dataclass
class CategoryInfo:
    size:int
    pages:int
    files:int
    subcats:int

@dataclasses.dataclass
class ActionContext:
    sql_session:sqlmodel.Session
    session:requests.Session
    row:WikiRecord
    cmtitle_tokens:List[str]
    category_info:CategoryInfo
    suggested_language:Optional[str]
    suggested_gender:Optional[str]

@dataclasses.dataclass
class Action:
    name:str
    alt_names:List[str]
    description:str
    default_value_calculation: Callable[[ActionContext], int]
    action: Callable[[ActionContext], None]

    def calculate_default_value(self, context:ActionContext) -> int:
        return self.default_value_calculation(context)

    def action(self, context:ActionContext) -> None:
        return self.action(context)

    def equals_input(self, input_name:str) -> bool:
        if self.name == input_name:
            return True

        for name in self.alt_names:
            if name == input_name:
                return True
        
        return False