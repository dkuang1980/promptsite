try:
    from datetime import UTC
except ImportError:
    from datetime import timezone as _timezone

    UTC = _timezone.utc
from typing import Any, Dict, List, Optional

from .config import Config
from .exceptions import (
    InvalidPromptContentError,
    PromptAlreadyExistsError,
    PromptNotFoundError,
    RunNotFoundError,
    StorageError,
    VersionNotFoundError,
)
from .model.prompt import Prompt
from .model.run import Run
from .model.variable import Variable
from .model.version import Version
from .storage import StorageBackend
from .storage.file import FileStorage


class PromptSite:
    """Main class for managing prompts and their versions.

    The PromptSite class provides a high-level interface for managing prompts, versions,
    and execution runs. It handles all operations through a configured storage backend
    and provides methods for prompt registration, version control, and run tracking.

    Attributes:
        storage (StorageBackend): Backend storage implementation for persisting data

    Example:
        >>> ps = PromptSite(storage_backend)
        >>> prompt = ps.register_prompt("my-prompt", "Initial content")
        >>> version = ps.add_prompt_version("my-prompt", "Updated content")
    """

    def __init__(self, storage: Optional[StorageBackend] = None):
        """Initialize promptsite.

        Args:
            storage (Storage): Storage backend instance.
        """
        if storage is None:
            self.storage = FileStorage(Config.BASE_DIRECTORY)
        else:
            self.storage = storage

    def register_prompt(
        self,
        prompt_id: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        initial_content: Optional[str] = None,
        variables: Optional[Dict[str, Variable]] = None,
    ) -> Prompt:
        """Register a new prompt with the system.

        Creates a new prompt entry with optional file association and initial content.
        The prompt can be created either from direct content or from a file.

        Args:
            prompt_id: Unique identifier for the prompt
            description: Optional description of the prompt's purpose
            tags: Optional list of tags for categorization
            initial_content: Optional initial content
            variables: Optional variables for the prompt
        Returns:
            Prompt: The newly created prompt object

        Raises:
            PromptAlreadyExistsError: If prompt_id already exists
        """
        if self.storage.get_prompt(prompt_id):
            raise PromptAlreadyExistsError(f"Prompt '{prompt_id}' already exists.")

        prompt = Prompt(
            id=prompt_id, description=description, tags=tags or [], variables=variables
        )

        if initial_content:
            prompt.add_version(initial_content, variables)

        self.storage.create_prompt(prompt_id, prompt.to_dict())
        return prompt

    def add_prompt_version(
        self, prompt_id: str, new_content: Optional[str] = None
    ) -> Version:
        """Add a new version to an existing prompt.

        Creates a new version of the prompt with updated content. If the prompt has an
        associated file, the content can be read from the file instead of being provided directly.

        Args:
            prompt_id: ID of the prompt to version
            new_content: Optional new content for the version

        Returns:
            Version: The newly created version object

        Raises:
            PromptNotFoundError: If prompt_id doesn't exist
            InvalidPromptContentError: If no content is provided
        """
        prompt_data = self.storage.get_prompt(prompt_id)
        if not prompt_data:
            raise PromptNotFoundError(f"Prompt '{prompt_id}' not found.")

        prompt = Prompt.from_dict(prompt_data)

        if not new_content:
            raise InvalidPromptContentError(
                "New content must be provided for the update."
            )

        new_version = prompt.add_version(new_content)
        self.storage.update_prompt(prompt_id, prompt.to_dict())
        return new_version

    def get_prompt(self, prompt_id: str) -> Prompt:
        """
        Get a prompt by its id.

        Args:
            prompt_id: ID of the prompt to retrieve

        Returns:
            Prompt: The requested prompt

        Raises:
            PromptNotFoundError: If prompt with given ID doesn't exist
        """
        prompt_data = self.storage.get_prompt(prompt_id)
        if not prompt_data:
            raise PromptNotFoundError(f"Prompt '{prompt_id}' not found.")

        return Prompt.from_dict(prompt_data)

    def list_prompts(self) -> List[Prompt]:
        """Get all registered prompts.

        Returns:
            List[Prompt]: List of all prompts
        """
        prompts = self.storage.list_prompts()
        return [self.get_prompt(prompt["id"]) for prompt in prompts]

    def get_version(self, prompt_id: str, version_id: str) -> Version:
        """Get a specific version of a prompt.

        Args:
            prompt_id: ID of the prompt
            version_id: ID of the version to retrieve

        Returns:
            Version: The requested version

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            VersionNotFoundError: If version doesn't exist
        """
        prompt = self.get_prompt(prompt_id)
        if version_id not in prompt.versions:
            raise VersionNotFoundError(
                f"Version {version_id} not found in prompt {prompt_id}"
            )
        return prompt.versions[version_id]

    def list_versions(self, prompt_id: str) -> Dict[str, Version]:
        """
        Get all versions of a prompt.

        Args:
            prompt_id: ID of the prompt

        Returns:
            List[Version]: List of all versions

        Raises:
            PromptNotFoundError: If prompt with given ID doesn't exist
        """
        prompt = self.get_prompt(prompt_id)
        return prompt.versions

    def delete_prompt(self, prompt_id: str) -> None:
        """Delete a prompt and its associated file data.

        Args:
            prompt_id: ID of the prompt to delete

        Raises:
            PromptNotFoundError: If prompt with given ID doesn't exist
        """
        if not self.storage.get_prompt(prompt_id):
            raise PromptNotFoundError(f"Prompt '{prompt_id}' not found.")

        # Remove from storage
        self.storage.delete_prompt(prompt_id)

    def add_run(
        self,
        prompt_id: str,
        version_id: str,
        final_prompt: str,
        variables: Optional[Dict[str, Any]] = None,
        llm_output: Optional[str] = None,
        execution_time: Optional[float] = None,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> Run:
        """Record a new execution run for a specific prompt version.

        Tracks the execution of a prompt version including the LLM's response,
        execution metrics, and configuration used.

        Args:
            prompt_id: ID of the prompt
            version_id: ID of the version executed
            llm_output: Output received from the LLM
            execution_time: Time taken for execution in seconds
            llm_config: Configuration used for the LLM call

        Returns:
            Run: The created run object

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            VersionNotFoundError: If version doesn't exist
        """
        prompt = self.get_prompt(prompt_id)
        if version_id not in prompt.versions:
            raise VersionNotFoundError(
                f"Version {version_id} not found in prompt {prompt_id}"
            )

        version = prompt.versions[version_id]
        run = version.add_run(
            final_prompt=final_prompt,
            variables=variables,
            llm_output=llm_output,
            execution_time=execution_time,
            llm_config=llm_config,
        )

        self.storage.update_prompt(prompt_id, prompt.to_dict())
        return run

    def get_run(self, prompt_id: str, version_id: str, run_id: str) -> Run:
        """Get a specific run of a prompt version.

        Args:
            prompt_id: ID of the prompt
            version_id: ID of the version
            run_id: ID of the run

        Returns:
            Run: The requested run

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            RunNotFoundError: If run doesn't exist
        """
        version = self.get_version(prompt_id, version_id)
        if run_id not in version.runs:
            raise RunNotFoundError(f"Run {run_id} not found in version {version_id}")
        return version.runs[run_id]

    def list_runs(self, prompt_id: str, version_id: str) -> List[Run]:
        """Get all runs for a specific prompt version.

        Args:
            prompt_id: ID of the prompt
            version_id: ID of the version

        Returns:
            List[Run]: List of all runs for the version
        """
        version = self.get_version(prompt_id, version_id)
        return list(version.runs.values())

    def sync_git(self) -> None:
        """Synchronize changes with git remote if storage backend supports it.

        Raises:
            StorageError: If storage backend doesn't support git operations
            StorageError: If sync operation fails
        """
        if not hasattr(self.storage, "sync"):
            raise StorageError("Storage backend doesn't support git synchronization")

        try:
            self.storage.sync()
        except Exception as e:
            raise StorageError(f"Failed to sync with git remote: {str(e)}") from e

    def get_version_by_content(self, prompt_id: str, content: str) -> Optional[Version]:
        """Get a version by its content.

        Args:
            prompt_id: ID of the prompt
            content: Content to search for

        Returns:
            Version: The version with matching content
            None: If no version matches the content
        """
        prompt = self.get_prompt(prompt_id)
        for version in prompt.versions.values():
            if version.content == content:
                return version
        return None

    # get last run of a prompt
    def get_last_run(self, prompt_id: str) -> Run:
        """Get the last run of a specific prompt.

        Args:
            prompt_id: ID of the prompt

        Returns:
            Run: The last run of the prompt
        """
        prompt = self.get_prompt(prompt_id)

        runs = []
        for version in prompt.versions.values():
            runs.extend(list(version.runs.values()))

        if runs:
            return sorted(runs, key=lambda x: x.created_at)[-1]

        return None
