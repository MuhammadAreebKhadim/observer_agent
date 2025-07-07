# clients.py
import os
import requests
from dotenv import load_dotenv
from groq import Groq
from anthropic import Anthropic

# load .env
load_dotenv()

# API clients
GROQ      = Groq(api_key=os.getenv("GROQ_API_KEY"))
ANTHROPIC = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
CURSOR_KEY   = os.getenv("CURSOR_API_KEY")
TAKASHI_KEY  = os.getenv("TAKASHI_API_KEY")

def call_groq(messages, **kwargs) -> str:
    resp = GROQ.chat.completions.create(messages=messages, **kwargs)
    return resp.choices[0].message.content

def call_anthropic(prompt: str, **kwargs) -> str:
    resp = ANTHROPIC.completions.create(prompt=prompt, **kwargs)
    return resp["completion"]

def call_cursor(query: str, **kwargs) -> str:
    resp = requests.post(
        "https://api.cursor.so/v1/chat",
        json={"query": query},
        headers={"Authorization": f"Bearer {CURSOR_KEY}"},
        **kwargs
    )
    return resp.json().get("answer", "")

def call_takashi(query: str, **kwargs) -> str:
    resp = requests.post(
        "https://api.takashi.example.com/ask",
        json={"q": query},
        headers={"Authorization": f"Bearer {TAKASHI_KEY}"},
        **kwargs
    )
    return resp.json().get("reply", "")
