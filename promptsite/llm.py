from typing import Dict, Any, Optional

class LLM:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        if "model" not in self.config:
            raise LlmConfigError("model is not set in config")

    def run(self, prompt: str, **kwargs):
        raise NotImplementedError("run method not implemented")


class OpenAI(LLM):
    def __init__(self, config: Dict[str, Any]):
        import openai
        self.client = openai.OpenAI()
        super().__init__(config)

    def run(self, user_prompt: str, system_prompt: Optional[str] = None, **kwargs):
        messages = [
            {"role": "user", "content": user_prompt},
        ]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        response = self.client.chat.completions.create(
            messages=messages,
            **self.config
        )
        return response.choices[0].message.content


class Ollama(LLM):
    def run(self, user_prompt: str, system_prompt: Optional[str] = None, **kwargs):
        from ollama import chat
        messages = [
            {"role": "user", "content": user_prompt},
        ]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        response = chat(
            messages=messages,
            **self.config
        )
        return response.message.content


class Anthropic(LLM):
    def __init__(self, config: Dict[str, Any]):
        import anthropic
        self.client = anthropic.Anthropic()
        super().__init__(config)

    def run(self, user_prompt: str, system_prompt: Optional[str] = None, **kwargs):
        message = self.client.messages.create(   
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            **self.config,
            **({} if system_prompt is None else {"system": system_prompt})
        )

        return message.content