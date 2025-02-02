import os
from pathlib import Path
from typing import Any, Dict

import yaml

from .exceptions import LLMBackendNotImplementedError, StorageBackendNotFoundError
from .llm import LLM, AnthropicLLM, OllamaLLM, OpenAiLLM
from .storage import StorageBackend
from .storage.file import FileStorage
from .storage.git import GitStorage


class Config:
    """Configuration manager for PromptFlow settings and storage backend.

    Attributes:
        BASE_DIRECTORY (str): The base directory for PromptFlow configuration files
    """

    BASE_DIRECTORY: str = ".promptsite"

    def __init__(self, config: Dict[str, Any] = None) -> None:
        """
        Initialize Config with a configuration file path.

        Args:
            config_file: Path to the configuration file
        """

        self.config_file: str = os.path.join(self.BASE_DIRECTORY, "config.yaml")
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        if config:
            self.save_config(config)
        else:
            self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        self.config = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}

        self.config.setdefault("storage_backend", "file")
        self.config.setdefault("llm_backend", "openai")
        self.config.setdefault("llm_config", {})
        return self.config

    def save_config(self, config: Dict[str, Any] = None) -> None:
        """Save current configuration to file with default values."""
        config = config or {}
        config.setdefault("storage_backend", "file")
        config.setdefault("llm_backend", "openai")
        config.setdefault("llm_config", {})

        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, indent=4)

        self.config = config

    def get_llm_backend(self) -> LLM:
        """
        Get configured LLM backend instance.
        """
        backend_type: str = self.config["llm_backend"]
        if backend_type == "openai":
            return OpenAiLLM(self.config["llm_config"])
        elif backend_type == "anthropic":
            return AnthropicLLM(self.config["llm_config"])
        elif backend_type == "ollama":
            return OllamaLLM(self.config["llm_config"])
        else:
            raise LLMBackendNotImplementedError(
                f"LLM backend '{backend_type}' not implemented"
            )

    def get_storage_backend(self) -> StorageBackend:
        """
        Get configured storage backend instance.

        Returns:
            StorageBackend: Configured storage backend instance

        Raises:
            StorageBackendNotFoundError: If specified backend type is not supported
        """

        backend_type: str = self.config["storage_backend"]

        if backend_type == "file":
            return FileStorage(base_path=self.BASE_DIRECTORY)
        elif backend_type == "git":
            branch: str = self.config.get("branch", "main")
            remote: str = self.config.get("remote")
            auto_sync: bool = self.config.get("auto_sync", False)
            return GitStorage(
                base_path=Path(self.BASE_DIRECTORY),
                branch=branch,
                remote=remote,
                auto_sync=auto_sync,
            )

        raise StorageBackendNotFoundError(f"Storage backend '{backend_type}' not found")
