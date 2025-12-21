import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{os.path.join(BASE_DIR, sqlite_file_name)}"

if sqlite_url is None:
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_table():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session