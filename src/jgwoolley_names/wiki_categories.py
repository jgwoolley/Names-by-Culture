import logging, requests, sqlmodel

from typing import Dict, List, Optional, Tuple
from jgwoolley_wikimedia import query_subcategory, query_category_pages, query_wikitext

from .languages import write_languages_to_sql, find_language_ref_name, find_language_id
from .model import WikiRecord, Language, WikiRecordStatus, Gender

genders = [x.value for x in Gender]

def split_subcategory(url:str, sql_session:sqlmodel.Session, session:requests.Session, row: WikiRecord):
    row.status = WikiRecordStatus.category
    sql_session.add(row)
    sql_session.commit()

    for child_cmtitle in query_subcategory(url, row.cmtitle, session):
        child = WikiRecord(
            cmtitle = child_cmtitle,
            url = url,
            category_type = row.category_type,
            parent_cmtitle = row.cmtitle
        )
        sql_session.add(child)

    sql_session.commit()

def get_cmtitle_tokens(row:WikiRecord) -> List[str]:
    return row.cmtitle.split(':')[-1].split()

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

def choose_language(sql_session:sqlmodel.Session, cmtitle:str, suggested_value:Optional[str]) -> str:
    input_guide = f'Please select a language for {cmtitle} {suggested_value} or type \"exit\"\n'

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
        
        if find_language_ref_name(sql_session, value) is not None:
            language_id = value
            break

        language_id = find_language_id(sql_session=sql_session, language=value)

    return language_id

def choose_gender(sql_session:sqlmodel.Session, cmtitle:str, suggested_value:Optional[str]) -> str:
    input_guide = f'Please select a gender for {cmtitle} {suggested_value} or type \"exit\"\n'

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

def update_subcategory(url:str, sql_session:sqlmodel.Session, row:WikiRecord, suggested_language:Optional[str], suggested_gender:Optional[str]):
    language_id = choose_language(sql_session=sql_session, cmtitle=row.cmtitle, suggested_value=suggested_language)
    if language_id is None:
        return
    gender = choose_gender(sql_session=sql_session, cmtitle=row.cmtitle, suggested_value=suggested_gender)
    gender = Gender[gender]
    if gender is None:
        return
    row.gender = gender
    row.language_id = language_id
    row.category_type = WikiRecordStatus.page

    sql_session.commit() 

def guess_subcategory(url:str, sql_session:sqlmodel.Session, row:WikiRecord, suggested_language:Optional[str], suggested_gender:Optional[str]):
    if suggested_language is None:
        print(f'Unable to guess language for {row}')
        return

    if suggested_gender is None:
        print(f'Unable to guess gender for {row}')
        return

    row.language_id = suggested_language
    row.gender = suggested_gender
    row.category_type = WikiRecordStatus.page

    sql_session.commit() 

def create_actions(actions:List[str]) -> Tuple[Dict[str,str], str, str]:
    if len(actions) < 1:
        raise ValueError('actions list must have at least one action')
    action_default = actions[0]
    actions_dict = dict()

    for action in actions:
        action = action.lower()
        letter = action[0].lower()
        actions_dict[action] = letter
        actions_dict[letter] = letter

    actions_formatted = [f'[{x[0:1]}]{x[1:]}' for x in actions[1:]]
    actions_formatted.insert(0, f'[{action_default[0:1]}]{action_default[1:]} (default)')

    actions_guide = f'Please provide one of the following: {", ".join(actions_formatted)}\n'

    return (actions_dict, actions_guide, action_default[0][0].lower())

def process_parent(sql_session:sqlmodel.Session, session:requests.Session, parent:WikiRecord) -> Tuple[str, str, str]:
    if not isinstance(parent, WikiRecord):
        raise Exception(f'Given category isn\'t WikiRecord: {type(parent)}')

    category_type = parent.category_type
    parent_cmtitle = parent.cmtitle
    url = parent.url

    for k, v in {'url': url, 'category_type':category_type, 'cmtitle': parent_cmtitle}.items():
        if v is None:
            raise TypeError(f'{k} must not be none for record: {parent}')

    statement = sqlmodel.select(WikiRecord).where(WikiRecord.cmtitle == parent_cmtitle)
    results = sql_session.exec(statement)
    if not results.first():
        row = WikiRecord(
            cmtitle = parent_cmtitle,
            url = url,
            category_type = category_type
        )
        sql_session.add(row)
        sql_session.commit()
        split_subcategory(url=url, sql_session=sql_session, session=session, row=row)

    return (category_type, parent_cmtitle, url)


def create_wikicategories(sql_session:sqlmodel.Session, session:requests.Session, categories=List[WikiRecord]):
    write_languages_to_sql(sql_session=sql_session, session=session)

    actions, actions_guide, action_default = create_actions(['guess', 'update', 'split', 'ignore'])

    for parent in categories:
        category_type, parent_cmtitle, url = process_parent(sql_session=sql_session, session=session, parent=parent)

        while True:
            statement = sqlmodel.select(WikiRecord).where(WikiRecord.status == WikiRecordStatus.unevaluated).where(WikiRecord.category_type == category_type)
            results = sql_session.exec(statement)

            row:WikiRecord = results.first()
            if row is None:
                break

            cmtitle_tokens = get_cmtitle_tokens(row)
            suggested_gender = find_suggested_gender(sql_session=sql_session, cmtitle_tokens=cmtitle_tokens)
            suggested_language = find_suggested_language(sql_session=sql_session, cmtitle_tokens=cmtitle_tokens)

            print(f'{row.cmtitle} [category_type=\"{row.category_type}\", suggested_language=\"{suggested_language}\", suggested_gender=\"{suggested_gender}\", url=\"{url}\"]')

            action = None
            while not action in actions:
                text = input(actions_guide).lower()
                action = actions.get(text[0], action_default) if len(text) > 0 else 'g'
            
            if action == 'g':
                guess_subcategory(url=url, sql_session=sql_session, row=row, suggested_language=suggested_language, suggested_gender=suggested_gender)
            elif action == 'u':
                update_subcategory(url=url, sql_session=sql_session, row=row, suggested_language=suggested_language, suggested_gender=suggested_gender)                
            elif action == 's':
                split_subcategory(url=url, sql_session=sql_session, session=session, row=row)
            elif action == 'i':
                row.status = WikiRecordStatus.skipped
                sql_session.commit()
            else:
                raise Exception(f'There is no action {action} in {list(actions.keys())}')