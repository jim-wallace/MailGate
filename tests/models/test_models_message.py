import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.models import get_session_factory, Message

@pytest.fixture()
def temp_db(tmp_path: Path):
    db_path = tmp_path/"messages.db"
    Session = get_session_factory(str(db_path))
    return Session, db_path

def test_table_created(temp_db):
    Session, db_path = temp_db
    assert db_path.exists()

def test_insert_and_fetch_message(temp_db, tmp_path: Path):
    Session, db_path = temp_db
    mid = str(uuid.uuid4())
    eml_file = tmp_path / f"{mid}.eml"
    eml_file.write_text("From: a@b\nTo: c@d\nSubject: hello\n\nbody\n", encoding="utf-8")

    with Session() as s:
        m = Message(
        id=mid,
        from_addr = "a@b",
        to_addrs = json.dumps(["c@d"]),
        subject="hello",
        message_id = f"<{mid}@local>",
        size_bytes = 123,
        has_attachments = 0,
        eml_path=str(eml_file),
        )
        s.add(m)
        s.commit()

    with Session() as s:
        got = s.get(Message, mid)
        assert got is not None
        assert got.subject == "hello"
        assert got.from_addr == "a@b"
        assert got.to_addrs == json.dumps(["c@d"])
        assert Path(got.eml_path).exists()

def test_received_at_default_is_quick(temp_db):
    Session, db_path = temp_db
    mid=str(uuid.uuid4())
    with Session() as s:
        s.add(Message(id=mid))
        s.commit()
        got = s.get(Message, mid)
        assert isinstance(got.received_at, datetime)
        assert datetime.utcnow() - got.received_at < timedelta(seconds=1)

def test_indicies_exist_logically(temp_db):
    Session, db_path = temp_db

    with Session() as s:
        for i in range(5):
            s.add(Message(id=str(uuid.uuid4()), message_id=f"<m-{i}>"))
        s.commit()

        got = s.query(Message).filter_by(message_id="<m-3>").one()
        assert got is not None

