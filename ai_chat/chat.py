import json
import logging as log
from abc import ABC, abstractmethod

from ai_chat.types import Message, Function, ChatResponse, AiConfig, AIFunctions
from ai_chat.store.base import Store
from ai_chat.util import uuid


class Chat(ABC):
    def __init__(self, *, ai: "AiConfig", thread_id: str | None = None, store: Store | None = None):
        """Thread of conversation"""
        self.ai = ai
        self.functions = self.ai.functions
        self.thread_id = thread_id
        self.store = store

    def function_kws(self):
        """Override this to provide other kwargs to functions"""
        return {"chat": self}

    def recent_messages(self, content: str):
        return self.store.get_messages(self, content)

    def get_system(self):
        """Override this if you want the current state to be considered in the system prompt."""
        return self.ai.system

    def chat(self, content, history: list["Message"] | None = None, save=True) -> ChatResponse:
        """Continue a conversation"""

        # this can include embeddings/search if you want, so that's why the content is there
        last_messages = history or self.recent_messages(content)

        prompt = [
            {
                "role": "system",
                "content": self.get_system()
            }
        ]

        if not last_messages:
            if self.ai.seed_chat:
                for user, assistant in self.ai.seed_chat:
                    prompt.append(
                        {
                            "role": "user",
                            "content": user,
                        }
                    )
                    prompt.append(
                        {
                            "role": "assistant",
                            "content": assistant,
                        }
                    )

        for msg in last_messages:
            info = self.get_prompt(msg.role, msg.content)
            prompt.append(info)

        return self.chat_as(content, "user", prompt, save=save)

    @staticmethod
    def get_prompt(role, content):
        prompt = {
            'role': role,
            'content': content,
        }

        if role.startswith("function:"):
            split_role = role.split(":", 1)
            prompt['role'] = split_role[0]
            prompt['name'] = split_role[1]

        if role == "function_call":
            prompt['role'] = 'assistant'
            prompt['content'] = None
            prompt['function_call'] = json.loads(content)

        return prompt

    def execute_function(self, function: Function):
        function_name = function.name
        functions = self.ai_functions()
        try:
            if not functions:
                raise ValueError(f"Function {function_name} is not available.")
            return functions.execute(function.name, function.arguments, **self.function_kws())
        except Exception as e:
            log.exception("Got an error while running function")
            return f"{self.ai.error_prefix} '{repr(e)}' while running '{function_name}'"

    def chat_as(self, content, in_role, prompt, save=True) -> ChatResponse:
        # add content and role to the prompt
        prompt.append(self.get_prompt(in_role, content))

        functions = self.get_functions()

        out_role, reply, function = self.chat_complete(prompt, functions)

        if function:
            function_result = self.execute_function(function)

            if save:
                # structure as the db would and save
                self.save_interaction(in_role, content, out_role, function)

            # continue chat with the functional reply, don't return until you get an assistant reply
            return self.chat_as(function_result, 'function:' + function.name, prompt)

        if save:
            request_id, response_id = self.save_interaction(in_role, content, out_role, reply)
        else:
            request_id, response_id = None, None

        return ChatResponse(
            request_id=request_id,
            response_id=response_id,
            content=reply
        )

    def ai_functions(self) -> AIFunctions:
        """Override to vary functions based on state."""
        return self.functions

    def get_functions(self):
        """Override to implement your own function lib, and not use ai-functions.

        You will also need to override execute_function.
        """
        return self.ai_functions() and self.ai_functions()

    def add_message(self, role: str, content: str | Function):
        if isinstance(content, Function):
            role = "function:" + content.name
            content = content.arguments
        user_chat = self.structure_reply(content, role)
        if self.store:
            self.store.add_message(user_chat, self)
        return user_chat.id

    def save_interaction(self, in_role: str, content: str, out_role: str, reply: str | Function):
        is_error = in_role == "function_all" and reply.startswith(self.ai.error_prefix)

        if not is_error:
            user_id = self.add_message(in_role, content)
            assistant_id = self.add_message(out_role, reply)
            return user_id, assistant_id
        return None, None

    def structure_reply(self, reply: str, role: str):
        """Make a new message from a reply."""
        return Message(
            id=uuid(),
            thread_id=self.thread_id,
            ai_id=self.ai.id,
            role=role,
            content=reply,
        )

    @abstractmethod
    def chat_complete(self, prompt, functions) -> tuple[str, str, Function | None]:
        """Override for your favorite chat model"""
