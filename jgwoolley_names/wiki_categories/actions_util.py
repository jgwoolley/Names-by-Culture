import logging, requests, sqlmodel

from typing import Dict, List, Optional, Tuple
from jgwoolley_wikimedia import query_subcategory, query_category_pages, query_wikitext, query_category_info

from ..languages import write_languages_to_sql, find_language_id
from ..models import WikiRecord, Language, WikiRecordStatus, Gender, LanguageName
from .models import CategoryInfo, Action, ActionContext

genders = [x.value for x in Gender]

def get_cmtitle_tokens(row:WikiRecord) -> List[str]:
    return row.title.split(':')[-1].split()

def find_suggested_language(sql_session:sqlmodel.Session, cmtitle_tokens:List[str]) -> str:
    suggested_values = []
    for value in cmtitle_tokens:
        value = find_language_id(sql_session, value)
        if not value is None:
            suggested_values.append(value)

    if len(suggested_values) <= 0:
        return None

    return suggested_values[-1]

def find_suggested_gender(sql_session:sqlmodel.Session, cmtitle_tokens:List[str]) -> str:
    suggested_values = []
    for value in cmtitle_tokens:
        if value in genders:
            suggested_values.append(value)
    if len(suggested_values) == 0:
        return 'unisex'

    return suggested_values[-1]

def choose_language(sql_session:sqlmodel.Session, cmtitle:str, suggested_value:Optional[str], guide_type:str='language') -> str:
    input_guide = f'Please select a {guide_type} for \"{cmtitle}\" \"{suggested_value}\" or type \"exit\"\n'

    print(f'{cmtitle}: {suggested_value}')
    language_id=None
    while language_id is None:
        value = input(input_guide).lower()
        if value == 'exit':
            return None

        if len(value) == 0 and suggested_value is None:
            continue

        if len(value) == 0 and suggested_value is not None:
            value = suggested_value
        
        language_id = find_language_id(sql_session=sql_session, name=value)

    return language_id

def choose_script_language(context:ActionContext):
    return choose_language(sql_session=context.sql_session, cmtitle=context.row.title, suggested_value=context.suggested_script)

def choose_gender(sql_session:sqlmodel.Session, cmtitle:str, suggested_value:Optional[str]) -> str:
    input_guide = f'Please select a gender for \"{cmtitle}\" \"{suggested_value}\" or type \"exit\"\n'

    print(f'{cmtitle}: {suggested_value}')
    value=None
    while value is None:
        value = input(input_guide).lower()
        if value == 'exit':
            return None

        if len(value) == 0 and suggested_value is None:
            continue

        if len(value) == 0 and suggested_value is not None:
            value = suggested_value
        
    return value
