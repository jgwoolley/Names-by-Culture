import requests
import csv
import sqlite3

from typing import Iterator, List

DEFAULT_URL = 'https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab'

def query_languages_from_web(session:requests.Session, url:str=DEFAULT_URL) -> str:
    if session is None:
        session = requests.Session()

    R = session.get(url=url)
    data = R.text
    return data

def parse_languages_from_text(tsv:str) -> Iterator[List[str]]:
    reader = csv.reader(tsv.splitlines(), delimiter='\t')
    header = next(reader)
    for line in reader:
        # data = {}
        # for idx, key in enumerate(header):
        #     data[key] = line[idx]
        yield line

def parse_languages_from_web(session:requests.Session, url:str=DEFAULT_URL) -> Iterator[List[str]]:
    result = query_languages_from_web(session=session)
    return parse_languages_from_text(result)

def write_languages_to_sql(session:requests.Session, connection:sqlite3.Connection, url:str=DEFAULT_URL):
    cur = connection.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS languages (id TEXT PRIMARY KEY, part2b TEXT, part2t TEXT, part1 TEXT, scope TEXT, language_type TEXT, ref_name TEXT, comment TEXT)')
    connection.commit()
    for result in parse_languages_from_web(url=url, session=session):
        cur.execute('INSERT OR IGNORE INTO languages VALUES (?, ?, ?, ?, ?, ?, ?, ?)', result)
    connection.commit()

def find_language_id(connection:sqlite3.Connection, language:str) -> str:
    cur = connection.cursor()
    cur.execute('SELECT id FROM languages WHERE ref_name=?', (language,))
    data = cur.fetchone()
    if data is not None:
        return data['id']

    return None

def find_language_ref_name(connection:sqlite3.Connection, language_id:str) -> str:
    cur = connection.cursor()
    cur.execute('SELECT ref_name FROM languages WHERE id=?', (language_id,))
    data = cur.fetchone()
    if data is not None:
        return data['ref_name']

    return None