from __future__ import annotations
import json, os, shutil
from pathlib import Path
from sqlalchemy import select, delete
from app.models import get_session_factory, Message
from app.constants.database import message

class Store:
    def __init__(self, db_path: str, store_dir: str):
        self.Session = get_session_factory(db_path)
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def list_messages(self, limit: int = 500):
        from sqlalchemy import select
        with self.Session() as s:
            rows = s.execute(
                select(Message).order_by(Message.received_at.desc()).limit(limit)
            ).scalars().all()
            for m in rows:
                yield {
                    message.COL_ID: m.id,
                    message.COL_RECEIVED_AT: m.received_at,
                    message.COL_FROM_ADDR: m.from_addr or "",
                    message.COL_TO_ADDRS: ", ".join(json.loads(m.to_addrs or "[]")),
                    message.COL_SUBJECT: m.subject or "",
                    message.COL_SIZE: m.size_bytes or 0,
                    message.COL_EML_PATH: m.eml_path or "",
                    message.COL_HAS_ATTACHMENTS: bool(m.has_attachments),
                }

    def get_message(self, mid: str) -> dict | None:
        with self.Session() as s:
            m = s.get(Message, mid)
            if not m:
                return None
            return {
                message.COL_ID: m.id,
                message.COL_RECEIVED_AT: m.received_at,  # datetime (or None)
                message.COL_FROM_ADDR: m.from_addr or "",
                message.COL_TO_ADDRS: json.loads(m.to_addrs or "[]"),
                message.COL_SUBJECT: m.subject or "",
                message.COL_SIZE: m.size_bytes or 0,
                message.COL_EML_PATH: m.eml_path or "",
                message.COL_HAS_ATTACHMENTS: bool(m.has_attachments),
            }

    def delete_message(self, mid: str) -> bool:
        with self.Session() as s:
            m = s.get(Message, mid)
            if not m: return False

            try:
                if m.eml_path and os.path.exists(m.eml_path):
                    os.remove(m.eml_path)
            except Exception:
                pass
            s.execute(delete(Message).where(Message.id == mid))
            s.commit()
            return True

    def export_message(self, mid:str, dest_dir: str) -> str | None:
        info = self.get_message(mid)
        if not info: return None
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        dest = Path(dest_dir) / f"{mid}.eml"
        shutil.copy(info["eml_path"], dest)
        return str(dest)