import logging, requests, sqlmodel

from itertools import islice
from typing import Dict, List, Optional, Tuple
from jgwoolley_wikimedia import (
    query_subcategory, 
    query_category_pages, 
    query_wikitext, 
    query_category_info
)

from jgwoolley_languages import (
    find_language_id,
    find_suggested_script,
    load_all
)
from ..models import WikiRecord, Language, WikiRecordStatus, Gender, LanguageName

from .models import CategoryInfo, Action, ActionContext

from .actions import (
    get_cmtitle_tokens,
    find_suggested_gender,
    find_suggested_language,
    split_subcategory, 
    create_actions, 
    find_action, 
    guess_action,
    create_actions_guide
)
def process_parent(sql_session:sqlmodel.Session, session:requests.Session, parent:WikiRecord) -> Tuple[str, str, str]:
    if not isinstance(parent, WikiRecord):
        raise Exception(f'Given category isn\'t WikiRecord: {type(parent)}')

    category_type = parent.category_type
    parent_cmtitle = parent.title
    url = parent.url

    for k, v in {'url': url, 'category_type':category_type, 'cmtitle': parent_cmtitle}.items():
        if v is None:
            raise TypeError(f'{k} must not be none for record: {parent}')

    statement = sqlmodel.select(WikiRecord).where(WikiRecord.title == parent_cmtitle)
    results = sql_session.exec(statement)
    if not results.first():
        row = WikiRecord(
            title = parent_cmtitle,
            url = url,
            category_type = category_type
        )
        sql_session.add(row)
        sql_session.commit()

        context = ActionContext(
            sql_session=sql_session,
            session=session,
            row=row,
            cmtitle_tokens=get_cmtitle_tokens(row),
            example_pages=[],
            category_info=None,
            suggested_language=None,
            suggested_gender=None
        )

        #TODO: Possibly reenable
        # split_subcategory(context=context)

    return (category_type, parent_cmtitle, url)

def create_wikicategories(sql_session:sqlmodel.Session, session:requests.Session, categories=List[WikiRecord]):
    load_all(sql_session=sql_session, session=session)
    actions = create_actions()

    for parent in categories:
        category_type, parent_cmtitle, url = process_parent(sql_session=sql_session, session=session, parent=parent)

        while True:
            statement = sqlmodel.select(WikiRecord)
            statement = statement.where(
                sqlmodel.or_(WikiRecord.status == WikiRecordStatus.unevaluated,
                    WikiRecord.status == WikiRecordStatus.redo
                ),
                WikiRecord.category_type == category_type
                )
            results = sql_session.exec(statement)

            row:WikiRecord = results.first()
            if row is None:
                break

            cmtitle_tokens = get_cmtitle_tokens(row)
            suggested_gender = row.gender.value if row.gender else find_suggested_gender(sql_session=sql_session, cmtitle_tokens=cmtitle_tokens)
            suggested_language = row.language_id if row.language_id else find_suggested_language(sql_session=sql_session, cmtitle_tokens=cmtitle_tokens)
            category_info = CategoryInfo(**query_category_info(url=url, title=row.title, session=session))

            example_pages = [x for x in islice(query_category_pages(url=url, cmtitle=row.title, session=session), 5)]
            example_subcategories = [x for x in islice(query_subcategory(url=url, cmtitle=row.title, session=session), 5)]

            #TODO: Is it assuming too much that all the subcategories will be of the same script?
            suggested_script = row.language_script if row.language_script else find_suggested_script(sql_session=sql_session, names=example_pages)
            if suggested_script is None:
                suggested_script = suggested_language

            context = ActionContext(
                sql_session=sql_session,
                session=session,
                row=row,
                cmtitle_tokens=cmtitle_tokens,
                example_pages=example_pages,
                category_info=category_info,
                suggested_language=suggested_language,
                suggested_gender=suggested_gender,
                suggested_script = suggested_script
            )

            default_action = guess_action(actions=actions, context=context)
            actions_guide = create_actions_guide(actions=actions, default_action=default_action)

            print(f'{" ".join(cmtitle_tokens)} [category_type=\"{row.category_type}\"]')
            print(f'\"suggested_language=\"{suggested_language}\", \"suggested_script\"=\"{suggested_script}\", suggested_gender=\"{suggested_gender}\"')
            print(f'category_info={category_info}')
            print(f'example_pages={example_pages}')
            print(f'example_subcategories={example_subcategories}')

            action:Action = None
            while action is None:
                input_name = input(actions_guide).lower()
                if len(input_name) > 0:
                    action = find_action(actions=actions, input_name=input_name)
                    continue
                action = default_action
            
            action.action(context)
