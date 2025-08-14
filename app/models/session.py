from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base

def get_engine(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)

def init_db(engine):
    Base.metadata.create_all(engine)

def get_session_factory(db_path: str) -> sessionmaker:
    engine = get_engine(db_path)
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)