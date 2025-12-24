from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email    : str = Field(unique=True, index=True)
    name     : str
    age      : int
    password : str

class Note(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title   : str
    content: str
    owner_id: Optional[int] = Field(foreign_key="user.id")