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

# def query_category_pages(url:str, cmtitle:str) -> List[dict]:
#     params = {
#         'action': 'query',
#         'cmtitle': cmtitle,
#         'cmlimit': 'max',
#         'cmtype': 'page',
#         'list': 'categorymembers',
#         'format': 'json'
#     }
#     for result in query_category(url, params, 'categorymembers', session=session):
#         yield result

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

def query_category_info(url:str, title:str, session:requests.Session) -> List[dict]:
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'categoryinfo',
        'format': 'json'
    }
    data = query(url, params, session)
    data = data.get('query')
    if not isinstance(data, dict):
        raise TypeError(f'{type(data)} not dict')
    
    normalized_values = dict()
    normalized = data.get('normalized')
    if isinstance(normalized, list):
        for normalized_value in normalized:
            from_value = normalized_value['from']
            to_value = normalized_value['to']
            normalized_values[to_value] = from_value

    data = data.get('pages')
    if not isinstance(data, dict):
        raise TypeError(f'{type(data)} not dict')


    for page in data.values():
        if not isinstance(page, dict):
            raise TypeError(f'{type(data)} not dict')

        if page.get('missing') is not None:
            raise Exception(f'Value is missing: {title}')

        page_title = page.get('title')

        if page_title == title:
            return page.get('categoryinfo')
        
        page_title = normalized_values[page_title]

        if page_title == title:
            return page.get('categoryinfo')

    raise Exception(f'No values in pages')


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