import dataclasses

from ai_chat.defaults import DEFAULT_CHAT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_ERROR_PREFIX

from ai_functions import AIFunctions


class AiConfig:
    """Persona and configuration"""
    id: str
    system: str
    error_prefix: str

    def __init__(self, *, id, system, error_prefix=DEFAULT_ERROR_PREFIX, functions: AIFunctions = None,
                 model_params=None, **data):
        self.__dict__ = data
        self.id = id
        self.system = system
        self.error_prefix = error_prefix
        self.functions = functions
        self.model_params = {
            **dict(model=DEFAULT_CHAT_MODEL, temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS),
            **(model_params or {})}


class Message:
    id: str
    role: str
    content: str
    thread_id: str

    def __init__(self, *, id, role, content, thread_id, **data):
        self.__dict__ = data
        self.id = id
        self.role = role
        self.content = content
        self.thread_id = thread_id


class Function:
    name: str
    arguments: str

    def __init__(self, *, name, arguments, **data):
        self.__dict__ = data
        self.name = name
        self.arguments = arguments


@dataclasses.dataclass
class ChatResponse:
    request_id: str
    response_id: str
    content: str
