from sqlmodel.sql.expression import Select, SelectOfScalar

SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore

del Select, SelectOfScalar

import enum

from sqlmodel import SQLModel, Field, Column, Enum
from typing import Optional, Iterable

from pydantic import validator

from jgwoolley_languages import LanguageName, Language, LanguageScriptRange

class WikiRecordStatus(enum.Enum):
    unevaluated = "unevaluated"
    skipped = "skipped"
    page = "page"
    category = "category"
    split_category = "split_category"
    redo = "redo"

class Gender(enum.Enum):
    unisex = "unisex"
    male = "male"
    female = "female"

class WikiRecord(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    title: str
    name: Optional[str] #TODO: This should be a normalized name, rather than the real title of article
    url:str
    category_type: str
    status: WikiRecordStatus = Field(sa_column=Column(Enum(WikiRecordStatus), default=WikiRecordStatus.unevaluated))
    status_backup: WikiRecordStatus = Field(sa_column=Column(Enum(WikiRecordStatus), default=WikiRecordStatus.unevaluated))
    language_id : Optional[str] = None
    language_script: Optional[str] = None
    gender: Gender = Field(sa_column=Column(Enum(Gender), default=Gender.unisex))
    parent_cmtitle: Optional[str] = None