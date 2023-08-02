# simple chat context manager

- override everything
- works with any model
- works with any prompt recovery system (simple history, embedding search, whatever)
- chains functions well
- uses ai-functions and executes them

## install

poetry add or pip install this repo, for now

## example:


```python
from ai_chat import AiConfig

# only supports openai for now, todo: add other models
from ai_chat.openai import OpenaiChat
from ai_chat.store import SupabaseStore
from ai_functions import AIFunctions

# supports SqliteStore() as well as MemoryStore() for storing the chain of prompts

store = SupabaseStore()
conf = AiConfig(id="persona-id-1", system="You are a silly friend.")
session = OpenaiChat(store=store, ai=conf, thread_id="session-1")

def search_google():
    ...

def get_calendar():
    ...

def add_calendar():
    ...

session.functions = AIFunctions([search_google, get_calendar, add_calendar])

print(session.chat("hello").content)

# this contains the hello, and the reply in the context
print(session.chat("cool").content)
```
