from pathlib import Path

import pytest
import yaml
from git import Repo

from promptsite.exceptions import StorageError


def test_register_prompt(git_promptsite, storage_path):
    """Test registering a new prompt."""
    # Test with initial content
    git_promptsite.register_prompt(
        prompt_id="test1",
        initial_content="Test content",
        description="Test description",
        tags=["test", "example"],
    )

    # Test output level
    prompt = git_promptsite.get_prompt("test1")
    assert prompt.id == "test1"
    assert prompt.description == "Test description"
    assert prompt.tags == ["test", "example"]
    assert prompt.get_latest_version().content == "Test content"

    # Test storage level
    storage_dir = Path(storage_path) / "prompts" / "test1"
    assert storage_dir.exists()

    # Check prompt file
    prompt_path = storage_dir / "prompt.yaml"
    assert prompt_path.exists()
    with open(prompt_path) as f:
        prompt_data = yaml.safe_load(f)
        assert prompt_data["id"] == "test1"
        assert prompt_data["description"] == "Test description"
        assert prompt_data["tags"] == ["test", "example"]

    # Verify Git commit
    repo = Repo(storage_path)
    latest_commit = repo.head.commit
    assert "Create prompt: test1" in latest_commit.message
    assert str(prompt_path.relative_to(storage_path)) in [
        item.path for item in latest_commit.tree.traverse()
    ]


def test_add_prompt_version(git_promptsite, storage_path):
    """Test adding a new version to a prompt."""
    # First register a prompt
    git_promptsite.register_prompt("test2", initial_content="Initial content")

    # Add a new version
    new_version = git_promptsite.add_prompt_version("test2", "Updated content")

    # Test output level
    prompt = git_promptsite.get_prompt("test2")
    assert len(prompt.versions) == 2
    assert prompt.get_latest_version().version_id == new_version.version_id
    assert prompt.get_latest_version().content == "Updated content"

    # Test storage level
    storage_dir = Path(storage_path) / "prompts" / "test2"
    version_path = (
        storage_dir / "versions" / f"{new_version.version_id}" / "version.yaml"
    )
    assert version_path.exists()
    with open(version_path) as f:
        version_data = yaml.safe_load(f)
        assert version_data["content"] == "Updated content"

    # Verify Git commit
    repo = Repo(storage_path)
    latest_commit = repo.head.commit
    assert "Update prompt: test2" in latest_commit.message


def test_list_prompts(git_promptsite, storage_path):
    """Test listing all prompts."""
    # Register multiple prompts
    git_promptsite.register_prompt("test5a", initial_content="Content A")
    git_promptsite.register_prompt("test5b", initial_content="Content B")

    # Test output level
    prompts = git_promptsite.list_prompts()
    assert len(prompts) == 2
    assert any(p.id == "test5a" for p in prompts)
    assert any(p.id == "test5b" for p in prompts)

    # Test storage level
    storage_root = Path(storage_path) / "prompts"
    prompt_dirs = [d for d in storage_root.iterdir() if d.is_dir()]
    assert len(prompt_dirs) == 2
    assert storage_root / "test5a" in prompt_dirs
    assert storage_root / "test5b" in prompt_dirs

    # Verify Git commits
    repo = Repo(storage_path)
    commits = list(repo.iter_commits())
    assert any("Create prompt: test5a" in c.message for c in commits)
    assert any("Create prompt: test5b" in c.message for c in commits)


def test_list_prompt_versions(git_promptsite, storage_path):
    """Test listing all versions of a prompt."""
    # Register a prompt and add multiple versions
    git_promptsite.register_prompt("test_versions", initial_content="Version 1")
    git_promptsite.add_prompt_version("test_versions", "Version 2")
    git_promptsite.add_prompt_version("test_versions", "Version 3")

    # List versions
    versions = git_promptsite.list_versions("test_versions")

    # Convert to a list if necessary
    if isinstance(versions, dict):
        versions = list(versions.values())

    # Test output level
    assert len(versions) == 3
    assert versions[0].content == "Version 1"
    assert versions[1].content == "Version 2"
    assert versions[2].content == "Version 3"

    # Test storage level
    storage_dir = Path(storage_path) / "prompts" / "test_versions"
    version_files = list(storage_dir.glob("versions/*/version.yaml"))
    assert len(version_files) == 3

    # Verify Git commits
    repo = Repo(storage_path)
    commits = list(repo.iter_commits())
    assert any("Create prompt: test_versions" in c.message for c in commits)
    assert (
        len(
            [
                commit
                for commit in commits
                if "Add version" in commit.message and "test_versions" in commit.message
            ]
        )
        == 3
    )


