import pytest
from dotenv import load_dotenv

from ai_chat import Message
from ai_chat.store import SupabaseStore
from ai_chat.util import uuid
from tests.test_chat import chat_instance, memory_store, ai_config  # noqa

load_dotenv()

@pytest.fixture
def supabase():
    test_id = uuid()
    store = SupabaseStore()
    yield store, test_id
    store.conn.table("messages").delete().eq("ai_id", test_id).execute()


def test_supabase_store(chat_instance, supabase):
    store, ai_id = supabase
    chat_instance.ai.id = ai_id
    msg_id = uuid()
    chat_instance.thread_id = uuid()
    store.add_message(Message(
        id=msg_id,
        role="user",
        content="me",
        thread_id=chat_instance.thread_id,
        ai_id=ai_id
    ), chat=chat_instance)

    msgs = store.get_messages(chat_instance, "")
    assert len(msgs) == 1
    assert msgs[0].id == msg_id
    assert msgs[0].role == "user"
    assert msgs[0].content == "me"
    assert msgs[0].thread_id == chat_instance.thread_id
    assert msgs[0].ai_id == chat_instance.ai.id

