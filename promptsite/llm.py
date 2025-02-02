from typing import Any, Dict, Optional

from .exceptions import ConfigError


class LLM:
    """
    Base class for LLM backends.
    To add a new LLM backend, you need to implement the `run` method.
    
    Args:
        config: A dictionary of configuration for the LLM backend.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        if "model" not in self.config:
            raise ConfigError("LLM model is not set in config")

    def run(self, prompt: str, **kwargs):
        """
        Run the LLM with the given prompt.

        Args:
            prompt: The prompt to run the LLM with.
        """
        raise NotImplementedError("run method not implemented")


class OpenAI(LLM):
    """
    LLM backend for OpenAI.

    Args:
        config: A dictionary of configuration for the OpenAI backend.
        For example, {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 100
        }
    """
    def __init__(self, config: Dict[str, Any]):
        import openai

        self.client = openai.OpenAI()
        super().__init__(config)

    def run(self, user_prompt: str, system_prompt: Optional[str] = None, **kwargs):
        """
        Run the LLM with the given prompt.

        Args:
            user_prompt: The prompt to run the LLM with.
            system_prompt: The system prompt to run the LLM with.
        """
        messages = [
            {"role": "user", "content": user_prompt},
        ]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        response = self.client.chat.completions.create(messages=messages, **self.config)
        return response.choices[0].message.content


class Ollama(LLM):
    """
    LLM backend for Ollama.

    Args:
        config: A dictionary of configuration for the Ollama backend.
    """
    def run(self, user_prompt: str, system_prompt: Optional[str] = None, **kwargs):
        """
        Run the LLM with the given prompt.

        Args:
            user_prompt: The prompt to run the LLM with.
            system_prompt: The system prompt to run the LLM with.
        """
        from ollama import chat

        messages = [
            {"role": "user", "content": user_prompt},
        ]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        response = chat(messages=messages, **self.config)
        return response.message.content


class Anthropic(LLM):
    """
    LLM backend for Anthropic.

    Args:
        config: A dictionary of configuration for the Anthropic backend.
    """
    def __init__(self, config: Dict[str, Any]):
        import anthropic

        self.client = anthropic.Anthropic()
        super().__init__(config)

    def run(self, user_prompt: str, system_prompt: Optional[str] = None, **kwargs):
        """
        Run the LLM with the given prompt.

        Args:
            user_prompt: The prompt to run the LLM with.
            system_prompt: The system prompt to run the LLM with.
        """
        message = self.client.messages.create(
            messages=[
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
            ],
            **self.config,
            **({} if system_prompt is None else {"system": system_prompt}),
        )

        return message.content
