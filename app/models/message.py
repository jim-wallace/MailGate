from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime
from .base import Base
from app.constants.database import message

class Message(Base):
    __tablename__ = message.TABLE_NAME
    id = Column(String, primary_key=True)
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    from_addr = Column(String)
    to_addrs = Column(Text)
    subject = Column(Text)
    message_id = Column(String, index=True)
    size_bytes = Column(Integer)
    has_attachments = Column(Integer)
    eml_path = Column(Text)
