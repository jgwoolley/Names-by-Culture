#TODO: change to models.py

from sqlmodel.sql.expression import Select, SelectOfScalar

SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore

del Select, SelectOfScalar

import enum

from sqlmodel import SQLModel, Field, Column, Enum
from typing import Optional, Iterable

from pydantic import validator

class LanguageName(SQLModel, table=True):
    name : str = Field(primary_key=True)
    language_id: str
    source: str

    # @validator('name', 'language_id', always=True)
    # def to_lowercase(cls, v:str):
    #     if not isinstance(v, str):
    #         return None
    #     assert v.isalpha() == True, 'Test'
    #     return v.lower()

class Language(SQLModel, table=True): 
    id : str = Field(primary_key=True)
    part2b : Optional[str]
    part2t : Optional[str]
    part1 : Optional[str]
    scope : Optional[str]
    language_type : Optional[str]
    ref_name : Optional[str]
    comment : Optional[str]

    # @validator('id', 'part2b', 'part2t', 'part1', 'scope', 'language_type', 'ref_name', always=True)
    # def to_lowercase(cls, v:str):
    #     if not isinstance(v, str):
    #         return None
    #     assert v.isalpha() == True, 'Test'
    #     return v.lower()

    def create_references(self):
        return [
            LanguageName(
                name=self.ref_name,
                language_id=self.id,
                source='language_object'
            ),
            LanguageName(
                name=self.id,
                language_id=self.id,
                source='language_object'
            )
        ]

class LanguageScriptRange(SQLModel, table=True): 
    min : int = Field(primary_key=True)
    max: int
    name: str

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