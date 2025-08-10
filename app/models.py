from __future__ import annotations
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime
from pathlib import Path
import os

class Base(DeclarativeBase):
    pass

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    from_addr = Column(String)
    to_addrs = Column(Text)
    subject = Column(Text)
    message_id = Column(String, index=True)
    size_bytes = Column(Integer)
    has_attachments = Column(Integer)
    eml_path = Column(Text)

def get_session_factory(db_path: str) -> sessionmaker:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)

