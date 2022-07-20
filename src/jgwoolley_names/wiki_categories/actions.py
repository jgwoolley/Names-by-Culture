import logging, requests, sqlmodel

from typing import Dict, List, Optional, Tuple, Callable
from jgwoolley_wikimedia import (
    query_subcategory, 
    query_category_pages, 
    query_wikitext, 
    query_category_info
)

from ..languages import write_languages_to_sql, find_language_id
from ..model import (
    WikiRecord, 
    Language, 
    WikiRecordStatus, 
    Gender, 
    LanguageName
)
from .models import (
    CategoryInfo, 
    Action, 
    ActionContext
)
from .actions_util import (
    get_cmtitle_tokens, 
    find_suggested_language, 
    find_suggested_gender, 
    choose_language, 
    choose_gender
)

def ignore_row(context:ActionContext):
    row = context.row
    sql_session = context.sql_session

    row.status = WikiRecordStatus.skipped
    sql_session.commit()

def ignore_row_default_value(context:ActionContext):
    if context.category_info.size <= 10:
        return 4
    return 0

def split_subcategory(context:ActionContext):
    sql_session:sqlmodel.Session = context.sql_session
    session:requests.Session = context.session
    row: WikiRecord = context.row

    row.status = WikiRecordStatus.category
    sql_session.add(row)
    sql_session.commit()

    for child_cmtitle in query_subcategory(row.url, row.cmtitle, session):
        child = WikiRecord(
            cmtitle = child_cmtitle,
            url = row.url,
            category_type = row.category_type,
            parent_cmtitle = row.cmtitle
        )
        sql_session.add(child)

    sql_session.commit()

def split_subcategory_default_value(context:ActionContext):
    if context.category_info.pages < context.category_info.subcats:
        return 4

    if context.category_info.size > 1000 and isinstance(context.suggested_language, str) and context.suggested_language == 'eng':
        return 4
    return 0

def double_split_subcategory(context:ActionContext):
    sql_session:sqlmodel.Session = context.sql_session
    session:requests.Session = context.session
    row: WikiRecord = context.row

    row.status = WikiRecordStatus.category
    sql_session.add(row)
    sql_session.commit()

    for parent_cmtitle in query_subcategory(row.url, row.cmtitle, session):
        parent = WikiRecord(
            cmtitle = parent_cmtitle,
            url = row.url,
            category_type = row.category_type,
            status = WikiRecordStatus.category,
            parent_cmtitle = row.cmtitle
        )
        sql_session.add(parent)

        for child_cmtitle in query_subcategory(row.url, parent_cmtitle, session):
            child = WikiRecord(
                cmtitle = child_cmtitle,
                url = row.url,
                category_type = row.category_type,
                parent_cmtitle = parent_cmtitle
            )
            sql_session.add(child)

    sql_session.commit()

def double_split_subcategory_default_value(context:ActionContext):
    return 0

def update_subcategory(context:ActionContext):
    sql_session:sqlmodel.Session = context.sql_session
    row:WikiRecord = context.row
    suggested_language:Optional[str] = context.suggested_language
    suggested_gender:Optional[str] = context.suggested_gender

    language_id = choose_language(sql_session=sql_session, cmtitle=row.cmtitle, suggested_value=suggested_language)
    if language_id is None:
        return
    gender = choose_gender(sql_session=sql_session, cmtitle=row.cmtitle, suggested_value=suggested_gender)
    gender = Gender[gender]
    if gender is None:
        return
    row.language_id = language_id
    row.gender = gender
    row.status = WikiRecordStatus.page

    sql_session.commit() 

def update_subcategory_default_value(context:ActionContext):
    return 0

def guess_subcategory(context:ActionContext):
    sql_session:sqlmodel.Session = context.sql_session
    row:WikiRecord = context.row
    suggested_language:str = context.suggested_language
    suggested_gender:str = context.suggested_gender

    if not isinstance(suggested_language, str):
        print(f'Unable to guess language for {row}')
        return

    if not isinstance(suggested_gender, str):
        print(f'Unable to guess gender for {row}')
        return

    row.language_id = suggested_language
    row.gender = suggested_gender
    row.status = WikiRecordStatus.page

    sql_session.commit() 

def guess_subcategory_default_value(context:ActionContext):
    if isinstance(context.suggested_language, str) and isinstance(context.suggested_gender, str):
        return 2
    return 0

def add_language(context:ActionContext):
    sql_session:sqlmodel.Session = context.sql_session

    input_guide = f'Please type alternative language name or type \"exit\"\n'
    name=None
    while name is None:
        value = input(input_guide)
        if value == 'exit':
            return

        if len(value) == 0:
            continue

        name = value

    input_guide = f'Please type alternative language id for {name} or type \"exit\"\n'

    language_id=None
    while language_id is None:
        value = input(input_guide)
        if value == 'exit':
            return

        if len(value) == 0:
            continue
        
        language_id = value
        statement = sqlmodel.select(Language).where(Language.id == language_id)
        results = sql_session.exec(statement)
        result = results.first()

        if result == None:
            language_id=None
            continue

    print(f'Adding language reference {name} for {language_id}')
    ref_data = LanguageName(
        name = name, 
        language_id = language_id,
        source='user'
    )
    sql_session.add(ref_data)
    sql_session.commit()

def add_language_default_value(context:ActionContext):
    if isinstance(context.suggested_language, str) and len(context.suggested_language) > 0:
        return 1
    return 0

def create_actions() -> List[Action]:
    actions:List[Action] = [
        Action(
            name='ignore_row', 
            alt_names=['i'], 
            description='ignores row',
            action=ignore_row,
            default_value_calculation=ignore_row_default_value
        ),
        Action(
            name='split_subcategory', 
            alt_names=['s'], 
            description='Row is treated as a subcategory, and is split for further processing', 
            action=split_subcategory,
            default_value_calculation=split_subcategory_default_value
        ),
        Action(
            name='double_split_subcategory', 
            alt_names=['d'], 
            description='Row is split twice for further processing', 
            action=double_split_subcategory,
            default_value_calculation=double_split_subcategory_default_value
        ),
        Action(
            name='update_subcategory', 
            alt_names=['u'], 
            description='Allows users to edit default values for row', 
            action=update_subcategory,
            default_value_calculation=update_subcategory_default_value
        ),
        Action(
            name='guess_subcategory', 
            alt_names=['g'], 
            description='Assumes default values for row', 
            action=guess_subcategory,
            default_value_calculation=guess_subcategory_default_value
        ),
        Action(
            name='add_language', 
            alt_names=['l'], 
            description='Adds a new language to language suggestion table, row will be reprompted', 
            action=add_language,
            default_value_calculation=add_language_default_value
        )
    ]

    def help_action(context:ActionContext):
        print(f'Listed are the name of the action, the alternate names, as well as the description')
        for action in actions:
            print(f'{action.name} {action.alt_names}: {action.description}')
        print()
    
    def help_default_value_calculation(context:ActionContext):
        return -1

    actions.append(
        Action(
            name='help', 
            alt_names=['h'], 
            description='Prints out help for actions', 
            action=help_action,
            default_value_calculation=help_default_value_calculation
        )
    )

    return actions

def find_action(actions:List[Action], input_name:str) -> Optional[Action]:
    for action in actions:
        if action.equals_input(input_name):
            return action
    return None

def guess_action(actions:List[Action], context:ActionContext) -> Optional[Action]:
    return sorted(actions, key=lambda x: x.calculate_default_value(context))[-1]

def create_actions_guide(actions:List[Action], default_action:Action):
    return f'Please choose between {[x.name for x in actions]}\ndefault for empty: {default_action.name}\n'