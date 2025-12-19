from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name     : str
    age      : int
    password : str

class Notes(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title   : str
    content: str
    owner_id: Optional[int] = Field(foreign_key="user.id")