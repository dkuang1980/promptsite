"""File-based storage implementations for promptsite."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import yaml

from .base import StorageBackend


@dataclass
class FileStorage(StorageBackend):
    """File-based storage implementation.

    Implements the StorageBackend interface using a file system structure:
    - prompts/<prompt_id>/prompt.yaml: Stores prompt metadata
    - prompts/<prompt_id>/versions/<version_id>/version.yaml: Stores version data
    - prompts/<prompt_id>/versions/<version_id>/runs/<run_id>.yaml: Stores run data

    Attributes:
        base_path (str): Base directory for storing all prompt data
        prompts_dir (str): Directory containing all prompt data

    Example:
        >>> storage = FileStorage(base_path="/path/to/storage")
        >>> storage.create_prompt("my-prompt", prompt_data)
    """

    base_path: str

    def __post_init__(self):
        # Ensure prompts directory exists
        self.prompts_dir = os.path.join(self.base_path, "prompts")
        os.makedirs(self.prompts_dir, exist_ok=True)

    def _ensure_path_exists(self, path: str) -> None:
        """Ensure the directory path exists.

        Args:
            path (str): Directory path to create
        """
        os.makedirs(path, exist_ok=True)

    def _write_yaml(self, path: str, data: Dict) -> None:
        """Write data to a YAML file.

        Args:
            path (str): Path to the YAML file
            data (Dict): Data to write to the file
        """
        with open(path, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False)

    def _read_yaml(self, path: str) -> Optional[Dict]:
        """Read data from a YAML file.

        Args:
            path (str): Path to the YAML file

        Returns:
            Optional[Dict]: The loaded YAML data or None if file not found
        """
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return None

    def _path_exists(self, path: str) -> bool:
        """Check if a path exists.

        Args:
            path (str): Path to check

        Returns:
            bool: True if path exists, False otherwise
        """
        return os.path.exists(path)

    def _remove_file(self, path: str) -> None:
        """Remove a file if it exists.

        Args:
            path (str): Path to the file to remove
        """
        if os.path.exists(path):
            os.remove(path)

    def _remove_directory(self, path: str) -> None:
        """Remove a directory and its contents if it exists.

        Args:
            path (str): Path to the directory to remove
        """
        if os.path.exists(path):
            import shutil

            shutil.rmtree(path)

    def _get_prompt_path(self, prompt_id: str) -> str:
        """Get the full path for a prompt directory.

        Args:
            prompt_id (str): ID of the prompt

        Returns:
            str: Full path to the prompt directory
        """
        return os.path.join(self.prompts_dir, prompt_id)

    def _get_version_path(self, prompt_id: str, version_id: str) -> str:
        """Get the full path for a version directory.

        Args:
            prompt_id (str): ID of the prompt
            version_id (str): ID of the version

        Returns:
            str: Full path to the version directory
        """
        return os.path.join(self._get_prompt_path(prompt_id), "versions", version_id)

    def _get_run_path(self, prompt_id: str, version_id: str, run_id: str) -> str:
        """Get the full path for a run file.

        Args:
            prompt_id (str): ID of the prompt
            version_id (str): ID of the version
            run_id (str): ID of the run

        Returns:
            str: Full path to the run YAML file
        """
        runs_path = os.path.join(self._get_version_path(prompt_id, version_id), "runs")
        if not os.path.exists(runs_path):
            os.makedirs(runs_path)
        return os.path.join(runs_path, f"{run_id}.yaml")

    def create_prompt(self, prompt_id: str, prompt_data: Dict) -> None:
        """Create a new prompt in storage.

        Args:
            prompt_id (str): Unique identifier for the prompt
            prompt_data (Dict): Dictionary containing prompt metadata and initial version
                Expected format:
                {
                    "versions": [{"version_id": str, "content": str, ...}],
                    ...other metadata...
                }

        Raises:
            KeyError: If prompt_data doesn't contain required version data
        """
        prompt_dir = os.path.join(self.prompts_dir, prompt_id)
        os.makedirs(prompt_dir, exist_ok=True)

        prompt_path = os.path.join(prompt_dir, "prompt.yaml")
        versions = prompt_data.pop("versions", None)
        with open(prompt_path, "w") as f:
            yaml.safe_dump(prompt_data, f)

        if versions:
            self.add_version(prompt_id, versions[0])

    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Get prompt data including versions."""
        prompt_path = os.path.join(self.prompts_dir, prompt_id, "prompt.yaml")
        try:
            with open(prompt_path, "r") as f:
                data = yaml.safe_load(f)
                # Get versions from list_versions
                if data:
                    data["versions"] = self.list_versions(prompt_id)
                    # Convert version data back to proper datetime objects
                    for version in data["versions"]:
                        if isinstance(version["created_at"], str):
                            version["created_at"] = datetime.fromisoformat(
                                version["created_at"].replace("Z", "+00:00")
                            )
                return data
        except FileNotFoundError:
            return None

    def update_prompt(self, prompt_id: str, prompt_data: Dict) -> None:
        """Update an existing prompt's metadata and versions.

        Args:
            prompt_id (str): ID of the prompt to update
            prompt_data (Dict): Updated prompt data including metadata and versions
                Expected format:
                {
                    "versions": [{"version_id": str, "content": str, ...}],
                    ...other metadata...
                }

        Note:
            - Existing versions not included in prompt_data remain unchanged
            - New versions are added
            - Modified versions are completely replaced
        """
        # Get existing versions from the versions subdirectory
        existing_versions = {v["version_id"]: v for v in self.list_versions(prompt_id)}

        # Get new versions from the prompt data and convert to dict if it's a list
        versions = prompt_data.get("versions", [])
        new_versions = {}
        if isinstance(versions, list):
            for version in versions:
                new_versions[version["version_id"]] = version
        else:
            new_versions = versions

        # Update metadata (without versions)
        metadata = {k: v for k, v in prompt_data.items() if k != "versions"}
        metadata_path = os.path.join(self._get_prompt_path(prompt_id), "prompt.yaml")
        with open(metadata_path, "w") as f:
            yaml.safe_dump(metadata, f, sort_keys=False)

        # Update versions
        for version_id, version_data in new_versions.items():
            if version_id not in existing_versions:
                # New version - just add it
                self.add_version(prompt_id, version_data)
            elif existing_versions[version_id] != version_data:
                # Updated version - remove old directory first
                version_dir = self._get_version_path(prompt_id, version_id)
                self._remove_directory(version_dir)
                self.add_version(prompt_id, version_data)

    def delete_prompt(self, prompt_id: str) -> None:
        """Delete a prompt and all its associated data.

        Args:
            prompt_id (str): ID of the prompt to delete

        Note:
            Silently succeeds if the prompt doesn't exist
        """
        path = self._get_prompt_path(prompt_id)
        if os.path.exists(path):
            import shutil

            shutil.rmtree(path)

    def add_version(self, prompt_id: str, version_data: Dict) -> None:
        """Add a new version to an existing prompt.

        Args:
            prompt_id (str): ID of the prompt
            version_data (Dict): Version data to add
                Required keys:
                - content: str
                - created_at: datetime
                - version_id: str
                Optional keys:
                - runs: List[Dict]
                - variables: Dict

        Raises:
            ValueError: If the prompt doesn't exist
        """
        prompt_path = self._get_prompt_path(prompt_id)
        if not os.path.exists(prompt_path):
            raise ValueError(f"Prompt {prompt_id} does not exist")

        # Ensure all values are serializable
        serializable_data = {
            "content": str(version_data["content"]),
            "created_at": str(version_data["created_at"]),
            "version_id": str(version_data["version_id"]),
            "variables": version_data.get("variables", {})
            if version_data.get("variables")
            else None,
        }

        version_path = self._get_version_path(prompt_id, version_data["version_id"])
        self._ensure_path_exists(version_path)
        with open(os.path.join(version_path, "version.yaml"), "w") as f:
            yaml.safe_dump(serializable_data, f, sort_keys=False)

        # Add run files for each run in version data
        for run in version_data.get("runs", []):
            self.add_run(prompt_id, version_data["version_id"], run)

    def add_run(self, prompt_id: str, version_id: str, run_data: Dict) -> None:
        """Add a new run to a specific version of a prompt.

        Args:
            prompt_id (str): ID of the prompt
            version_id (str): ID of the version
            run_data (Dict): Run data to store
                Required keys:
                - run_id: str

        Note:
            Creates the runs directory if it doesn't exist
        """
        run_path = self._get_run_path(prompt_id, version_id, run_data["run_id"])

        with open(run_path, "w") as f:
            yaml.safe_dump(run_data, f, sort_keys=False)

    def list_versions(self, prompt_id: str) -> List[Dict]:
        """List all versions for a specific prompt.

        Returns:
            List of dictionaries containing version data.
            Each dictionary contains the following keys:
            - version_id: str
            - content: str
            - created_at: datetime
        - runs: List[Dict]
        """
        prompt_path = self._get_prompt_path(prompt_id)
        versions_path = os.path.join(prompt_path, "versions")
        versions = []

        try:
            for version_dir in os.listdir(versions_path):
                version_file = os.path.join(versions_path, version_dir, "version.yaml")
                if os.path.isdir(
                    os.path.join(versions_path, version_dir)
                ) and os.path.exists(version_file):
                    with open(version_file, "r") as f:
                        version_data = yaml.safe_load(f)
                        version_data["runs"] = self.list_runs(prompt_id, version_dir)
                        versions.append(version_data)

            # Sort versions by created_at timestamp
            versions.sort(key=lambda x: x["created_at"])
            return versions
        except FileNotFoundError:
            return []

    def list_runs(self, prompt_id: str, version_id: str) -> List[Dict]:
        """List all runs for a specific version.

        Returns:
            List of dictionaries containing run data.
            Each dictionary contains the following keys:
            - run_id: str
            - created_at: datetime
        """
        runs_path = os.path.join(self._get_version_path(prompt_id, version_id), "runs")
        runs = []
        try:
            for run_file in os.listdir(runs_path):
                with open(os.path.join(runs_path, run_file), "r") as f:
                    runs.append(yaml.safe_load(f))
        except FileNotFoundError:
            pass
        return runs

    def get_version(self, prompt_id: str, version_id: str) -> Optional[Dict]:
        """Get a specific version of a prompt.

        Args:
            prompt_id (str): ID of the prompt
            version_id (str): ID of the version

        Returns:
            Dictionary containing version data.
        """
        try:
            version_path = os.path.join(
                self._get_version_path(prompt_id, version_id), "version.yaml"
            )
            with open(version_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return None

    def list_prompts(self) -> List[Dict]:
        """List all prompts in storage with their complete information.

        Returns:
            List of prompt dictionaries containing all metadata, versions, and runs
        """
        try:
            prompts_dir = os.path.join(self.base_path, "prompts")
            if not os.path.exists(prompts_dir):
                return []

            prompts = []
            for prompt_id in os.listdir(prompts_dir):
                prompt_path = os.path.join(prompts_dir, prompt_id)
                prompt_yaml = os.path.join(prompt_path, "prompt.yaml")

                if os.path.isdir(prompt_path) and os.path.exists(prompt_yaml):
                    # Get the prompt data using existing method which already includes versions
                    prompt_data = self.get_prompt(prompt_id)
                    if prompt_data:
                        prompts.append(prompt_data)

            return prompts
        except FileNotFoundError:
            return []
