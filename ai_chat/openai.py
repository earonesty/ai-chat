import logging as log
import os

import openai

from ai_chat.chat import Chat
from ai_chat.types import AIFunctions
from ai_chat import Function


class OpenaiChat(Chat):
    def chat_complete(self, prompt, functions: AIFunctions) -> tuple[str, str, Function | None]:
        openai.api_key = os.getenv("OPENAI_API_KEY")

        args = dict(
            messages=prompt,
            **self.ai.model_params,
            n=1,
        )

        if functions:
            args['functions'] = functions.openai_dict()

        try:
            result = openai.ChatCompletion.create(**args)
        except Exception:
            # log the full args on error
            log.exception("openai error: %s", args)
            raise

        # log.debug("prompt: %s", prompt)
        log.debug("chat complete: %s", result)

        role = "assistant"
        message = result.choices[0].message
        content = message.content

        func = None
        if getattr(message, "function_call", None):
            function = message.function_call
            role = "function_call"
            func = Function(name=function.pop('name'), arguments=function.pop('arguments'), **function)

        return role, content, func
