import json
import os
from typing import TYPE_CHECKING

from supabase import Client

if TYPE_CHECKING:
    from ai_chat.chat import Chat

from ai_chat.types import Message
from ai_chat.store.base import Store, State


class SupabaseStore(Store):
    """Supabase message storage

    CREATE TABLE messages (
        id text primary key,
        created_at timestamp with time zone default now(),
        ai_id text not null,
        thread_id text not null,
        role text not null,
        content text not null,
        );

    create index ix_messages_ai_id on messages(ai_id);
    create index ix_messages_thread_id on messages(thread_id);
    create index ix_messages_created_at on messages(created_at);

    CREATE TABLE state (
        ai_id text not null,
        key text,
        content text not null,
        created_at timestamp with time zone default now(),
        primary key (ai_id, key)
        );
    """

    def __init__(self, conn: Client | None = None):
        if conn is None:
            url: str = os.environ["SUPABASE_URL"]
            key: str = os.environ["SUPABASE_KEY"]
            conn = Client(url, key)
        self.conn = conn

    def get_messages(self, chat: "Chat", content: str, limit=20):
        """Must return oldest to newest."""

        return [Message(**ent) for ent in sorted(self.conn.table('messages').select(
            '*').eq('thread_id', chat.thread_id).eq('ai_id', chat.ai.id).order(
            'created_at.desc').limit(limit).execute().data, key=lambda row: row['created_at'])]

    def add_message(self, message: "Message", chat: "Chat"):
        """Add chat to db, must guarantee sort order somehow."""

        assert message.ai_id == chat.ai.id
        assert message.thread_id == chat.thread_id

        data = dict(
            id=message.id,
            role=message.role,
            content=message.content,
            thread_id=message.thread_id,
            ai_id=chat.ai.id
        )

        self.conn.table('messages').insert(data).execute()

    def set_state(self, chat: "Chat", key: str, state: State):
        data = dict(
            ai_id=chat.ai.id,
            key=key,
            content=json.dumps(state),
        )
        self.conn.table('state').upsert(data).execute()

    def get_state(self, chat: "Chat", key: str) -> State | None:
        res = self.conn.table('state').select('content').eq('ai_id', chat.ai.id).eq('key', key).execute()
        if res and res.data:
            return json.loads(res.data[0]['content'])

    def enum_state(self, chat: "Chat", prefix: str) -> list[tuple[str, State]]:
        res = self.conn.table('state').select('content').eq('ai_id', chat.ai.id).like('key', prefix + '%').execute()
        if res and res.data:
            return [(row['key'], json.loads(row['content'])) for row in res.data]

    def set_glob(self, key: str, state: State):
        data = dict(
            ai_id="<glob>",
            key=key,
            content=json.dumps(state),
        )
        self.conn.table('state').upsert(data).execute()

    def get_glob(self, key: str) -> State | None:
        res = self.conn.table('state').select('content').eq('ai_id', "<glob>").eq('key', key).execute()
        if res and res.data:
            return json.loads(res.data[0]['content'])

    def enum_glob(self, prefix: str) -> list[tuple[str, State]]:
        res = self.conn.table('state').select('key, content').eq('ai_id', "<glob>").like('key', prefix + '%').execute()
        if res and res.data:
            return [(row['key'], json.loads(row['content'])) for row in res.data]