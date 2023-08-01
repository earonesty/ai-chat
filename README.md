# simple chat context manager

- override everything
- works with any model
- works with any prompt recovery system (simple history, embedding search, whatever)
- chains functions well
- uses ai-functions and executes them

# example:


```python
from ai_chat import AiConfig
from ai_chat.openai import OpenaiChat
from ai_chat.store import SupabaseStore

store = SupabaseStore()
conf = AiConfig(id="persona-id-1", system="You are a silly friend.")
session = OpenaiChat(store, conf, "session-1")

session.functions = AIFunctions([search_google, get_calendar, add_calendar])

print(session.chat("hello").content)

# this contains the hello, and the reply in the context
print(session.chat("cool").content)
```
