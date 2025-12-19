from sqlmodel import SQLModel

class BaseNotes(SQLModel):
    title   : str
    content: str

class CreateNotes(BaseNotes):
    pass

class ReadNotes(BaseNotes):
    id:int
    owner_id: int