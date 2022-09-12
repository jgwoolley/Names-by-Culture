import requests, csv, sqlmodel
from typing import Optional, Iterable, Type, TextIO, Callable, Set, List

from .models import LanguageName, Language, LanguageScriptRange, ConfigurableModel

DEFAULT_URL = 'http://unicode.org/Public/UNIDATA/Scripts.txt'

def parse_payload(sql_session:sqlmodel.Session, file:TextIO):
    for line in file:
        if len(line.strip()) == 0 or line.startswith('#'):
            continue
        maxmin, line = line.split(';', 1)
        maxmin = [int(x.strip(),16) for x in maxmin.split('..', 1)]
        if len(maxmin) == 1:
            maxmin.append(maxmin[0])

        script, line = line.split('#', 1)
        script = script.strip()

        result_min, result_max = maxmin
        if result_min > result_max:
            raise Exception(f'result.min > result.max')

        statement = sqlmodel.select(LanguageScriptRange).where(LanguageScriptRange.min == result_min)
        results = sql_session.exec(statement)
        result = results.first()
        if not result is None:
            continue

        result = LanguageScriptRange(name=script, min=result_min, max=result_max)
        sql_session.add(result)
        sql_session.commit()

def load(session:requests.Session, sql_session:sqlmodel.Session, url:str=DEFAULT_URL, file_path:Optional[str]=None):    
    config = ConfigurableModel(
        url=url, 
        file_path=file_path, 
        model=LanguageScriptRange,
        parse_payload=parse_payload
    )
    config.load(session, sql_session)

#TODO: cachetools can set one argument that matters
#@functools.lru_cache(maxsize=100, typed=False)
def find_script(sql_session:sqlmodel.Session, unicode) -> Set[str]:
    statement = sqlmodel.select(LanguageScriptRange).where(unicode <= LanguageScriptRange.max).where(LanguageScriptRange.min <= unicode)
    results = sql_session.exec(statement)
    result = results.one_or_none()
    if result is None:
        raise Exception(f'Could not find script for unicode value: {unicode}')
        return None

    return result.name

def find_suggested_script(sql_session:sqlmodel.Session, names:List[str]) -> Set[str]:
    if isinstance(names, str):
        names = [names]

    scripts = set()
    for name in names:
        for x in name:
            id = ord(x)
            script = find_script(sql_session, id)
            if script is None:
                continue
            scripts.add(script)

    if 'Common' in scripts:
        scripts.remove('Common')
    if len(scripts) == 0:
        return None
    if len(scripts) > 1 and 'Latin' in scripts:
        scripts.remove('Latin')

    #TODO: I've seen {'Han', 'Hiragana'}
    #TODO: {'Inherited', 'Malayalam'}
    #TODO: {'Inherited', 'Common', 'Greek', 'Latin'}
    for script in scripts:
        return script

    return None