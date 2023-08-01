import os
from typing import TYPE_CHECKING

from supabase import Client

from ai_chat.util import uuid

if TYPE_CHECKING:
    from ai_chat.chat import Chat

from ai_chat.types import Message
from ai_chat.store.base import Store


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
    """

    def __init__(self, conn: Client | None = None):
        if conn is None:
            url: str = os.environ["SUPABASE_URL"]
            key: str = os.environ["SUPABASE_KEY"]
            conn = Client(url, key)
        self.conn = conn

    def get_messages(self, chat: "Chat", content: str):
        """Must return oldest to newest."""

        return [Message(**ent) for ent in sorted(self.conn.table('messages').select(
            '*').eq('thread_id', chat.thread_id).eq('ai_id', chat.ai.id).order(
            'created_at.desc').limit(20).execute().data, key=lambda row: row['created_at'])]

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
