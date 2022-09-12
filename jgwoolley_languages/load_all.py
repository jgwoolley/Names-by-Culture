import requests, csv, sqlmodel
from typing import Optional, Iterable, Type, TextIO, Callable, Set, List
from .models import LanguageName, Language, LanguageScriptRange, ConfigurableModel

from .load_iso639_3 import (
    load as load_iso639_3
)
from .load_scripts import (
    load as load_scripts
)

def load_all(session:requests.Session, sql_session:sqlmodel.Session):    
    load_iso639_3(session, sql_session)
    load_scripts(session, sql_session)
