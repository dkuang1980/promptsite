from pathlib import Path

import pytest
import yaml

from promptsite.config import Config
from promptsite.core import PromptSite
from promptsite.exceptions import PromptNotFoundError
from promptsite.storage.file import FileStorage


def test_register_prompt(promptsite, storage_path):
    """Test registering a new prompt."""
    # Test with initial content
    promptsite.register_prompt(
        prompt_id="test1",
        initial_content="Test content",
        description="Test description",
        tags=["test", "example"],
    )

    # Test output level
    prompt = promptsite.get_prompt("test1")
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


def test_add_prompt_version(promptsite, storage_path):
    """Test adding a new version to a prompt."""
    # First register a prompt
    promptsite.register_prompt("test2", initial_content="Initial content")

    # Add a new version
    new_version = promptsite.add_prompt_version("test2", "Updated content")

    # Test output level
    prompt = promptsite.get_prompt("test2")
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


def test_list_prompts(promptsite, storage_path):
    """Test listing all prompts."""
    # Register multiple prompts
    promptsite.register_prompt("test5a", initial_content="Content A")
    promptsite.register_prompt("test5b", initial_content="Content B")

    # Test output level
    prompts = promptsite.list_prompts()
    assert len(prompts) == 2
    assert any(p.id == "test5a" for p in prompts)
    assert any(p.id == "test5b" for p in prompts)

    # Test storage level
    storage_root = Path(storage_path) / "prompts"
    prompt_dirs = [d for d in storage_root.iterdir() if d.is_dir()]
    assert len(prompt_dirs) == 2
    assert storage_root / "test5a" in prompt_dirs
    assert storage_root / "test5b" in prompt_dirs


def test_list_prompt_versions(promptsite, storage_path):
    """Test listing all versions of a prompt."""
    # Register a prompt and add multiple versions
    promptsite.register_prompt("test_versions", initial_content="Version 1")
    promptsite.add_prompt_version("test_versions", "Version 2")
    promptsite.add_prompt_version("test_versions", "Version 3")

    # List versions
    versions = promptsite.list_versions("test_versions")

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
    # Exclude metadata.yaml from the count
    version_files = [f for f in storage_dir.glob("versions/*/version.yaml")]
    assert len(version_files) == 3


def test_add_run(promptsite):
    """Test adding a run to a prompt version."""
    # Setup - create a prompt first
    promptsite.register_prompt("test_run", initial_content="Test content")
    prompt = promptsite.get_prompt("test_run")
    version_id = prompt.get_latest_version().version_id

    # Test data
    llm_output = "Test LLM response"
    execution_time = 1.5
    llm_config = {"model": "test-model"}
    final_prompt = "Final prompt"
    variables = {"test_variable": "test_value"}
    # Add run
    run = promptsite.add_run(
        prompt_id="test_run",
        version_id=version_id,
        llm_output=llm_output,
        execution_time=execution_time,
        llm_config=llm_config,
        final_prompt=final_prompt,
        variables=variables,
    )

    # Verify
    assert run.llm_output == llm_output
    assert run.execution_time == execution_time
    assert run.llm_config == llm_config
    assert run.run_id is not None
    assert run.created_at is not None
    assert run.run_at is not None
    assert run.final_prompt == final_prompt
    assert run.variables == variables


def test_get_run(promptsite):
    """Test retrieving a specific run."""
    # Setup - create a prompt and add a run
    promptsite.register_prompt("test_get_run", initial_content="Test content")
    prompt = promptsite.get_prompt("test_get_run")
    version_id = prompt.get_latest_version().version_id

    original_run = promptsite.add_run(
        prompt_id="test_get_run",
        version_id=version_id,
        llm_output="Test output",
        final_prompt="Final prompt",
        variables={"test_variable": "test_value"},
    )

    # Get the run
    retrieved_run = promptsite.get_run(
        prompt_id="test_get_run", version_id=version_id, run_id=original_run.run_id
    )

    # Verify
    assert retrieved_run.run_id == original_run.run_id
    assert retrieved_run.llm_output == original_run.llm_output
    assert retrieved_run.created_at == original_run.created_at
    assert retrieved_run.final_prompt == original_run.final_prompt
    assert retrieved_run.variables == original_run.variables


