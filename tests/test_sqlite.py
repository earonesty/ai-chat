import pytest
from dotenv import load_dotenv

from ai_chat import Message
from ai_chat.store import SqliteStore
from ai_chat.util import uuid
from tests.test_chat import chat_instance, memory_store, ai_config  # noqa

load_dotenv()

@pytest.fixture
def sqlite(tmp_path):
    test_id = uuid()
    store = SqliteStore(tmp_path / "db")
    yield store, test_id
    store.conn.close()


def test_sqlite_store(chat_instance, sqlite):
    store, ai_id = sqlite
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

    store.set_state(chat_instance, "name", "val")

    assert store.get_state(chat_instance, "name") == "val"