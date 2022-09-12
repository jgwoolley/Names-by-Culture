import requests, csv, sqlmodel
from typing import Optional, Iterable, Type, TextIO, Callable

from .models import LanguageName, Language, LanguageScriptRange, ConfigurableModel
import csv

DEFAULT_URL = 'https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab'

def _get_optional(data:dict, key) -> Optional[str]:
    value = data[key]
    if len(value) == 0:
        return None
    return value

def parse_payload(sql_session:sqlmodel.Session, file:TextIO):
    reader = csv.DictReader(file, delimiter='\t')    
    for row in reader:
        id = row['Id']
        statement = sqlmodel.select(Language).where(Language.id == id)
        results = sql_session.exec(statement)
        result = results.first()
        if result is None:
            result = Language(
                id = id,
                part2b = _get_optional(row, 'Part2B'),
                part2t = _get_optional(row, 'Part2T'),
                part1 = _get_optional(row, 'Part1'),
                scope = _get_optional(row, 'Scope'),
                language_type = _get_optional(row, 'Language_Type'),
                ref_name = _get_optional(row, 'Ref_Name'),
                comment = _get_optional(row, 'Comment')
            )            
            sql_session.add(result)

        for ref_dat in result.create_references():
            statement = sqlmodel.select(LanguageName).where(LanguageName.name == ref_dat.name)
            results = sql_session.exec(statement)
            result = results.first()
            if result is not None:
                continue
            
            sql_session.add(ref_dat)
    sql_session.commit()

def load(session:requests.Session, sql_session:sqlmodel.Session, url:str=DEFAULT_URL, file_path:Optional[str]=None):    
    config = ConfigurableModel(
        url=url, 
        file_path=file_path, 
        model=Language,
        parse_payload=parse_payload
    )
    config.load(session, sql_session)

def find_language_id(sql_session:sqlmodel.Session, name:str) -> str:
    statement = sqlmodel.select(LanguageName).where(LanguageName.name == name)
    results = sql_session.exec(statement)
    result = results.first()
    return result.language_id if result else None