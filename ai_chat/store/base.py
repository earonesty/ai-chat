from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_chat.chat import Chat

from ai_chat.types import Message


class Store:
    def get_messages(self, chat: "Chat", content: str) -> list[Message]:
        ...

    def add_message(self, message: "Message", chat: "Chat"):
        ...
