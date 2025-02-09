import pytest
from pydantic import BaseModel, Field

from promptsite.config import Config
from promptsite.decorator import tracker
from promptsite.exceptions import (
    ContentRequiredError,
    InvalidPromptContentError,
    PromptAlreadyExistsError,
    PromptNotFoundError,
    RunNotFoundError,
    StorageBackendNotFoundError,
    StorageError,
    VariableUnmatchError,
    VariableValidationError,
    VersionNotFoundError,
)
from promptsite.model.variable import ArrayVariable, ObjectVariable


def test_get_nonexistent_prompt(promptsite):
    """Test getting a prompt that doesn't exist."""
    with pytest.raises(PromptNotFoundError):
        promptsite.get_prompt("nonexistent")


def test_add_prompt_version_no_content(promptsite):
    """Test adding a version without content."""
    promptsite.register_prompt("test_version", initial_content="Initial content")

    with pytest.raises(InvalidPromptContentError):
        promptsite.add_prompt_version("test_version")


def test_delete_prompt_not_found(promptsite):
    """Test deleting a non-existent prompt."""
    with pytest.raises(PromptNotFoundError):
        promptsite.delete_prompt("nonexistent")


def test_sync_git_not_supported(promptsite):
    """Test git sync with unsupported storage backend."""
    with pytest.raises(
        StorageError, match="Storage backend doesn't support git synchronization"
    ):
        promptsite.sync_git()


def test_get_version_by_content_prompt_not_found(promptsite):
    """Test getting a version by content for non-existent prompt."""
    with pytest.raises(PromptNotFoundError):
        promptsite.get_version_by_content("nonexistent", "Some content")


def test_add_prompt_version_not_found(promptsite):
    """Test adding a version to a non-existent prompt."""
    with pytest.raises(PromptNotFoundError) as exc_info:
        promptsite.add_prompt_version("nonexistent", "New content")

    assert str(exc_info.value) == "Prompt 'nonexistent' not found."


def test_get_nonexistent_version(promptsite):
    """Test getting a version that doesn't exist."""
    # First create a prompt with a version
    promptsite.register_prompt("test_version", initial_content="Initial content")

    # Try to get a non-existent version
    with pytest.raises(VersionNotFoundError) as exc_info:
        promptsite.get_version("test_version", "nonexistent_version_id")

    assert (
        str(exc_info.value)
        == "Version nonexistent_version_id not found in prompt test_version"
    )


def test_get_run_not_found(promptsite):
    """Test getting a non-existent run throws PromptVersionError."""
    # First create a prompt with a version and run
    promptsite.register_prompt("test_run_error", initial_content="Test content")
    prompt = promptsite.get_prompt("test_run_error")
    version_id = prompt.get_latest_version().version_id

    # Add a run to have a valid version with runs
    promptsite.add_run(
        prompt_id="test_run_error",
        version_id=version_id,
        final_prompt="Test prompt",
        llm_output="Test output",
    )

    # Try to get a non-existent run
    with pytest.raises(RunNotFoundError) as exc_info:
        promptsite.get_run("test_run_error", version_id, "nonexistent_run_id")

    assert (
        str(exc_info.value)
        == f"Run nonexistent_run_id not found in version {version_id}"
    )


def test_register_prompt_already_exists(promptsite):
    """Test registering a prompt that already exists."""
    promptsite.register_prompt("test1", initial_content="Original content")

    with pytest.raises(PromptAlreadyExistsError):
        promptsite.register_prompt("test1", initial_content="New content")


def test_add_run_nonexistent_version(promptsite):
    """Test adding a run to a non-existent version."""
    # First create a prompt
    promptsite.register_prompt("test_run_error", initial_content="Test content")

    # Try to add run with non-existent version
    with pytest.raises(VersionNotFoundError) as exc_info:
        promptsite.add_run(
            prompt_id="test_run_error",
            version_id="nonexistent_version",
            final_prompt="Test prompt",
            llm_output="Test output",
        )

    assert "Version nonexistent_version not found in prompt test_run_error" in str(
        exc_info.value
    )


def test_storage_backend_not_found(promptsite):
    """Test retrieving a storage backend with an unsupported type."""
    # Mock the configuration to have an unsupported storage backend
    config = Config(config={"storage_backend": "unsupported_backend"})

    with pytest.raises(StorageBackendNotFoundError) as exc_info:
        config.get_storage_backend()

    assert str(exc_info.value) == "Storage backend 'unsupported_backend' not found"


def test_content_required_error(promptsite):
    """Test content required error."""
    with pytest.raises(ContentRequiredError):

        @tracker(prompt_id="test_prompt", description="Test prompt for decorator")
        def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
            # Simulate LLM response
            return content

        mock_llm_call()


def test_variable_validation_error_object_variable(promptsite):
    """Test variable validation error."""

    class TestModel(BaseModel):
        first_name: str = Field(description="The person's first name.")

    with pytest.raises(VariableValidationError):

        @tracker(
            prompt_id="test_prompt",
            description="Test prompt for decorator",
            variables={"test_variable": ObjectVariable(model=TestModel)},
        )
        def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
            # Simulate LLM response
            return content

        mock_llm_call(
            content="This is a new test prompt version {{ test_variable }}",
            variables={"test_variable": {"first_name": 123}},
        )

    with pytest.raises(VariableValidationError):

        @tracker(
            prompt_id="test_prompt",
            description="Test prompt for decorator",
            variables={"test_variable": ObjectVariable(model=TestModel)},
        )
        def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
            # Simulate LLM response
            return content

        mock_llm_call(
            content="This is a new test prompt version {{ test_variable }}",
            variables={"test_variable": "person"},
        )


def test_variable_validation_error_array_variable(promptsite):
    """Test variable validation error."""

    class TestModel(BaseModel):
        first_name: str = Field(description="The person's first name.")

    with pytest.raises(VariableValidationError):

        @tracker(
            prompt_id="test_prompt",
            description="Test prompt for decorator",
            variables={"test_variable": ArrayVariable(model=TestModel)},
        )
        def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
            # Simulate LLM response
            return content

        mock_llm_call(
            content="This is a new test prompt version {{ test_variable }}",
            variables={"test_variable": "person"},
        )

    with pytest.raises(VariableValidationError):

        @tracker(
            prompt_id="test_prompt",
            description="Test prompt for decorator",
            variables={"test_variable": ArrayVariable(model=TestModel)},
        )
        def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
            # Simulate LLM response
            return content

        mock_llm_call(
            content="This is a new test prompt version {{ test_variable }}",
            variables={"test_variable": [{"first_name": 123}]},
        )


def test_variable_unmatch_error(promptsite):
    """Test variable unmatch error."""

    class TestModel(BaseModel):
        first_name: str = Field(description="The person's first name.")

    with pytest.raises(VariableUnmatchError):

        @tracker(
            prompt_id="test_prompt",
            description="Test prompt for decorator",
            variables={"test_variable": ObjectVariable(model=TestModel)},
        )
        def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
            # Simulate LLM response
            return content

        mock_llm_call(
            content="This is a new test prompt version {{ test_variable }}",
            variables={
                "wrong_variable": {"first_name": "John", "last_name": "Doe", "age": 30}
            },
        )
