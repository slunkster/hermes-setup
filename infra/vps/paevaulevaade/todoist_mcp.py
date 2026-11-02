#!/usr/bin/env python3
"""Read-only Todoist MCP client (streamable HTTP). Never prints tokens."""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

TOK = os.path.expanduser("~/.hermes/mcp-tokens/todoist.json")
CLI = os.path.expanduser("~/.hermes/mcp-tokens/todoist.client.json")
META = os.path.expanduser("~/.hermes/mcp-tokens/todoist.meta.json")
URL = "https://ai.todoist.net/mcp"


def refresh():
    t = json.load(open(TOK)); c = json.load(open(CLI)); m = json.load(open(META))
    data = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": t["refresh_token"],
                                   "client_id": c["client_id"]}).encode()
    req = urllib.request.Request(m["token_endpoint"], data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=30))
    t.update(r)
    if "expires_in" in r:
        t["expires_at"] = time.time() + int(r["expires_in"])
    tmp = TOK + ".tmp"
    with open(tmp, "w") as f:
        json.dump(t, f)
    os.chmod(tmp, 0o600); os.replace(tmp, TOK)
    print("[token refreshed]", file=sys.stderr)


def token():
    t = json.load(open(TOK))
    if t.get("expires_at", 0) < time.time() + 60:
        refresh(); t = json.load(open(TOK))
    return t["access_token"]


class MCP:
    def __init__(self):
        self.sid = None; self.id = 0; self.tok = token()

    def post(self, payload):
        h = {"Authorization": "Bearer " + self.tok, "Content-Type": "application/json",
             "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-06-18"}
        if self.sid: h["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=h, method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=60)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:500].decode(errors='replace')}")
        self.sid = resp.headers.get("Mcp-Session-Id") or self.sid
        body = resp.read().decode()
        if not body.strip(): return None
        if "text/event-stream" in (resp.headers.get("Content-Type") or ""):
            out = None
            for line in body.splitlines():
                if line.startswith("data:"):
                    try:
                        msg = json.loads(line[5:].strip())
                        if "id" in msg: out = msg
                    except ValueError: pass
            return out
        return json.loads(body)

    def req(self, method, params=None):
        self.id += 1
        r = self.post({"jsonrpc": "2.0", "id": self.id, "method": method, "params": params or {}})
        if r and "error" in r: raise RuntimeError(json.dumps(r["error"]))
        return r["result"] if r else None

    def start(self):
        self.req("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                "clientInfo": {"name": "hermes-paevaulevaade", "version": "1.0"}})
        self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return self

    def call(self, name, args):
        return self.req("tools/call", {"name": name, "arguments": args})


if __name__ == "__main__":
    m = MCP().start()
    cmd = sys.argv[1]
    if cmd == "list":
        for t in m.req("tools/list")["tools"]:
            print("==", t["name"], "|", (t.get("description") or "")[:200].replace("\n", " "))
            print("   args:", json.dumps(t.get("inputSchema", {}).get("properties", {}))[:600])
    else:
        print(json.dumps(m.call(cmd, json.loads(sys.argv[2] if len(sys.argv) > 2 else "{}")), ensure_ascii=False, indent=1))
