from __future__ import annotations
import argparse, json, os, uuid
from email.parser import BytesParser
from aiosmtpd.controller import Controller
from app.models import get_session_factory, Message

class SinkHandler:
    def __init__(self, store_dir: str, session_factory):
        self.store_dir = store_dir
        self.Session = session_factory
        os.makedirs(self.store_dir, exist_ok=True)

    async def handle_DATA(self, server, session, envelope):
        mid = str(uuid.uuid4())
        eml_path = os.path.join(self.store_dir, f"{mid}.eml")

        with open(eml_path, "wb") as f:
            f.write(envelope.original_content)

        msg = BytesParser().parsebytes(envelope.content)
        subject = msg.get("Subject", "") or ""
        message_id = msg.get("Message-ID", "") or ""
        has_attachments = 1 if msg.get_content_maintype() == "multipart" else 0

        rec = Message(
            id=mid,
            from_addr=envelope.mail_from or "",
            to_addrs=json.dumps(envelope.rcpt_tos or []),
            subject=subject,
            message_id=message_id,
            size_bytes=len(envelope.original_content),
            has_attachments=has_attachments,
            eml_path=eml_path,
        )
        with self.Session() as s:
            s.add(rec)
            s.commit()

        return "250 OK - captured"

def main():
    ap = argparse.ArgumentParser(description="SMTP capture listener")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1025)
    ap.add_argument("--store-dir", default="./localdata")
    ap.add_argument("--db", default="./localdata/messages.db")
    args=ap.parse_args()

    Session = get_session_factory(args.db)
    handler = SinkHandler(args.store_dir, Session)
    controller = Controller(handler, hostname=args.host, port=args.port)
    controller.start()
    print(f"SMTP capture running on {args.host}:{args.port} - {args.store_dir}")
    try:
        import threading; threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
