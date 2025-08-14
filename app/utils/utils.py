import os
from email import policy
from email.parser import BytesParser

def read_text_part(eml_path: str) -> tuple[dict, str]:
    headers, body = {}, ""
    if not eml_path or not os.path.exists(eml_path):
        return headers, body
    with open(eml_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    for k in ("From", "To", "Subject", "Date", "Message-ID"):
        v = msg.get(k)
        if v:
            headers[k] = str(v)
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
        if not body:
            for part in msg.walk():
                if part.get_content_maintype() == "text":
                    body = part.get_content()
                    break
    else:
        if msg.get_content_maintype() == "text":
            body = msg.get_content()
    return headers, body or ""
