import logging as log

import openai

from ai_chat.chat import Chat
from ai_chat.types import AIFunctions
from ai_chat import Function


class OpenaiChat(Chat):
    def chat_complete(self, prompt, functions: AIFunctions) -> tuple[str, str, Function | None]:
        args = dict(
            messages=prompt,
            **self.ai.model_params,
            n=1,
        )

        if functions:
            args['functions'] = functions.get_openai()

        result = openai.ChatCompletion.create(**args)

        log.info("chat complete: %s", result)

        role = "assistant"
        message = result.choices[0].message
        content = message.content

        func = None
        if content is None:
            function = message.function_call
            role = "function_call"
            func = Function(name=function.pop('name'), arguments=function.pop('arguments'), **function)

        return role, content, func
