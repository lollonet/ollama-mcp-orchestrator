import json, subprocess, sys, time, threading
reqs = [json.loads(l) for l in open("requests.jsonl") if l.strip()]
p = subprocess.Popen([".venv/bin/mcp-firewall","wrap","--config","policy.yaml","--",".venv/bin/python","fake_server.py"],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open("stderr2.txt","wb"))
out = []
def rd():
    for line in p.stdout:
        out.append(line.decode().strip())
t = threading.Thread(target=rd, daemon=True); t.start()
for r in reqs:
    p.stdin.write((json.dumps(r)+"\n").encode()); p.stdin.flush(); time.sleep(0.4)
time.sleep(1.0)
p.terminate()
print("RESPONSES SEEN BY CLIENT:")
for o in out: print("  ", o[:130])
