import argparse

def create_argparser() -> argparse.ArgumentParser:
    description='A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language'
    parser = argparse.ArgumentParser(description)

    parser.add_argument('--wikimedia_url', metavar='u', dest='wikimedia_url', default='https://en.wiktionary.org/w/api.php')
    parser.add_argument('--cache_name', metavar='c', dest='cache_name', default='names_requests')
    parser.add_argument('--backend', metavar='b', dest='backend', default='sqlite')
    parser.add_argument('--sqlite_database', metavar='s', dest='sqlite_database', default='names.db')

    subparsers = parser.add_subparsers(dest='command',help='sub-command help', required=True)
    subparsers.add_parser('wikicategories', help='Parse wiki-categories')
    subparsers.add_parser('wikipages', help='Parse wiki-categories')
    wikicategories_out = subparsers.add_parser('wikicategories_out', help='output wiki-categories to csv')
    wikicategories_out.add_argument('--out', metavar='o', dest='out', type=argparse.FileType('w'), default='wikicategories_out.csv')

    wikipages_out = subparsers.add_parser('wikipages_out', help='output wiki-categories to csv')
    wikipages_out.add_argument('--out', metavar='o', dest='out', type=argparse.FileType('w'), default='wikipages_out.csv')


    return parser

def _create_wikicategories(args:argparse.ArgumentParser):
    from requests_cache import CachedSession
    import sqlite3
    from .wiki_pages import create_wikipages

    categories = {
        'surnames': ['Category:Surnames_by_language']
    }

    with CachedSession(cache_name=args.cache_name, backend=args.backend) as session:
        with sqlite3.connect(args.sqlite_database) as connection:
            create_wikicategories(connection=connection, session=session, url=args.wikimedia_url, categories=categories)

def _create_wikipages(args:argparse.ArgumentParser):
    from requests_cache import CachedSession
    import sqlite3
    from .wiki_pages import create_wikipages

    with CachedSession(cache_name=args.cache_name, backend=args.backend) as session:
        with sqlite3.connect(args.sqlite_database) as connection:
            create_wikipages(connection=connection, session=session, url=args.wikimedia_url)
   

def _wikicategories_out(args:argparse.ArgumentParser):
    from requests_cache import CachedSession
    import sqlite3, csv 

    with sqlite3.connect(args.sqlite_database) as connection:
        connection.row_factory = sqlite3.Row 
        cur = connection.cursor()
        cur.execute('SELECT * FROM wiki_categories')
        rows = cur.fetchall()
        keys = rows[0].keys()
        with args.out as outfile:
            csv_writer = csv.writer(outfile)
            csv_writer.writerow(keys)
            for row in rows:
                csv_writer.writerow(row)

def _wikipages_out(args:argparse.ArgumentParser):
    from requests_cache import CachedSession
    import sqlite3, csv 

    with sqlite3.connect(args.sqlite_database) as connection:
        connection.row_factory = sqlite3.Row 
        cur = connection.cursor()
        cur.execute('SELECT * FROM wiki_pages')
        rows = cur.fetchall()
        keys = rows[0].keys()
        with args.out as outfile:
            csv_writer = csv.writer(outfile)
            csv_writer.writerow(keys)
            for row in rows:
                csv_writer.writerow(row)

def main(args=None):
    parser = create_argparser()
    args = parser.parse_args(args)

    commands = {
        'wikicategories': _create_wikicategories,
        'wikipages': _create_wikipages,
        'wikicategories_out': _wikicategories_out,
        'wikipages_out': _wikipages_out
    }

    commands[args.command](args)