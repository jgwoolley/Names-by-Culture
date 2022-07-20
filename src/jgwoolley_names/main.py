import argparse

from typing import List
from .model import WikiRecord

def read_categories(args:argparse.ArgumentParser) -> List[WikiRecord]:
    if args.categories is None:
        url = 'https://en.wiktionary.org/w/api.php'
        return [
            WikiRecord(    
                cmtitle = 'Category:Given names by language',
                url = url,
                category_type = 'given_names'
            ),
            WikiRecord(    
                cmtitle = 'Category:Surnames_by_language',
                url = url,
                category_type = 'surnames'
            )
        ]
    
    import json
    with args.categories.open('r') as fp:
        return [WikiRecord.parse_obj(x) for x in json.load(fp)]

def _create_wikicategories(args:argparse.ArgumentParser):
    from requests_cache import CachedSession
    from sqlmodel import SQLModel, create_engine, Session
    from .wiki_categories import create_wikicategories

    categories = read_categories(args)
    for parent in categories:
        if not isinstance(parent, WikiRecord):
            raise Exception(f'Given category isn\'t WikiRecord: {type(parent)}')

        for k, v in {'url': parent.url, 'category_type':parent.category_type, 'cmtitle': parent.cmtitle}.items():
            if v is None:
                raise TypeError(f'{k} must not be none for record: {parent}')

    with CachedSession(cache_name=args.cache_name, backend=args.backend) as session:
        engine = create_engine(args.sqlite_database)
        SQLModel.metadata.create_all(engine)
        with Session(engine) as sql_session:
            create_wikicategories(sql_session=sql_session, session=session, categories=categories)

# def _create_wikipages(args:argparse.ArgumentParser):
#     from requests_cache import CachedSession
#     from sqlmodel import SQLModel, create_engine, Session
#     from .wiki_pages import create_wikipages

#     with CachedSession(cache_name=args.cache_name, backend=args.backend) as session:
#         engine = create_engine(args.sqlite_database)
#         SQLModel.metadata.create_all(engine)
#         with Session(engine) as sql_session:
#             create_wikipages(sql_session=sql_session, session=session)
   

# def _wikicategories_out(args:argparse.ArgumentParser):
#     from requests_cache import CachedSession
#     from sqlmodel import SQLModel, create_engine, Session
#     import csv 

#     engine = create_engine(args.sqlite_database)
#     SQLModel.metadata.create_all(engine)
#     with Session(engine) as sql_session:
#         connection.row_factory = sqlite3.Row 
#         cur = connection.cursor()
#         cur.execute('SELECT * FROM wiki_categories')
#         rows = cur.fetchall()
#         keys = rows[0].keys()
#         with args.out as outfile:
#             csv_writer = csv.writer(outfile)
#             csv_writer.writerow(keys)
#             for row in rows:
#                 csv_writer.writerow(row)

# def _wikipages_out(args:argparse.ArgumentParser):
#     from requests_cache import CachedSession
#     from sqlmodel import SQLModel, create_engine, Session
#     import csv 

#     engine = create_engine(args.sqlite_database)
#     SQLModel.metadata.create_all(engine)
#     with Session(engine) as sql_session:
#         connection.row_factory = sqlite3.Row 
#         cur = connection.cursor()
#         cur.execute('SELECT * FROM wiki_pages')
#         rows = cur.fetchall()
#         keys = rows[0].keys()
#         with args.out as outfile:
#             csv_writer = csv.writer(outfile)
#             csv_writer.writerow(keys)
#             for row in rows:
#                 csv_writer.writerow(row)

def create_argparser() -> argparse.ArgumentParser:
    description='A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language'
    parser = argparse.ArgumentParser(description)

    parser.add_argument('--cache_name', metavar='c', dest='cache_name', default='names.db')
    parser.add_argument('--backend', metavar='b', dest='backend', default='sqlite')
    parser.add_argument('--sqlite_database', metavar='s', dest='sqlite_database', default='sqlite:///names.db')
    parser.add_argument('--categories', metavar='c', dest='categories', type=argparse.FileType('w'), default=None)

    subparsers = parser.add_subparsers(dest='command',help='sub-command help', required=True)
    subparsers.add_parser('wikicategories', help='Parse wiki-categories').set_defaults(func=_create_wikicategories)
    # subparsers.add_parser('wikipages', help='Parse wiki-categories').set_defaults(func=_create_wikipages)

    # wikicategories_out = subparsers.add_parser('wikicategories_out', help='output wiki-categories to csv')
    # wikicategories_out.add_argument('--out', metavar='o', dest='out', type=argparse.FileType('w'), default='wikicategories_out.csv')
    # wikicategories_out.set_defaults(func=_wikicategories_out)

    # wikipages_out = subparsers.add_parser('wikipages_out', help='output wiki-categories to csv')
    # wikipages_out.add_argument('--out', metavar='o', dest='out', type=argparse.FileType('w'), default='wikipages_out.csv')
    # wikipages_out.set_defaults(func=_wikipages_out)

    return parser

def main(args=None):
    parser = create_argparser()
    args = parser.parse_args(args)
    args.func(args)