import logging, requests, sqlite3

from jgwoolley_wikimedia import query_subcategory, query_category_pages, query_wikitext
from typing import Dict, List, Optional, Tuple

from .languages import write_languages_to_sql, find_language_ref_name, find_language_id

def create_table(connection:sqlite3.Connection):
    cur = connection.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS wiki_categories (cmtitle TEXT PRIMARY KEY, type TEXT, status TEXT, language_id TEXT, parent_cmtitle TEXT)')
    connection.commit()

def split_subcategory(url:str, cmtitle:str, parent_cmtitle:str, category_type:str, connection:sqlite3.Connection, session:requests.Session):
    cur = connection.cursor()
    cur.execute('UPDATE wiki_categories SET status = ? WHERE cmtitle = ?', ('split', cmtitle))
    connection.commit()

    for child_cmtitle in query_subcategory(url, cmtitle, session):
        cur.execute('INSERT OR IGNORE INTO wiki_categories VALUES (?, ?, ?, ?, ?)', (child_cmtitle, category_type, 'unevaluated', 'unevaluated', cmtitle))
    connection.commit()

def find_suggested_languages(connection:sqlite3.Connection, row:sqlite3.Row) -> List[str]:
    suggested_languages = []
    for language in row['cmtitle'].split(':')[-1].split():
        language_id = find_language_id(connection, language)
        if not language_id is None:
            suggested_languages.append(language)
    return suggested_languages

def choose_language(connection:sqlite3.Connection, row:sqlite3.Row) -> str:
    suggested_languages = find_suggested_languages(connection=connection, row=row)
    languages_guide = f'Please select a language for {row["cmtitle"]} {suggested_languages} or type \"exit\"\n'

    print(f'{row["cmtitle"]}: {suggested_languages}')
    language_id=None
    while language_id is None:
        value = input(languages_guide).lower()
        if value == 'exit':
            return None

        if len(value) == 0 and len(suggested_languages) != 1:
            continue

        if len(value) == 0 and len(suggested_languages) == 1:
            value = suggested_languages[0]
        
        if find_language_ref_name(connection, value) is not None:
            language_id = value
            break

        language_id = find_language_id(connection=connection, language=value)

    return language_id

def update_subcategory(url:str, cmtitle:str, connection:sqlite3.Connection, row:sqlite3.Row):
    language_id = choose_language(connection=connection, row=row)
    if language_id is None:
        return
    cur = connection.cursor()
    cur.execute('UPDATE wiki_categories SET status = ?, language_id = ? WHERE cmtitle = ?', ('evaluated', language_id, cmtitle))
    connection.commit() 

def create_actions(actions:List[str]) -> Tuple[Dict[str,str], str]:
    actions_dict = dict()
    for action in actions:
        action = action.lower()
        letter = action[0]
        actions_dict[action] = letter
        actions_dict[letter] = letter

    actions_guide = 'Please provide one of the following: ' + ', '.join([f'[{x[0:1]}]{x[1:]}' for x in actions]) + '\n'
    return (actions_dict, actions_guide)

def main(connection:sqlite3.Connection, session:requests.Session, url:str, categories=Dict[str, List[str]]):
    write_languages_to_sql(session, connection)
    create_table(connection)
    connection.row_factory = sqlite3.Row 

    actions, actions_guide = create_actions(['update', 'split', 'ignore'])

    for category_type, parent_cmtitles in categories.items():
        cur = connection.cursor()
        for parent_cmtitle in parent_cmtitles:
            cur.execute('INSERT OR IGNORE INTO wiki_categories VALUES (?, ?, ?, ?, ?)', (parent_cmtitle, category_type, 'unevaluated', 'unevaluated', 'None'))
            split_subcategory(url=url, cmtitle=parent_cmtitle, parent_cmtitle='None', category_type=category_type, connection=connection, session=session)
        connection.commit()

        while True:
            cur.execute('SELECT * FROM wiki_categories WHERE status = "unevaluated" AND type = ?', (category_type, ))
            row = cur.fetchone()
            if row is None:
                break

            cmtitle = row["cmtitle"]
            print(f'{cmtitle} [{row["type"]}]')
            action = None
            while not action in actions:
                text = input(actions_guide).lower()
                action = actions.get(text[0], None) if len(text) > 0 else 'u'
            
            if action == 'u':
                update_subcategory(url=url, cmtitle=cmtitle, connection=connection, row=row)                
            elif action == 's':
                split_subcategory(url=url, cmtitle=cmtitle, parent_cmtitle=parent_cmtitle, category_type=category_type, connection=connection, session=session)
            elif action == 'i':
                cur.execute('UPDATE wiki_categories SET status = ? WHERE cmtitle = ?', ('ignored', cmtitle))
                connection.commit()
            else:
                raise Exception(f'There is no action {action} in {list(actions.keys())}')
