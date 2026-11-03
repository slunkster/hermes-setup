"""Minimal Enable Banking API client. Put next to <APP_ID>.pem and set APP_ID.
Run with the Hermes python: pip install pyjwt cryptography requests
"""
import json, time
from pathlib import Path
import jwt, requests

APP_ID = "REPLACE-WITH-APP-ID"  # the .pem file name without extension
KEY = Path(__file__).with_name(f"{APP_ID}.pem").read_bytes()
BASE = "https://api.enablebanking.com"


def token(ttl=3600):
    iat = int(time.time())
    return jwt.encode(
        {"iss": "enablebanking.com", "aud": "api.enablebanking.com", "iat": iat, "exp": iat + ttl},
        KEY, algorithm="RS256", headers={"kid": APP_ID},
    )


def call(method, path, **kw):
    r = requests.request(method, BASE + path,
                         headers={"Authorization": f"Bearer {token()}", **kw.pop("headers", {})},
                         timeout=30, **kw)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


if __name__ == "__main__":
    code, body = call("GET", "/application")  # sanity check: key + status
    print(code, json.dumps(body, indent=2, ensure_ascii=False))
