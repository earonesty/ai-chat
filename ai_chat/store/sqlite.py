import json
import sqlite3
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_chat.chat import Chat

from ai_chat.types import Message
from ai_chat.store.base import Store, State


class SqliteStore(Store):
    """Sqlite message storage"""

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        # Create the 'messages' table if it doesn't exist
        create_table_query = """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                role TEXT,
                content TEXT,
                thread_id TEXT,
                ai_id TEXT,
                created_at REAL
            );
            
            create index if not exists ix_messages_ai_id on messages(ai_id);
            create index if not exists ix_messages_thread_id on messages(thread_id);
            create index if not exists ix_messages_created_at on messages(created_at);

            CREATE TABLE IF NOT EXISTS state (
                ai_id TEXT,
                key TEXT,
                content TEXT,
                created_at REAL,
                primary key (ai_id, key)
            );
 
        """
        self.conn.executescript(create_table_query)
        self.conn.commit()

    def get_messages(self, chat: "Chat", content: str, limit=20) -> list[Message]:
        """Must return oldest to newest."""
        query = f"""
            SELECT * FROM messages
            WHERE thread_id = ? AND ai_id = ?
            ORDER BY created_at DESC
            LIMIT {limit};
        """
        params = (chat.thread_id, chat.ai.id)
        rows = self.conn.execute(query, params).fetchall()
        return [Message(**dict(row)) for row in sorted(rows, key=lambda row: row['created_at'])]

    def add_message(self, message: "Message", chat: "Chat"):
        """Add chat to db, must guarantee sort order somehow."""
        query = """
            INSERT INTO messages (id, role, content, thread_id, ai_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        params = (message.id, message.role, message.content, message.thread_id, chat.ai.id, time.time())
        self.conn.execute(query, params)
        self.conn.commit()

    def set_state(self, chat: "Chat", key: str, state: "State"):
        """Add state to db, this is generally 'across chats'."""
        query = """
            INSERT OR REPLACE INTO state (key, content, ai_id, created_at)
            VALUES (?, ?, ?, ?);
        """
        params = (key, json.dumps(state), chat.ai.id, time.time())
        self.conn.execute(query, params)
        self.conn.commit()

    def get_state(self, chat: "Chat", key: str) -> State | None:
        """Add state to db, this is generally 'across chats'."""
        query = """
            SELECT content from  state
             WHERE key = ? and ai_id = ?
        """
        params = (key, chat.ai.id)
        rows = self.conn.execute(query, params).fetchall()
        if rows:
            return json.loads(rows[0]['content'])
        return None

    def enum_state(self, chat: "Chat", prefix: str) -> list[tuple[str, State]]:
        """Add state to db, this is generally 'across chats'."""
        query = """
            SELECT content from  state
             WHERE key like ? and ai_id = ?
        """
        params = (prefix + "%", chat.ai.id)
        rows = self.conn.execute(query, params).fetchall()
        if rows:
            return [(row['key'], json.loads(row['content'])) for row in rows]
        return []

    def set_glob(self, key: str, state: "State"):
        """Add state to db, this is generally 'across chats'."""
        query = """
            INSERT OR REPLACE INTO state (key, content, ai_id, created_at)
            VALUES (?, ?, ?, ?);
        """
        params = (key, json.dumps(state), "<glob>", time.time())
        self.conn.execute(query, params)
        self.conn.commit()

    def get_glob(self, key: str) -> State | None:
        """Add state to db, this is generally 'across chats'."""
        query = """
            SELECT content from  state
             WHERE key = ? and ai_id = ?
        """
        params = (key, "<glob>")
        rows = self.conn.execute(query, params).fetchall()
        if rows:
            return json.loads(rows[0]['content'])
        return None

    def enum_glob(self, prefix: str) -> list[tuple[str, State]]:
        """Add state to db, this is generally 'across chats'."""
        query = """
            SELECT content from  state
             WHERE key like ? and ai_id = ?
        """
        params = (prefix + "%", "<glob>")
        rows = self.conn.execute(query, params).fetchall()
        if rows:
            return [(row['key'], json.loads(row['content'])) for row in rows]
        return []


class MemoryStore(SqliteStore):
    def __init__(self):
        super().__init__(":memory:")
