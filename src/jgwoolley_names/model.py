from sqlmodel.sql.expression import Select, SelectOfScalar

SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore

del Select, SelectOfScalar

import enum

from sqlmodel import SQLModel, Field, Column, Enum
from typing import Optional

class Language(SQLModel, table=True):
    id : str = Field(primary_key=True)
    part2b : Optional[str]
    part2t : Optional[str]
    part1 : Optional[str]
    scope : Optional[str]
    language_type : Optional[str]
    ref_name : Optional[str]
    comment : Optional[str]

class LanguageName(SQLModel, table=True):
    name : str = Field(primary_key=True)
    language_id: str

class WikiRecordStatus(enum.Enum):
    unevaluated = "unevaluated"
    skipped = "skipped"
    page = "page"
    category = "category"

class Gender(enum.Enum):
    unisex = "unisex"
    male = "male"
    female = "female"

class WikiRecord(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    cmtitle: str
    url:str
    category_type: str
    status: WikiRecordStatus = Field(sa_column=Column(Enum(WikiRecordStatus), default=WikiRecordStatus.unevaluated))
    language_id : Optional[str] = None
    gender: Gender = Field(sa_column=Column(Enum(Gender), default=Gender.unisex))
    parent_cmtitle: Optional[str] = None