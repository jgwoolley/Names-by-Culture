import argparse

from typing import List
from .models import (
    LanguageName, 
    Language, 
    LanguageScriptRange, 
    WikiRecord, 
    WikiRecordStatus
)

def read_categories(args:argparse.ArgumentParser) -> List[WikiRecord]:
    #TODO: Potentially remove defautls, make this its own seperate file
    if args.categories is None:
        url = 'https://en.wiktionary.org/w/api.php'
        return [
            WikiRecord(    
                title = 'Category:Given names by language',
                url = url,
                category_type = 'given_names'
            ),
            WikiRecord(    
                title = 'Category:Surnames_by_language',
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

        for k, v in {'url': parent.url, 'category_type':parent.category_type, 'title': parent.title}.items():
            if v is None:
                raise TypeError(f'{k} must not be none for record: {parent}')

    with CachedSession(cache_name=args.cache_name, backend=args.backend) as session:
        engine = create_engine(args.sqlite_database)
        with Session(engine) as sql_session:
            SQLModel.metadata.create_all(engine)
            create_wikicategories(sql_session=sql_session, session=session, categories=categories)

models = {cls.__name__: cls for cls in [LanguageName, Language, LanguageScriptRange, WikiRecord]}

def _sql_to_csv(args:argparse.ArgumentParser):
    from sqlmodel import SQLModel, create_engine, Session, select
    from tqdm import tqdm
    import csv

    cls = models[args.model]

    writer = csv.DictWriter(args.out_csv, cls.__fields__.keys())
    writer.writeheader()

    engine = create_engine(args.sqlite_database)
    SQLModel.metadata.create_all(engine)
    print(f'Writing as {cls.__name__}')
    with Session(engine) as sql_session:
        statement = select(cls)
        with tqdm(sql_session.exec(statement), desc='in') as progress:
            for idx, row in enumerate(progress):
                writer.writerow(row.dict(row.dict(exclude={'id', 'status_backup'})))

def _csv_to_sql(args:argparse.ArgumentParser):
    from sqlmodel import SQLModel, create_engine, Session, select
    from sqlalchemy.exc import IntegrityError
    from tqdm import tqdm
    import csv

    cls = models[args.model]
    reader = csv.DictReader(args.in_csv)

    engine = create_engine(args.sqlite_database)
    SQLModel.metadata.create_all(engine)
    print(f'Reading as {cls.__name__}')
    with Session(engine) as sql_session, tqdm(reader, desc='out') as progress:
        for idx, row in enumerate(progress):
            record = cls.parse_obj(row)
            if len(record.dict()) == 0:
                raise Exception(f'Could not read row {idx}: {record} or {row}')

            sql_session.add(record)
            sql_session.commit()

# def _wikicategories_redo(args:argparse.ArgumentParser):
#     from sqlmodel import SQLModel, create_engine, Session, select
#     from tqdm import tqdm

#     engine = create_engine(args.sqlite_database)
#     SQLModel.metadata.create_all(engine)
#     with Session(engine) as sql_session:
#         # statement = select(WikiRecord).where(WikiRecord.status == WikiRecordStatus.skipped)
#         # for result in tqdm(sql_session.exec(statement)):
#         #     sql_session.delete(result)

#         statement = select(WikiRecord).where(WikiRecord.status == WikiRecordStatus.category)
#         for result in tqdm(sql_session.exec(statement)):
#             result:WikiRecord = result
#             result.status_backup = result.status
#             result.status = WikiRecordStatus.redo
#             sql_session.commit()

def _create_wikipages(args:argparse.ArgumentParser):
    from requests_cache import CachedSession
    from sqlmodel import SQLModel, create_engine, Session
    from .wiki_pages import create_wikipages

    with CachedSession(cache_name=args.cache_name, backend=args.backend) as session:
        engine = create_engine(args.sqlite_database)
        SQLModel.metadata.create_all(engine)
        with Session(engine) as sql_session:
            create_wikipages(sql_session=sql_session, session=session)

def _write_pages(args:argparse.ArgumentParser):
    from requests_cache import CachedSession
    from sqlmodel import SQLModel, create_engine, Session, select
    from tqdm import tqdm
    import os, csv, json

    with CachedSession(cache_name=args.cache_name, backend=args.backend) as session:
        engine = create_engine(args.sqlite_database)
        SQLModel.metadata.create_all(engine)
        with Session(engine) as sql_session:
            statement = select(WikiRecord).where(WikiRecord.status == WikiRecordStatus.page)
            metadata = []
            language_ids = set()
            category_types = set()
            with tqdm(sql_session.exec(statement), desc='find_language_ids') as progress:
                for row in progress:
                    language_ids.add(row.language_id)
                    category_types.add(row.category_type)
            
            with tqdm(language_ids, desc='languages') as progress:
                for language_id in progress:
                    progress.set_description_str(language_id)
                    metadatum = dict()
                    for category_type in category_types:
                        statement = select(WikiRecord).where(WikiRecord.status == WikiRecordStatus.page)
                        statement = statement.where(WikiRecord.language_id == language_id)
                        statement = statement.where(WikiRecord.category_type == category_type)

                        path = os.path.join(args.out_dir, language_id)
                        os.makedirs(path, exist_ok=True)            
                        path = os.path.join(path, category_type+'.csv')

                        count = 0
                        with open(path, 'w') as file:
                            writer = csv.DictWriter(file, WikiRecord.__fields__.keys())
                            writer.writeheader()
                            for idx, row in enumerate(sql_session.exec(statement)):
                                writer.writerow(row.dict(exclude={'id', 'status_backup'}))
                                count+=1
                        metadatum[category_type] = count
                    path = os.path.join(args.out_dir, language_id, 'metadata.json')
                    metadatum['total'] = sum(metadatum.values())
                    metadatum['language_id'] = language_id
                    with open(path, 'w') as file:
                        json.dump(metadatum, file)
                    metadata.append(metadatum)
            
            path = os.path.join(args.out_dir, 'metadata.csv')
            with open(path, 'w') as file:
                keys = [x for x in category_types]
                keys.append('total')
                keys.append('language_id')
                writer = csv.DictWriter(file, keys)
                writer.writeheader()
                metadata = sorted(metadata, key = lambda x: x['total'], reverse=True)
                for metadatum in metadata:
                    writer.writerow(metadatum)


def create_argparser() -> argparse.ArgumentParser:
    description='A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language'
    parser = argparse.ArgumentParser(description)

    parser.add_argument('--cache_name', metavar='c', dest='cache_name', default='names.db')
    parser.add_argument('--backend', metavar='b', dest='backend', default='sqlite')
    parser.add_argument('--sqlite_database', metavar='s', dest='sqlite_database', default='sqlite:///names.db')
    parser.add_argument('--categories', metavar='c', dest='categories', type=argparse.FileType('w'), default=None)

    subparsers = parser.add_subparsers(dest='command',help='sub-command help', required=True)
    subparsers.add_parser('wikicategories', help='Parse wiki-categories').set_defaults(func=_create_wikicategories)
    subparsers.add_parser('wikipages', help='Parse wiki-pages').set_defaults(func=_create_wikipages)
    
    subparser = subparsers.add_parser('wikipages_out', help='Write wiki-pages')
    subparser.add_argument('--out', metavar='o', dest='out_dir', required=True)
    subparser.set_defaults(func=_write_pages)

    subparser = subparsers.add_parser('out', help='output sql database to csv')
    subparser.add_argument('--out', metavar='o', dest='out_csv', type=argparse.FileType('w'), required=True)
    subparser.add_argument('--model', metavar='m', dest='model', choices=models.keys(), required=True)
    subparser.set_defaults(func=_sql_to_csv)

    subparser = subparsers.add_parser('in', help='ingest csv into sql database')
    subparser.add_argument('--in', metavar='i', dest='in_csv', type=argparse.FileType('r'), required=True)
    subparser.add_argument('--model', metavar='m', dest='model', choices=models.keys(), required=True)
    subparser.set_defaults(func=_csv_to_sql)

    #TODO: Properly test
    # subparser = subparsers.add_parser('wikicategories_redo', help='set all values of wiki-categories to unparsed')
    # subparser.set_defaults(func=_wikicategories_redo)   

    # wikipages_out = subparsers.add_parser('wikipages_out', help='output wiki-categories to csv')
    # wikipages_out.add_argument('--out', metavar='o', dest='out', type=argparse.FileType('w'), default='wikipages_out.csv')
    # wikipages_out.set_defaults(func=_wikipages_out)

    return parser

def main(args=None):
    parser = create_argparser()
    args = parser.parse_args(args)
    print(f'Executing: {args.command}')
    args.func(args)
    print(f'Completed')