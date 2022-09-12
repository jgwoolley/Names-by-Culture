from typing import Optional, Set, Type, Iterable, TextIO, Callable
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