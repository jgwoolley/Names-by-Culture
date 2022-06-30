import logging
import requests

from typing import List

def query(url:str, params:dict, session:requests.Session) -> List[dict]:
    R = session.get(url=url, params=params)
    data = R.json()
    return data

def query_category(url:str, params:dict, type_field:str, session:requests.Session) -> List[dict]:
    while True:
        data = query(url, params, session)
        if 'query' in data and type_field in data['query']:      
            for categorymember in data['query'][type_field]:
                yield categorymember['title']
            if 'continue' in data:
                params.update(data['continue'])        
            else:
                break
        else:
            break

def query_subcategory(url:str, cmtitle:str, session:requests.Session) -> List[dict]:  
    params = {
        'action': 'query',
        'cmtitle': cmtitle,
        'cmlimit': 'max',
        'cmtype': 'subcat',
        'list': 'categorymembers',
        'format': 'json'
    }
    
    for result in query_category(url, params, 'categorymembers', session=session):
        yield result

def query_category_pages(url:str, cmtitle:str) -> List[dict]:
    params = {
        'action': 'query',
        'cmtitle': cmtitle,
        'cmlimit': 'max',
        'cmtype': 'page',
        'list': 'categorymembers',
        'format': 'json'
    }
    for result in query_category(url, params, 'categorymembers', session=session):
        yield result

def query_page_categories(url:str,titles:str, session:requests.Session) -> List[dict]:
    params = {
        'action': 'query',
        'prop': 'categories',
        'titles': titles,
        'format': 'json'
    }
    for result in query_category(url, params, 'categories', session=session):
        yield result

def query_category_pages(url:str, cmtitle:str, session:requests.Session) -> List[dict]:
    params = {
        'action': 'query',
        'cmtitle': cmtitle,
        'cmlimit': 'max',
        'cmtype': 'page',
        'list': 'categorymembers',
        'format': 'json'
    }
    for result in query_category(url, params, 'categorymembers', session=session):
        yield result

# import wikitextparser as wtp
# return wtp.parse(data)

def query_wikitext(url:str, page:str, session:requests.Session):
    params = {
        'action': 'parse',
        'page': page,
        'format': 'json',
        'prop': 'wikitext'
    }
    data = query(url, params)
    if 'parse' in data:
        data = data['parse']
        if 'wikitext' in data:
            data = data['wikitext']
            if '*' in data:
                data = data['*']
                return data
    
    return None