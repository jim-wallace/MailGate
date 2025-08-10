from __future__ import annotations
import os, json
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy import select
from app.models import get_session_factory, Message

API_TOKEN = os.getenv("API_TOKEN", "change_me")
DB_PATH = os.getenv("DB_PATH", "./localdata/messages.db")

Session = get_session_factory(DB_PATH)
app = FastAPI(title = "SMTP Sink API")

def _auth(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer"):
        raise HTTPException(401, "Missing token")
    token = authorization.split(" ", 1)[1]
    if token != API_TOKEN:
        raise HTTPException(401, "Invalid token")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/messages")
def list_messages(authorization: str | None = Header(None), limit: int = 100) :
    _auth(authorization)
    with Session() as s:
        rows = s.execute(
            select(Message).order_by(Message.received_at.desc()).limit(limit)
        ).scalars().all()
        return [
            {
                "id": m.id,
                "received_at": m.received_at.isoformat() if m.received_at else None,
                "from": m.from_addr,
                "to": json.loads(m.to_addrs or "[]"),
                "subject": m.subject,
                "size": m.size_bytes,
                "has_attachments": bool(m.has_attachments),
             } for m in rows
        ]

@app.get("/messages/{mid}/raw")
def get_raw(mid: str, authorization: str | None = Header(None)):
    _auth(authorization)
    with Session() as s:
        m = s.get(Message, mid)
        if not m: raise HTTPException(404, "Not found")
        return FileResponse(
            m.eml_path,
            media_type="message/rfc822",
            filename=f"{mid}.eml"
        )