def test_add_run(git_promptsite, storage_path):
    """Test adding a run to a prompt version."""
    # Setup - create a prompt first
    git_promptsite.register_prompt("test_run", initial_content="Test content")
    prompt = git_promptsite.get_prompt("test_run")
    version_id = prompt.get_latest_version().version_id

    # Test data
    llm_output = "Test LLM response"
    execution_time = 1.5
    llm_config = {"model": "test-model"}
    final_prompt = "Final prompt"
    variables = {"test_variable": "test_value"}

    # Add run
    run = git_promptsite.add_run(
        prompt_id="test_run",
        version_id=version_id,
        llm_output=llm_output,
        execution_time=execution_time,
        llm_config=llm_config,
        final_prompt=final_prompt,
        variables=variables,
    )

    # Verify run data
    assert run.llm_output == llm_output
    assert run.execution_time == execution_time
    assert run.llm_config == llm_config
    assert run.run_id is not None
    assert run.final_prompt == final_prompt
    assert run.variables == variables

    # Test storage level
    storage_dir = Path(storage_path) / "prompts" / "test_run"
    run_path = storage_dir / "versions" / version_id / "runs" / f"{run.run_id}.yaml"
    assert run_path.exists()

    # Verify Git commit
    repo = Repo(storage_path)
    commits = list(repo.iter_commits())
    assert (
        len(
            [
                commit
                for commit in commits
                if "Add run" in commit.message and "test_run" in commit.message
            ]
        )
        == 1
    )


def test_get_run(git_promptsite, storage_path):
    """Test retrieving a specific run."""
    # Setup - create a prompt and add a run
    git_promptsite.register_prompt("test_get_run", initial_content="Test content")
    prompt = git_promptsite.get_prompt("test_get_run")
    version_id = prompt.get_latest_version().version_id

    original_run = git_promptsite.add_run(
        prompt_id="test_get_run",
        version_id=version_id,
        llm_output="Test output",
        final_prompt="Final prompt",
        variables={"test_variable": "test_value"},
    )

    # Get the run
    retrieved_run = git_promptsite.get_run(
        prompt_id="test_get_run", version_id=version_id, run_id=original_run.run_id
    )

    # Verify
    assert retrieved_run.run_id == original_run.run_id
    assert retrieved_run.llm_output == original_run.llm_output
    assert retrieved_run.created_at == original_run.created_at
    assert retrieved_run.final_prompt == original_run.final_prompt
    assert retrieved_run.variables == original_run.variables


def test_list_runs(git_promptsite, storage_path):
    """Test listing all runs for a prompt version."""
    # Setup - create a prompt
    git_promptsite.register_prompt("test_list_runs", initial_content="Test content")
    prompt = git_promptsite.get_prompt("test_list_runs")
    version_id = prompt.get_latest_version().version_id

    # Add multiple runs
    run1 = git_promptsite.add_run(
        prompt_id="test_list_runs",
        version_id=version_id,
        llm_output="Output 1",
        final_prompt="Final prompt 1",
        variables={"test_variable": "test_value"},
    )
    run2 = git_promptsite.add_run(
        prompt_id="test_list_runs",
        version_id=version_id,
        llm_output="Output 2",
        final_prompt="Final prompt 2",
        variables={"test_variable": "test_value"},
    )

    # List runs
    runs = git_promptsite.list_runs(prompt_id="test_list_runs", version_id=version_id)

    # Verify output
    assert len(runs) == 2
    assert any(r.run_id == run1.run_id for r in runs)
    assert any(r.run_id == run2.run_id for r in runs)
    assert any(r.final_prompt == "Final prompt 1" for r in runs)
    assert any(r.final_prompt == "Final prompt 2" for r in runs)
    assert any(r.variables == {"test_variable": "test_value"} for r in runs)

    # Test storage level
    storage_dir = Path(storage_path) / "prompts" / "test_list_runs"
    run_files = list(storage_dir.glob(f"versions/{version_id}/runs/*.yaml"))
    assert len(run_files) == 2


def test_sync_git_error(git_promptsite, mocker):
    """Test handling of git sync errors."""
    # Mock the storage sync method to raise an exception
    mocker.patch.object(
        git_promptsite.storage,
        "sync",
        side_effect=Exception("Remote connection failed"),
    )

    # Verify the error is properly wrapped in StorageError
    with pytest.raises(StorageError) as exc_info:
        git_promptsite.sync_git()

    assert "Failed to sync with git remote: Remote connection failed" in str(
        exc_info.value
    )
    assert git_promptsite.storage.sync.called


# ... continue with other tests from test_file_storage.py, adding Git verification ...
