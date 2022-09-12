import requests, sqlmodel

from .load_iso639_3 import (
    load as load_iso639_3
)
from .load_scripts import (
    load as load_scripts
)

def load(session:requests.Session, sql_session:sqlmodel.Session):    
    load_iso639_3(session=session, sql_session=sql_session)
    load_scripts(session=session, sql_session=sql_session)