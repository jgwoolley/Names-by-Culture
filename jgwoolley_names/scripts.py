#TODO: Nothing done with this yet
#This could actually determine the true
import os, requests, sqlmodel

from typing import Dict, List, Set

from .models import LanguageScriptRange

DEFAULT_URL = 'http://unicode.org/Public/UNIDATA/Scripts.txt'

def load_database(session:requests.Session, url:str= DEFAULT_URL, file_path:str = 'Scripts.txt') -> Dict[str, List[List[int]]]:
    if not os.path.isfile(file_path):
        response = session.get(url)
        with open(file_path, 'wb') as f:
            f.write(response.content)

    result = dict()

    with open(file_path, 'r') as file:
        for line in file:
            if len(line.strip()) == 0 or line.startswith('#'):
                continue
            hex_range, line = line.split(';', 1)
            hex_range = [int(x.strip(),16) for x in hex_range.split('..', 1)]
            if len(hex_range) == 1:
                hex_range.append(hex_range[0])

            script, line = line.split('#', 1)
            script = script.strip()

            try:
                ids = result[script]
            except:
                ids = result[script] = list()
            ids.append(hex_range)

    return result

#Maybe merge with languages.write_languages_to_sql ?
def write_scripts_to_sql(session:requests.Session, sql_session:sqlmodel.Session, url:str=DEFAULT_URL) -> None:
    for table in [LanguageScriptRange]:
        statement = sqlmodel.select(table)
        results = sql_session.exec(statement)
        result = results.first()
        if result is not None:
            return

    for name, maxmins in load_database(session=session).items():
        for maxmin in maxmins: 
            data = LanguageScriptRange(name=name, min=maxmin[0], max=maxmin[1])
            if data.min > data.max:
                raise Exception(f'data.min > data.max')
            sql_session.add(data)
            sql_session.commit()

#TODO: cachetools can set one argument that matters
#@functools.lru_cache(maxsize=100, typed=False)
def find_script(sql_session:sqlmodel.Session, unicode) -> Set[str]:
    statement = sqlmodel.select(LanguageScriptRange).where(unicode <= LanguageScriptRange.max).where(LanguageScriptRange.min <= unicode)
    results = sql_session.exec(statement)
    result = results.one_or_none()
    if result is None:
        raise Exception()
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