import argparse

from typing import List, Tuple
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
        return [
            WikiRecord(    
                title = 'Category:Given names by language',
                url = 'https://en.wiktionary.org/w/api.php',
                category_type = 'given_names'
            ),
            WikiRecord(    
                title = 'Category:Surnames_by_language',
                url = 'https://en.wiktionary.org/w/api.php',
                category_type = 'surnames'
            ),
            # WikiRecord(    
            #     title = 'Category:Cities by country',
            #     url = 'https://en.wikipedia.org/w/api.php',
            #     category_type = 'cities'
            # )
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

def _write_csv(args:argparse.ArgumentParser):
    from sqlmodel import SQLModel, create_engine, Session, select
    from .sqlmodel_csv import write_csv, TqdmType 

    cls = models[args.model]
    print(f'Writing as {cls.__name__}')
    engine = create_engine(args.sqlite_database)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as sql_session:
        statement = select(cls)
        write_csv(sql_session, statement, args.out_csv, cls, TqdmType.tqdm, 'Write Csv', {'id', 'status_backup'})


def _read_csv(args:argparse.ArgumentParser):
    from sqlmodel import SQLModel, create_engine, Session, select
    from .sqlmodel_csv import read_csv, TqdmType

    cls = models[args.model]
    print(f'Reading as {cls.__name__}')
    engine = create_engine(args.sqlite_database)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as sql_session:
        read_csv(sql_session, args.in_csv, cls, TqdmType.tqdm, 'Read Csv', {'id', 'status_backup'})

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

def _write_wikipages(args:argparse.ArgumentParser):
    from requests_cache import CachedSession
    from sqlmodel import SQLModel, create_engine, Session, select
    from tqdm import tqdm
    import os, csv, json
    from .sqlmodel_csv import write_csv, TqdmType, create_tqdm

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
            
            exclude = {'id', 'status_backup'}

            progress = create_tqdm(language_ids, TqdmType.tqdm, 'Languages')

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
                            def on_record(row):
                                count+=1
                                return row

                            write_csv(sql_session, statement, file, WikiRecord, TqdmType.none, exclude={'id', 'status_backup'}, on_record=on_record)
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

def _read_wikipages(args:argparse.ArgumentParser):
    from sqlmodel import SQLModel, create_engine, Session, select
    import os, csv

    from .sqlmodel_csv import write_csv, read_csv, TqdmType, create_tqdm, get_fieldnames

    engine = create_engine(args.sqlite_database)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as sql_session:
        exclude = {'id', 'status_backup'}
        fieldnames = get_fieldnames(WikiRecord, exclude)
        count = 0
        with open(args.out_csv, 'w') as file:
            writer = csv.DictWriter(file, fieldnames)
            writer.writeheader()

            for root,dirs,files in create_tqdm(os.walk(args.in_dir),TqdmType.tqdm, 'Write WikiPages'):
                for file_name in files:
                    if not file_name.endswith('.csv'):
                        continue
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'r') as file:
                        progress = csv.DictReader(file, fieldnames)
                        next(progress)
                        for row in progress:
                            if row is None:
                                continue
                            row.pop(None, None)
                            writer.writerow(row)
                            count+=1
        with open(args.out_csv, 'r') as file:
            read_csv(sql_session, file, WikiRecord, TqdmType.tqdm, 'Read WikiPages', exclude, total=count)

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
    
    subparser = subparsers.add_parser('write_wikipages', help='Write wikipages')
    subparser.add_argument('--out', metavar='o', dest='out_dir', required=True)
    subparser.set_defaults(func=_write_wikipages)

    subparser = subparsers.add_parser('read_wikipages', help='Read wikipages')
    subparser.add_argument('--in', metavar='i', dest='in_dir', required=True)
    subparser.add_argument('--out', metavar='o', dest='out_csv', required=True)
    subparser.set_defaults(func=_read_wikipages)

    subparser = subparsers.add_parser('write_csv', help='output sql database to csv')
    subparser.add_argument('--out', metavar='o', dest='out_csv', type=argparse.FileType('w'), required=True)
    subparser.add_argument('--model', metavar='m', dest='model', choices=models.keys(), required=True)
    subparser.set_defaults(func=_write_csv)

    subparser = subparsers.add_parser('read_csv', help='ingest csv into sql database')
    subparser.add_argument('--in', metavar='i', dest='in_csv', type=argparse.FileType('r'), required=True)
    subparser.add_argument('--model', metavar='m', dest='model', choices=models.keys(), required=True)
    subparser.set_defaults(func=_read_csv)

    #TODO: add
    # subparser = subparsers.add_parser('wikicategories_redo', help='set all values of wiki-categories to unparsed')
    # subparser.set_defaults(func=_wikicategories_redo)   

    return parser

def main(args=None):
    parser = create_argparser()
    args = parser.parse_args(args)
    print(f'Executing: {args.command}')
    args.func(args)
    print(f'Completed')