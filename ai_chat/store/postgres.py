import json
import os
from typing import TYPE_CHECKING
import psycopg2
from psycopg2.extras import DictCursor

if TYPE_CHECKING:
    from ai_chat.chat import Chat

from ai_chat.types import Message
from ai_chat.store.base import Store, State


class PostgresStore(Store):
    """PostgreSQL message storage"""

    def __init__(self, conn=None):
        if conn is None:
            postgres_url = os.environ["POSTGRES_URL"]
            conn = psycopg2.connect(postgres_url, cursor_factory=DictCursor)
        self.conn = conn


    def create(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS messages (
                id text primary key,
                created_at timestamp with time zone default now(),
                ai_id text not null,
                thread_id text not null,
                role text not null,
                content text not null
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_messages_ai_id ON messages(ai_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_messages_thread_id ON messages(thread_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages(created_at);
            """,
            """
            CREATE TABLE IF NOT EXISTS state (
                ai_id text not null,
                key text,
                content text not null,
                created_at timestamp with time zone default now(),
                primary key (ai_id, key)
            );
            """
        ]

        with self.conn.cursor() as cur:
            for query in queries:
                cur.execute(query)
            self.conn.commit()

    def get_messages(self, chat: "Chat", content: str, limit=20):
        query = """
            SELECT * FROM messages
            WHERE thread_id = %s AND ai_id = %s
            ORDER BY created_at ASC
            LIMIT %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (chat.thread_id, chat.ai.id, limit))
            rows = cur.fetchall()
        return [Message(**row) for row in rows]

    def add_message(self, message: "Message", chat: "Chat"):
        query = """
            INSERT INTO messages (id, created_at, role, content, thread_id, ai_id)
            VALUES (%s, NOW(), %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (message.id, message.role, message.content, chat.thread_id, chat.ai.id))
            self.conn.commit()

    def set_state(self, chat: "Chat", key: str, state: State):
        query = """
            INSERT INTO state (ai_id, key, content, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (ai_id, key)
            DO UPDATE SET content = EXCLUDED.content
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (chat.ai.id, key, json.dumps(state)))
            self.conn.commit()

    def get_state(self, chat: "Chat", key: str) -> State | None:
        query = """
            SELECT content FROM state
            WHERE ai_id = %s AND key = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (chat.ai.id, key))
            row = cur.fetchone()
        return json.loads(row['content']) if row else None

    def enum_state(self, chat: "Chat", prefix: str) -> list[tuple[str, State]]:
        query = """
            SELECT key, content FROM state
            WHERE ai_id = %s AND key LIKE %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (chat.ai.id, prefix + '%'))
            rows = cur.fetchall()
        return [(row['key'], json.loads(row['content'])) for row in rows]

    def set_glob(self, key: str, state: State):
        self.set_state("<glob>", key, state)

    def get_glob(self, key: str) -> State | None:
        return self.get_state("<glob>", key)

    def enum_glob(self, prefix: str) -> list[tuple[str, State]]:
        return self.enum_state("<glob>", prefix)
