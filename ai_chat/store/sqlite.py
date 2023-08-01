import sqlite3
import time
from typing import TYPE_CHECKING

from ai_chat.util import uuid

if TYPE_CHECKING:
    from ai_chat.chat import Chat

from ai_chat.types import Message
from ai_chat.store.base import Store


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
        """
        self.conn.executescript(create_table_query)
        self.conn.commit()

    def get_messages(self, chat: "Chat", content: str) -> list[Message]:
        """Must return oldest to newest."""
        query = """
            SELECT * FROM messages
            WHERE thread_id = ? AND ai_id = ?
            ORDER BY created_at DESC
            LIMIT 20;
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
        params = (uuid(), message.role, message.content, message.thread_id, chat.ai.id, time.time())
        self.conn.execute(query, params)
        self.conn.commit()


class MemoryStore(SqliteStore):
    def __init__(self):
        super().__init__(":memory:")