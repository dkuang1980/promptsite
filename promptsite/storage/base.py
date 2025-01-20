from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class StorageBackend(ABC):
    """Abstract base class defining the storage backend interface.

    This class defines the required interface that all storage implementations
    must provide. It handles the persistence of prompts, versions, and runs.

    Implementations should handle the details of storing and retrieving data
    in their specific storage medium (e.g., file system, git, database).
    """

    @abstractmethod
    def list_prompts(self) -> List[str]:
        """
        Get a list of all prompt IDs.
        Returns:
            List[str]: List of prompt IDs
        """
        pass

    @abstractmethod
    def create_prompt(self, prompt_id: str, prompt_data: Dict) -> None:
        """
        Create a new prompt in storage.
        Args:
            prompt_id: str - Unique identifier for the prompt
            prompt_data: Dict - Raw prompt data containing description, tags, etc.
        """
        pass

    @abstractmethod
    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """
        Retrieve raw prompt data by ID.
        Returns:
            Optional[Dict]: Raw prompt data if found, None otherwise
        """
        pass

    @abstractmethod
    def update_prompt(self, prompt_id: str, prompt_data: Dict) -> None:
        """
        Update prompt data.
        Args:
            prompt_id: str - Prompt identifier
            prompt_data: Dict - Updated prompt data
        """
        pass

    @abstractmethod
    def delete_prompt(self, prompt_id: str) -> None:
        """
        Delete a prompt and all its versions.
        """
        pass

    @abstractmethod
    def add_version(self, prompt_id: str, version_data: Dict) -> None:
        """
        Add a new version data to a prompt.
        Args:
            prompt_id: str - Prompt identifier
            version_data: Dict - Raw version data
        """
        pass

    @abstractmethod
    def get_version(self, prompt_id: str, version_id: str) -> Optional[Dict]:
        """
        Get raw version data.
        Returns:
            Optional[Dict]: Version data if found, None otherwise
        """
        pass

    @abstractmethod
    def list_versions(self, prompt_id: str) -> List[Dict]:
        """
        Get all version data for a prompt.
        Returns:
            List[Dict]: List of version data dictionaries
        """
        pass

    @abstractmethod
    def add_run(self, prompt_id: str, version_id: str, run_data: Dict) -> None:
        """
        Add a new run to a version.
        Args:
            prompt_id: str - Prompt identifier
            version_id: str - Version identifier
            run_data: Dict - Raw run data
        """
        pass
