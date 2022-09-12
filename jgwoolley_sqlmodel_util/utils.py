from typing import Optional, Set, Type, Iterable, TextIO, Callable
from sqlmodel import SQLModel, Session
from tqdm import tqdm
from tqdm.notebook import tqdm_notebook
import csv, enum

from .models import TqdmType, TqdmMock

def create_tqdm(progress:Iterable[SQLModel], tqdm_type:TqdmType=TqdmType.none, desc:Optional[str]=None, total:Optional[int]=None):
    if tqdm_type == TqdmType.none:
        return TqdmMock(progress)
    if tqdm_type == TqdmType.tqdm:
        return tqdm(progress, desc=desc, total=total)
    elif tqdm_type == TqdmType.tqdm_notebook:
        return tqdm_notebook(progress, desc=desc, total=total)
    else:
        raise Exception(f'tqdm_type invalid: {tqdm_type}')

def get_fieldnames(cls:Type[SQLModel], exclude:Set[str]):
    return list({x for x in cls.__fields__.keys() if x not in exclude})