import requests, csv, sqlmodel

from typing import Iterator, List
from .model import Language

DEFAULT_URL = 'https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab'

def query_languages_from_web(session:requests.Session, url:str=DEFAULT_URL) -> str:
    R = session.get(url=url)
    data = R.text
    return data

def parse_languages_from_text(tsv:str) -> Iterator[List[str]]:
    reader = csv.reader(tsv.splitlines(), delimiter='\t')
    header = next(reader)
    for line in reader:
        yield line

def parse_languages_from_web(session:requests.Session, url:str=DEFAULT_URL) -> Iterator[List[str]]:
    result = query_languages_from_web(session=session)
    return parse_languages_from_text(result)

def write_languages_to_sql(session:requests.Session, sql_session:sqlmodel.Session, url:str=DEFAULT_URL):
    statement = sqlmodel.delete(Language)
    result = sql_session.exec(statement)
    sql_session.commit()

    for result in parse_languages_from_web(url=url, session=session):
        id, part2b, part2t, part1, scope, language_type, ref_name, comment = result
        data = Language(
            id = id,
            part2b = part2b,
            part2t = part2t,
            part1 = part1,
            scope = scope,
            language_type = language_type,
            ref_name = ref_name,
            comment = comment
        )
        sql_session.add(data)
    sql_session.commit()

def find_language_id(sql_session:sqlmodel.Session, language:str) -> str:
    statement = sqlmodel.select(Language).where(Language.ref_name == language)
    results = sql_session.exec(statement)
    result = results.first()

    if result == None:
        return None

    return result.id

def find_language_ref_name(sql_session:sqlmodel.Session, language_id:str) -> str:
    statement = sqlmodel.select(Language).where(Language.id == language_id)
    results = sql_session.exec(statement)
    result = results.first()

    if result == None:
        return None
    
    return result.ref_name