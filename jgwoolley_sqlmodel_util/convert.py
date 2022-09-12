from typing import Optional, Set, Type, Iterable, TextIO, Callable
from sqlmodel import SQLModel, Session
from tqdm import tqdm
from tqdm.notebook import tqdm_notebook
import csv, enum

from .models import TqdmType, TqdmMock
from .utils import create_tqdm, get_fieldnames

def read_csv(sql_session:Session, f: Iterable[TextIO], cls:Type[SQLModel], tqdm_type:TqdmType=TqdmType.none, desc:Optional[str]=None, exclude:Optional[Set[str]]=None, on_record:Callable=lambda x: x, total:Optional[int]=None):
    if exclude is None:
        exclude = set()

    # fieldnames = get_fieldnames(cls, exclude)
    progress = csv.DictReader(f)#, fieldnames)
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
 
def write_csv(sql_session:Session, statement, f: Iterable[TextIO], cls:Type[SQLModel], tqdm_type:TqdmType=TqdmType.none, desc:Optional[str]=None, exclude:Optional[Set[str]]=None, on_record:Callable=lambda x: x):
    if exclude is None:
        exclude = set()

    #fieldnames = get_fieldnames(cls, exclude)
    writer = csv.DictWriter(f)#, fieldnames)
    writer.writeheader()

    progress = sql_session.exec(statement)
    progress = create_tqdm(progress, tqdm_type=tqdm_type, desc=desc)

    for idx, row in enumerate(progress):
        row = on_record(row)
        if row is None:
            continue
        writer.writerow(row.dict(exclude=exclude))