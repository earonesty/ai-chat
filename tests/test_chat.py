import json
from typing import Annotated

import pytest
from ai_chat import AiConfig, Chat, Function, ChatResponse, Message
from ai_chat.store import MemoryStore
from ai_chat.types import AIFunctions


class MockChat(Chat):
    def chat_complete(self, prompt, functions) -> tuple[str, str, Function | None]:
        return "assistant", "hi, im a reply", None


@pytest.fixture
def memory_store():
    return MemoryStore()


@pytest.fixture
def ai_config():
    return AiConfig(id="ai_1", system="My AI System")


@pytest.fixture
def chat_instance(memory_store, ai_config):
    thread_id = "thread_1"
    return MockChat(store=memory_store, ai=ai_config, thread_id=thread_id)


def test_chat_response():
    response = ChatResponse(request_id="123", response_id="456", content="Hello, World!")
    assert response.request_id == "123"
    assert response.response_id == "456"
    assert response.content == "Hello, World!"


def test_message_creation():
    message = Message(id="msg_1", role="user", content="Hello, AI", thread_id="thread_1")
    assert message.id == "msg_1"
    assert message.role == "user"
    assert message.content == "Hello, AI"
    assert message.thread_id == "thread_1"


def test_function_creation():
    function = Function(name="func1", arguments="arg1")
    assert function.name == "func1"
    assert function.arguments == "arg1"


def test_ai_config_creation(ai_config):
    assert ai_config.id == "ai_1"
    assert ai_config.system == "My AI System"
    assert ai_config.error_prefix == "Got an error:"
    assert ai_config.model_params == {
        "model": "gpt-3.5-turbo-16k",
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    assert ai_config.functions is None


def test_chat_instance_creation(chat_instance, ai_config):
    assert chat_instance.ai == ai_config
    assert chat_instance.thread_id == "thread_1"
    assert isinstance(chat_instance.store, MemoryStore)


def test_chat_response_default_parameters(chat_instance):
    chat_response = chat_instance.chat("Hello, AI!")
    assert chat_response.request_id is not None
    assert chat_response.response_id is not None
    assert chat_response.content is not None


def test_add_message(chat_instance):
    user_id = chat_instance.add_message("user", "Hello, AI!")
    assert user_id is not None
    assistant_id = chat_instance.add_message("assistant", "Hi, User!")
    assert assistant_id is not None


def test_save_interaction(chat_instance):
    user_id, assistant_id = chat_instance.save_interaction("user", "Hello, AI!", "assistant", "Hi, User!")
    assert user_id is not None
    assert assistant_id is not None


def test_structure_reply(chat_instance):
    reply = chat_instance.structure_reply("Hi, User!", "assistant")
    assert isinstance(reply, Message)
    assert reply.id is not None
    assert reply.thread_id == "thread_1"
    assert reply.ai_id == "ai_1"
    assert reply.role == "assistant"
    assert reply.content == "Hi, User!"


def test_get_prompt(chat_instance):
    prompt = chat_instance.get_prompt("user", "Hello, AI!")
    assert prompt == {"role": "user", "content": "Hello, AI!"}

    prompt = chat_instance.get_prompt("function:func1", "Hello, AI!")
    assert prompt == {"role": "function", "name": "func1", "content": "Hello, AI!"}

    prompt = chat_instance.get_prompt("function_call", '{"name": "func1", "arguments": "arg1"}')
    assert prompt == {
        "role": "assistant",
        "content": None,
        "function_call": {"name": "func1", "arguments": "arg1"},
    }


def test_execute_function(chat_instance):
    function = Function(name="func1", arguments="arg1")
    chat_instance.ai_functions = lambda: None  # Mock ai_functions to return None
    result = chat_instance.execute_function(function)
    assert result.startswith(chat_instance.ai.error_prefix)


def test_execute_function_works(chat_instance):
    funcs = AIFunctions()

    did_something = None

    def my_func(arg: Annotated[str, "arg 1"], chat, **kws):
        """Some func that does something"""
        nonlocal did_something
        did_something = arg
        return "ok"

    funcs.add(my_func)

    chat_instance.functions = funcs
    function = Function(name="my_func", arguments=json.dumps(dict(arg="yo")))
    result = chat_instance.execute_function(function)
    assert not result.startswith(chat_instance.ai.error_prefix)
    assert did_something

def test_function_state_chaining(chat_instance):
    funcs = AIFunctions()

    def my_func(arg: Annotated[str, "arg 1"], chat, **kws):
        """Some func that does something"""
        def tmp_func(**_kws):
            """Another func that gets created because the first was called."""
            return "tmp"

        chat.functions.add(tmp_func)

        return "ok"

    funcs.add(my_func)

    chat_instance.functions = funcs
    function = Function(name="my_func", arguments=json.dumps(dict(arg="yo")))
    result = chat_instance.execute_function(function)
    assert result == "ok"
    assert len(chat_instance.ai_functions().map) == 2

    function = Function(name="tmp_func", arguments=json.dumps(dict()))
    result = chat_instance.execute_function(function)
    assert result == "tmp"

def test_chat_as(chat_instance):
    chat_response = chat_instance.chat_as("Hello, AI!", "user", [])
    assert chat_response.request_id is not None
    assert chat_response.response_id is not None
    assert chat_response.content is not None


def test_chat_complete(chat_instance):
    # Override the abstract method chat_complete for testing purposes
    chat_instance.chat_complete = lambda prompt, functions: ("assistant", "hello", "")

    res = chat_instance.chat_as("Hello, AI!", "user", [])
    assert res.content == "hello"
    assert res.request_id
    assert res.response_id

    msgs = chat_instance.store.get_messages(chat_instance, "")
    assert len(msgs) == 2

    assert msgs[0].role == "user"
    assert msgs[1].role == "assistant"
