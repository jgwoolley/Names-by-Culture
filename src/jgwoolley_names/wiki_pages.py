import logging, requests, sqlite3

from jgwoolley_wikimedia import query_subcategory, query_category_pages, query_wikitext
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
from time import sleep

def create_table(connection:sqlite3.Connection):
    cur = connection.cursor()
    cur.execute('DROP TABLE wiki_pages')
    connection.commit()

    cur.execute('CREATE TABLE IF NOT EXISTS wiki_pages (cmtitle TEXT NOT NULL, type TEXT NOT NULL, language_ids NOT NULL, genders NOT NULL, parent_cmtitle NOT NULL)')
    connection.commit()

def create_wikipages(connection:sqlite3.Connection, session:requests.Session):
    #TODO: Removed url:str
    create_table(connection=connection)
    connection.row_factory = sqlite3.Row 
    cur = connection.cursor()
    cur.execute('SELECT cmtitle, type, language_id, gender FROM wiki_categories WHERE status = "evaluated"')

    for category_row in tqdm(cur.fetchall()):
        parent_cmtitle = category_row['cmtitle']
        category_type = category_row['type']
        language_ids = {category_row['language_id']}
        genders = {category_row['gender']}

        for cmtitle in query_category_pages(url=url, cmtitle=parent_cmtitle, session=session):
            cur.execute('SELECT cmtitle, type, language_ids, genders, parent_cmtitle FROM wiki_pages WHERE cmtitle = ? AND type = ? AND parent_cmtitle = ?', (cmtitle, category_type, parent_cmtitle))
            row = cur.fetchone()
            if row is None:
                cur.execute('INSERT INTO wiki_pages VALUES (?, ?, ?, ?, ?)', (cmtitle, category_type, ','.join(genders), ','.join(language_ids), parent_cmtitle))
            else:
                language_ids.update(category_row['language_id'].split(','))
                genders.update(category_row['gender'].split(',')) 
                cur.execute('UPDATE wiki_pages SET language_ids = ?, genders = ? WHERE cmtitle = ? AND type = ? AND parent_cmtitle = ?', (','.join(genders), ','.join(language_ids), cmtitle, category_type, parent_cmtitle))
        connection.commit()
        sleep(0.1)
