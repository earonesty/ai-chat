from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ai_chat.chat import Chat

from ai_chat.types import Message


State = str | dict[str, "State"] | int


class Store(ABC):
    @abstractmethod
    def get_messages(self, chat: "Chat", content: str, limit: int = 20) -> list[Message]:
        ...

    @abstractmethod
    def add_message(self, message: "Message", chat: "Chat"):
        ...

    @abstractmethod
    def get_state(self, chat: "Chat", key: str) -> State | None:
        ...

    @abstractmethod
    def set_state(self, chat: "Chat", key: str, state: State):
        ...

    @abstractmethod
    def enum_state(self, chat: "Chat", prefix: str) -> list[tuple[str, State]]:
        ...

    @abstractmethod
    def set_glob(self, key: str, state: State):
        ...

    @abstractmethod
    def get_glob(self, key: str) -> State:
        ...

    @abstractmethod
    def enum_glob(self, key: str) -> list[tuple[str, State]]:
        ...
