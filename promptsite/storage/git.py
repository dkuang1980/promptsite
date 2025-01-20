"""Git-based storage implementations for promptsite."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from git import GitCommandError, Repo

from ..exceptions import StorageError
from .file import FileStorage


@dataclass
class GitStorage(FileStorage):
    """Git-based storage implementation extending FileStorage.

    Extends FileStorage to add Git version control capabilities. All operations
    are automatically committed to the Git repository and can be synced with
    a remote repository.

    Attributes:
        remote (str): URL of the remote Git repository
        branch (str): Git branch to use (defaults to "main")
        auto_sync (bool): Whether to automatically sync with remote
        repo (Repo): GitPython repository instance

    Example:
        >>> storage = GitStorage(
        ...     base_path="/path/to/repo",
        ...     remote="https://github.com/user/repo.git",
        ...     branch="main",
        ...     auto_sync=True
        ... )
    """

    remote: str
    branch: str = "main"
    auto_sync: bool = False

    def __post_init__(self) -> None:
        """Initialize the storage."""
        # Initialize FileStorage first
        super().__post_init__()
        # Then initialize Git repository
        self._ensure_repo()

    def _ensure_repo(self) -> None:
        """Ensure git repository exists and is properly configured."""
        try:
            repo_path = Path(self.base_path)
            git_dir = repo_path / ".git"

            # Create directory if it doesn't exist
            if not repo_path.exists():
                repo_path.mkdir(parents=True)
            # If remote is provided and repo doesn't exist yet, try to clone first

            if self.remote and not git_dir.exists():
                # Save existing files before cloning
                temp_dir = repo_path.parent / f"{repo_path.name}_temp"
                if repo_path.exists():
                    import shutil

                    shutil.copytree(repo_path, temp_dir, dirs_exist_ok=True)
                    shutil.rmtree(repo_path)

                self.repo = Repo.clone_from(self.remote, repo_path, branch=self.branch)

                # Restore existing files if cloning failed
                if temp_dir.exists():
                    shutil.copytree(temp_dir, repo_path, dirs_exist_ok=True)
                    shutil.rmtree(temp_dir)
            # Initialize repository if .git doesn't exist
            if not git_dir.exists():
                self.repo = Repo.init(repo_path)

                # Configure git user
                self.repo.config_writer().set_value(
                    "user", "name", "promptsite"
                ).release()
                self.repo.config_writer().set_value(
                    "user", "email", "promptsite@local"
                ).release()

                # Create an initial empty commit
                # Create an empty file to commit
                readme_path = repo_path / "README.md"
                readme_path.write_text("# Promptsite Repository\n")
                self.repo.index.add(["README.md"])
                self.repo.index.commit("Initial commit")

                # Now we can create the branch
                if self.branch not in self.repo.heads:
                    self.repo.create_head(self.branch)
                self.repo.heads[self.branch].checkout()

                # Setup remote if provided
                if self.remote:
                    self.repo.create_remote("origin", self.remote)
            else:
                self.repo = Repo(repo_path)
                # Ensure we're on the correct branch
                if self.branch not in self.repo.heads:
                    self.repo.create_head(self.branch)
                self.repo.heads[self.branch].checkout()

        except GitCommandError as e:
            raise StorageError(f"Git repository error: {str(e)}") from e

    def _commit(self, message: str, files: Optional[List[str]] = None) -> None:
        """Create a git commit with the specified message and files.

        Args:
            message (str): Commit message
            files (Optional[List[str]]): List of file paths to add to the commit
        """
        try:
            if files:
                # Convert paths to be relative to the repo root
                relative_files = [
                    str(Path(f).relative_to(self.base_path)) for f in files
                ]
                self.repo.index.add(relative_files)
            else:
                self.repo.index.add("*")

            if self.repo.is_dirty() or self.repo.untracked_files:
                self.repo.index.commit(message)
                if self.auto_sync:
                    self.sync()
        except Exception as e:
            raise StorageError(f"Failed to commit changes: {str(e)}") from e

    def sync(self) -> None:
        """Sync local changes with remote repository if configured."""
        if not self.remote:
            return  # Skip sync if no remote configured

        if "origin" not in self.repo.remotes:
            return  # Skip sync if origin remote not found

        try:
            # Try to pull first
            try:
                self.repo.remotes.origin.pull(self.repo.active_branch.name)
            except GitCommandError as pull_error:
                if "couldn't find remote ref" in str(pull_error):
                    # Remote is empty, skip pull
                    pass
                else:
                    raise pull_error

            # Then try to push
            try:
                self.repo.remotes.origin.push(self.repo.active_branch.name)
            except GitCommandError as push_error:
                if "remote contains work that you do" in str(push_error):
                    # Handle merge conflicts
                    raise StorageError(
                        "Remote contains work that needs to be merged first"
                    ) from push_error
                else:
                    raise StorageError(
                        f"Failed to push to remote: {str(push_error)}"
                    ) from push_error

        except GitCommandError as e:
            if "Repository not found" in str(e):
                raise StorageError(
                    "Remote repository not found. Please check the repository URL and your access permissions."
                ) from e
            elif "Authentication failed" in str(e):
                raise StorageError(
                    "Git authentication failed. Please check your credentials."
                ) from e
            else:
                raise StorageError(f"Failed to sync with remote: {str(e)}") from e

    def create_prompt(self, prompt_id: str, prompt_data: Dict) -> None:
        """Create a new prompt in the Git repository.

        Args:
            prompt_id (str): Unique identifier for the prompt
            prompt_data (Dict): Prompt data including content and metadata
        """
        super().create_prompt(prompt_id, prompt_data)
        self._commit(
            f"Create prompt: {prompt_id}", [str(self._get_prompt_path(prompt_id))]
        )

    def update_prompt(self, prompt_id: str, prompt_data: Dict) -> None:
        """Update an existing prompt in the Git repository.

        Args:
            prompt_id (str): Unique identifier for the prompt
            prompt_data (Dict): Prompt data including content and metadata
        """
        super().update_prompt(prompt_id, prompt_data)
        self._commit(
            f"Update prompt: {prompt_id}", [str(self._get_prompt_path(prompt_id))]
        )

    def delete_prompt(self, prompt_id: str) -> None:
        """Delete an existing prompt from the Git repository.

        Args:
            prompt_id (str): Unique identifier for the prompt
        """
        path = self._get_prompt_path(prompt_id)
        super().delete_prompt(prompt_id)
        self._commit(f"Delete prompt: {prompt_id}", [str(path)])

    def add_version(self, prompt_id: str, version_data: Dict) -> None:
        """Add a new version to an existing prompt in the Git repository.

        Args:
            prompt_id (str): Unique identifier for the prompt
            version_data (Dict): Version data including content and metadata
        """
        super().add_version(prompt_id, version_data)
        self._commit(
            f"Add version {version_data.get('version_id')} to prompt: {prompt_id}",
            [str(self._get_prompt_path(prompt_id))],
        )

    def add_run(self, prompt_id: str, version_id: str, run_data: Dict) -> None:
        """Add a new run to an existing version of a prompt in the Git repository.

        Args:
            prompt_id (str): Unique identifier for the prompt
            version_id (str): Unique identifier for the version
            run_data (Dict): Run data including output and metadata
        """
        super().add_run(prompt_id, version_id, run_data)
        self._commit(
            f"Add run {run_data.get('run_id')} to version {version_id} of prompt: {prompt_id}",
            [
                str(self._get_prompt_path(prompt_id)),
                str(self._get_version_path(prompt_id, version_id)),
            ],
        )
