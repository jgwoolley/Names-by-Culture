import logging, requests, sqlmodel

from tqdm import tqdm
from time import sleep

from typing import Dict, List, Optional, Tuple
from jgwoolley_wikimedia import (
    query_subcategory, 
    query_category_pages, 
    query_wikitext, 
    query_category_info
)

from .languages import write_languages_to_sql, find_language_id
from .models import WikiRecord, Language, WikiRecordStatus, Gender, LanguageName
from .scripts import find_suggested_script, write_scripts_to_sql

def create_wikipages(sql_session:sqlmodel.Session, session:requests.Session, categories=List[WikiRecord]):
    print("Creating Language/Script Tables")
    write_languages_to_sql(sql_session=sql_session, session=session)
    write_scripts_to_sql(sql_session=sql_session, session=session)

    statement = sqlmodel.select(WikiRecord).where(WikiRecord.status == WikiRecordStatus.category)
    statement = statement.where(WikiRecord.language_id != None)
    statement = statement.where(WikiRecord.title != None)
    statement = statement.where(WikiRecord.url != None)
    results = sql_session.exec(statement)

    counter = dict()

    for parent in tqdm(results.fetchall()):
        counter['parents'] = counter.get('parent_no_keys', 0) + 1
        if len(dict(parent)) == 0:
            counter['parent_no_keys'] = counter.get('parent_no_keys', 0) + 1
            continue
        pages = query_category_pages(parent.url, parent.title, session)

        for page in pages:
            if page.startswith('Appendix:'):
                counter['appendix'] = counter.get('parent_no_pages', 0) + 1
                continue
            child = WikiRecord(
                name = page.split(' (')[0],
                title = page,
                gender = parent.gender,
                url = parent.url,
                parent_cmtitle = parent.title,
                language_id = parent.language_id,
                category_type = parent.category_type,
                status = WikiRecordStatus.page,
                language_script = find_suggested_script(sql_session=sql_session, names=page),
            )
            sql_session.add(child)
            try:
                sql_session.commit()
            except Exception as e:
                print('parent')
                print(parent)
                print('child')
                print(child)
                raise e
            counter['children'] = counter.get('parent_no_keys', 0) + 1
        sleep(1)
    print(f'Added {counter}')