def test_list_runs(promptsite):
    """Test listing all runs for a prompt version."""
    # Setup - create a prompt
    promptsite.register_prompt("test_list_runs", initial_content="Test content")
    prompt = promptsite.get_prompt("test_list_runs")
    version_id = prompt.get_latest_version().version_id

    # Add multiple runs
    run1 = promptsite.add_run(
        prompt_id="test_list_runs",
        version_id=version_id,
        llm_output="Output 1",
        final_prompt="Final prompt 1",
        variables={"test_variable": "test_value"},
    )
    run2 = promptsite.add_run(
        prompt_id="test_list_runs",
        version_id=version_id,
        llm_output="Output 2",
        final_prompt="Final prompt 2",
        variables={"test_variable": "test_value"},
    )

    # List runs
    runs = promptsite.list_runs(prompt_id="test_list_runs", version_id=version_id)

    # Verify
    assert len(runs) == 2
    assert any(r.run_id == run1.run_id for r in runs)
    assert any(r.run_id == run2.run_id for r in runs)
    assert any(r.llm_output == "Output 1" for r in runs)
    assert any(r.llm_output == "Output 2" for r in runs)
    assert any(r.final_prompt == "Final prompt 1" for r in runs)
    assert any(r.final_prompt == "Final prompt 2" for r in runs)
    assert any(r.variables == {"test_variable": "test_value"} for r in runs)


def test_get_version_by_content(promptsite):
    """Test getting a version by its content."""
    # Register prompt with initial version
    promptsite.register_prompt("test_content", initial_content="Version 1 content")

    # Add another version
    promptsite.add_prompt_version("test_content", "Version 2 content")

    # Test finding existing content
    version = promptsite.get_version_by_content("test_content", "Version 1 content")
    assert version is not None
    assert version.content == "Version 1 content"

    # Test finding non-existent content
    version = promptsite.get_version_by_content("test_content", "Non-existent content")
    assert version is None


def test_default_storage_initialization(tmp_path):
    """Test that PromptSite initializes with default FileStorage when no storage is provided."""
    # Set up temporary config
    Config.BASE_DIRECTORY = str(tmp_path)

    # Initialize PromptSite without storage
    ps = PromptSite()

    # Verify storage type
    assert isinstance(ps.storage, FileStorage)
    assert ps.storage.base_path == str(tmp_path)

    # Test basic functionality with default storage
    ps.register_prompt(
        prompt_id="test_default",
        initial_content="Test content",
        description="Test description",
    )

    # Verify prompt was stored correctly
    prompt = ps.get_prompt("test_default")
    assert prompt.id == "test_default"
    assert prompt.description == "Test description"
    assert prompt.get_latest_version().content == "Test content"

    # Verify storage structure
    storage_dir = tmp_path / "prompts" / "test_default"
    assert storage_dir.exists()
    assert (storage_dir / "prompt.yaml").exists()


def test_delete_prompt(promptsite, storage_path):
    """Test deleting a prompt and verifying it's removed from storage."""
    # First register a prompt
    promptsite.register_prompt(
        "test_delete",
        initial_content="Test content",
        description="Test description",
        tags=["test"],
    )

    # Verify prompt exists
    prompt_dir = Path(storage_path) / "prompts" / "test_delete"
    assert prompt_dir.exists()

    # Delete the prompt
    promptsite.delete_prompt("test_delete")

    # Verify prompt directory is removed
    assert not prompt_dir.exists()

    # Verify prompt is no longer retrievable
    with pytest.raises(PromptNotFoundError):
        promptsite.get_prompt("test_delete")


def test_get_version_from_initial_prompt(promptsite):
    """Test getting a version from an initial prompt."""
    promptsite.register_prompt("test_version_from_initial_prompt")
    prompt = promptsite.get_prompt("test_version_from_initial_prompt")
    assert prompt.get_latest_version() == None
    
    