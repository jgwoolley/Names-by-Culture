from urllib.parse import urlsplit

import os

def find_file_in_url(url:str) -> str:
    val = urlsplit(url)
    val = os.path.basename(val.path)
    return val