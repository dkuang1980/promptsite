import os
from pathlib import Path
from typing import Any, Dict

import yaml

from .exceptions import ConfigFileNotFoundError, StorageBackendNotFoundError
from .storage import StorageBackend
from .storage.file import FileStorage
from .storage.git import GitStorage


class Config:
    """Configuration manager for PromptFlow settings and storage backend.

    Attributes:
        BASE_DIRECTORY (str): The base directory for PromptFlow configuration files
    """

    BASE_DIRECTORY: str = ".promptsite"

    def __init__(self) -> None:
        """
        Initialize Config with a configuration file path.

        Args:
            config_file: Path to the configuration file
        """

        self.config_file: str = os.path.join(self.BASE_DIRECTORY, "config.yaml")
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        self.config = {}

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        if not os.path.exists(self.config_file):
            raise ConfigFileNotFoundError("Config file not found")

        with open(self.config_file, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f) or {}
            return self.config

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save current configuration to file with default values."""
        # Set default values if not present
        if config is None:
            config = {}

        config.setdefault("storage_backend", "file")

        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, indent=4)

        self.config = config

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
