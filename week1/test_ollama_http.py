import json
import urllib.request

url = "http://127.0.0.1:11434/api/generate"

data = {
    "model": "llama3.1:8b",
    "prompt": "hello",
    "stream": False
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(req) as resp:
    print(resp.status)
    print(resp.read().decode("utf-8"))
