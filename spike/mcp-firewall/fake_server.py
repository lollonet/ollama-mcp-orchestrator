"""Minimal MCP-ish stdio server: answers anything it receives."""
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue
    method = msg.get("method", "")
    if method == "tools/call":
        path = msg.get("params", {}).get("arguments", {}).get("path", "?")
        out = {"jsonrpc": "2.0", "id": msg.get("id"),
               "result": {"content": [{"type": "text", "text": f"SERVER-EXECUTED: read {path}"}]}}
    elif method == "resources/read":
        uri = msg.get("params", {}).get("uri", "?")
        out = {"jsonrpc": "2.0", "id": msg.get("id"),
               "result": {"contents": [{"uri": uri, "text": f"SERVER-EXECUTED: resource {uri}"}]}}
    else:
        out = {"jsonrpc": "2.0", "id": msg.get("id"), "result": {"ok": True}}
    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()
