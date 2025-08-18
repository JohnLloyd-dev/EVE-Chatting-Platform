import requests

resp = requests.post("http://localhost:8000/generate", json={
    "prompt": "What is the capital of France?",
    "max_tokens": 50
})

print(resp.json())
