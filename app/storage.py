from __future__ import annotations
import json, os, shutil
from pathlib import Path
from sqlalchemy import select, delete
from app.models import get_session_factory, Message

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
                    "id": m.id,
                    "received_at": m.received_at,  # datetime (not string)
                    "from_addr": m.from_addr or "",
                    "to_addrs": ", ".join(json.loads(m.to_addrs or "[]")),
                    "subject": m.subject or "",
                    "size": m.size_bytes or 0,
                    "eml_path": m.eml_path or "",
                    "has_attachments": bool(m.has_attachments),
                }

    def get_message(self, mid: str) -> dict | None:
        with self.Session() as s:
            m = s.get(Message, mid)
            if not m:
                return None
            return {
                "id": m.id,
                "received_at": m.received_at,  # datetime (or None)
                "from_addr": m.from_addr or "",
                "to_addrs": json.loads(m.to_addrs or "[]"),
                "subject": m.subject or "",
                "size": m.size_bytes or 0,
                "eml_path": m.eml_path or "",
                "has_attachments": bool(m.has_attachments),
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