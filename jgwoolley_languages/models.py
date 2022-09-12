from sqlmodel.sql.expression import Select, SelectOfScalar

SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore

del Select, SelectOfScalar

from sqlmodel import SQLModel, Session, Field, Column, Enum
from typing import Optional, Iterable, Type, TextIO, Callable
from pydantic import BaseModel, FilePath, HttpUrl, root_validator
from pathlib import Path
from logging import getLogger

import enum, sqlmodel, requests

from .utils import find_file_in_url

class LanguageName(SQLModel, table=True):
    name : str = Field(primary_key=True)
    language_id: str
    source: str

class Language(SQLModel, table=True):
    id : str = Field(primary_key=True)
    part2b : Optional[str]
    part2t : Optional[str]
    part1 : Optional[str]
    scope : Optional[str]
    language_type : Optional[str]
    ref_name : Optional[str]
    comment : Optional[str]

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

class ConfigurableModel(BaseModel):
    url:HttpUrl
    file_path:Optional[Path]
    model:Type[SQLModel]
    parse_payload:Callable[sqlmodel.Session, TextIO]

    @root_validator(pre=True)
    def file_path_empty(cls, values:dict):
        file_path = values.get('file_path')
        if file_path:
            return values
        url = values.get('url')
        if url:
            values['file_path'] = find_file_in_url(str(url))
        return values

    def query_file(self, session:requests.Session):
        getLogger('jgwoolley_languages.configurable.query_file').info(self.url)
        response = session.get(self.url)
        with self.file_path.open('wb') as f:
            f.write(response.content)

    def load_file(self, sql_session:sqlmodel.Session):
        with self.file_path.open('r') as file:
            self.parse_payload(sql_session, file)

    def load(self, session:requests.Session, sql_session:sqlmodel.Session):
        statement = sqlmodel.select(self.model)
        results = sql_session.exec(statement)
        result = results.first()
        if result is not None:
            getLogger('jgwoolley_languages.configurable.sql_loaded').info(self.model.__name__)
            return
        if not self.file_path.is_file():
            self.query_file(session)
        getLogger('jgwoolley_languages.configurable.parsing_file').info(self.url)
        self.load_file(sql_session)