from .main import main

if __name__ == '__main__':
    from requests_cache import CachedSession
    import sqlite3
    from .main import main

    url = 'https://en.wiktionary.org/w/api.php'

    categories = {
        'surnames': ['Category:Surnames_by_language']
    }

    with CachedSession('names_requests') as session:
        with sqlite3.connect('names.db') as connection:
            main(connection=connection, session=session, url=url, categories=categories)
    