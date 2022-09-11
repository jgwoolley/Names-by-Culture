from typing import Optional, Set, Type, Iterable, Text, Callable
from sqlmodel import SQLModel, Session
from tqdm import tqdm
from tqdm.notebook import tqdm_notebook
import csv, enum

class TqdmMock:
    def __init__(self, progress):
        self.progress = progress
    
    def __enter__(self):
        return self
  
    def __exit__(self):
        ...

    def __iter__(self):
        return iter(self.progress)


class TqdmType(enum.Enum):
    tqdm = "tqdm"
    tqdm_notebook = "tqdm_notebook"
    none = "none"

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

def read_csv(sql_session:Session, f: Iterable[Text], cls:Type[SQLModel], tqdm_type:TqdmType=TqdmType.none, desc:Optional[str]=None, exclude:Optional[Set[str]]=None, on_record:Callable=lambda x: x, total:Optional[int]=None):
    if exclude is None:
        exclude = set()

    fieldnames = get_fieldnames(cls, exclude)
    progress = csv.DictReader(f, fieldnames)
    next(progress)
    progress = create_tqdm(progress, tqdm_type=tqdm_type, desc=desc, total=total)

    for idx, row in enumerate(progress):
        if row is None:
            continue
        row.pop(None, None)
        record = cls.parse_obj(row)
        record = on_record(record)
        sql_session.add(record)
        sql_session.commit()

def write_csv(sql_session:Session, statement, f: Iterable[Text], cls:Type[SQLModel], tqdm_type:TqdmType=TqdmType.none, desc:Optional[str]=None, exclude:Optional[Set[str]]=None, on_record:Callable=lambda x: x):
    if exclude is None:
        exclude = set()

    fieldnames = get_fieldnames(cls, exclude)
    writer = csv.DictWriter(f, fieldnames)
    writer.writeheader()

    progress = sql_session.exec(statement)
    progress = create_tqdm(progress, tqdm_type=tqdm_type, desc=desc)

    for idx, row in enumerate(progress):
        row = on_record(row)
        if row is None:
            continue
        writer.writerow(row.dict(exclude=exclude))