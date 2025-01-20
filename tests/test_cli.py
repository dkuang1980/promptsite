from datetime import datetime

import pytest
from click.testing import CliRunner

from promptsite.cli import cli
from promptsite.core import PromptSite
from promptsite.exceptions import PromptNotFoundError, PromptSiteError


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_ps(mocker):
    """Create a mocked PromptSite instance."""
    return mocker.Mock(spec=PromptSite)


def test_prompt_register(runner, mock_ps, mocker):
    """Test registering a new prompt via CLI."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    result = runner.invoke(
        cli,
        [
            "prompt",
            "register",
            "test-prompt",
            "--content",
            "Test content",
            "--description",
            "Test description",
            "-t",
            "tag1",
            "-t",
            "tag2",
        ],
    )

    assert result.exit_code == 0
    mock_ps.register_prompt.assert_called_once_with(
        prompt_id="test-prompt",
        initial_content="Test content",
        description="Test description",
        tags=["tag1", "tag2"],
    )


def test_prompt_list(runner, mock_ps, mocker):
    """Test listing all prompts."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    # Mock the list_prompts response
    mock_ps.list_prompts.return_value = [
        mocker.Mock(
            id="prompt1",
            description="Description 1",
            tags=["tag1"],
            versions={"v1": mocker.Mock(content="Content 1")},
        ),
        mocker.Mock(
            id="prompt2",
            description="Description 2",
            tags=["tag2"],
            versions={"v1": mocker.Mock(content="Content 2")},
        ),
    ]

    result = runner.invoke(cli, ["prompt", "list"])

    assert result.exit_code == 0
    assert "prompt1" in result.output
    assert "prompt2" in result.output


def test_prompt_get(runner, mock_ps, mocker):
    """Test getting a specific prompt."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    # Mock the get_prompt response
    mock_prompt = mocker.Mock(
        id="test-prompt",
        description="Test description",
        tags=["tag1", "tag2"],
        versions={
            "v1": mocker.Mock(content="Test content", created_at="2024-01-01T00:00:00")
        },
    )
    mock_ps.get_prompt.return_value = mock_prompt

    result = runner.invoke(cli, ["prompt", "get", "test-prompt"])

    assert result.exit_code == 0
    assert "test-prompt" in result.output
    assert "Test description" in result.output


def test_prompt_get_not_found(runner, mock_ps, mocker):
    """Test getting a non-existent prompt."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)
    mock_ps.get_prompt.side_effect = PromptNotFoundError("Prompt not found")

    result = runner.invoke(cli, ["prompt", "get", "nonexistent"])

    assert result.exit_code == 0
    assert "Error: Prompt not found" in result.output


def test_version_add(runner, mock_ps, mocker):
    """Test adding a new version to a prompt."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    mock_version = mocker.Mock(version_id="v1")
    mock_ps.add_prompt_version.return_value = mock_version

    result = runner.invoke(
        cli, ["version", "add", "test-prompt", "--content", "New version content"]
    )

    assert result.exit_code == 0
    mock_ps.add_prompt_version.assert_called_once_with(
        "test-prompt", "New version content"
    )


def test_version_get(runner, mock_ps, mocker):
    """Test getting a specific version of a prompt."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    mock_version = mocker.Mock(
        content="Version content",
        created_at="2024-01-01T00:00:00",
        version_id="v1",
        parent_version=None,
        runs=[],
    )
    mock_ps.get_version.return_value = mock_version

    result = runner.invoke(cli, ["version", "get", "test-prompt", "v1"])

    assert result.exit_code == 0
    assert "Version content" in result.output
    mock_ps.get_version.assert_called_once_with("test-prompt", "v1")


def test_version_list(runner, mock_ps, mocker):
    """Test listing all versions of a prompt."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    mock_versions = {
        "v1": mocker.Mock(
            version_id="v1", content="Content 1", created_at=datetime(2024, 1, 1)
        ),
        "v2": mocker.Mock(
            version_id="v2", content="Content 2", created_at=datetime(2024, 1, 2)
        ),
    }
    mock_ps.list_versions.return_value = mock_versions

    result = runner.invoke(cli, ["version", "list", "test-prompt"])
    assert result.exit_code == 0
    assert "v1" in result.output
    assert "v2" in result.output
    mock_ps.list_versions.assert_called_once_with("test-prompt")


def test_prompt_delete(runner, mock_ps, mocker):
    """Test deleting a prompt."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    result = runner.invoke(cli, ["prompt", "delete", "test-prompt", "--force"])

    assert result.exit_code == 0
    mock_ps.delete_prompt.assert_called_once_with("test-prompt")


def test_prompt_delete_not_found(runner, mock_ps, mocker):
    """Test deleting a non-existent prompt."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)
    mock_ps.delete_prompt.side_effect = PromptNotFoundError("Prompt not found")

    result = runner.invoke(cli, ["prompt", "delete", "nonexistent", "--force"])

    assert result.exit_code == 1
    assert "Error: Prompt not found" in result.output
    mock_ps.delete_prompt.assert_called_once_with("nonexistent")


def test_prompt_delete_without_force(runner, mock_ps, mocker):
    """Test deleting a prompt without --force flag."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    result = runner.invoke(cli, ["prompt", "delete", "test-prompt"])

    assert result.exit_code == 1
    assert "Are you sure" in result.output
    mock_ps.delete_prompt.assert_not_called()


def test_run_list(runner, mock_ps, mocker):
    """Test listing runs for a prompt version."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    mock_runs = [
        mocker.Mock(
            run_id="run1",
            final_prompt="Final prompt 1",
            llm_output="Output 1",
            created_at=datetime(2024, 1, 1),
            execution_time=1.5,
            variables={"var1": "val1"},
        ),
        mocker.Mock(
            run_id="run2",
            final_prompt="Final prompt 2",
            llm_output="Output 2",
            created_at=datetime(2024, 1, 2),
            execution_time=2.0,
            variables={"var2": "val2"},
        ),
    ]
    mock_ps.list_runs.return_value = mock_runs

    result = runner.invoke(cli, ["run", "list", "test-prompt", "v1"])

    assert result.exit_code == 0
    assert "run1" in result.output
    assert "run2" in result.output
    mock_ps.list_runs.assert_called_once_with("test-prompt", "v1")


def test_run_get(runner, mock_ps, mocker):
    """Test getting details of a specific run."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    mock_run = mocker.Mock(
        run_id="test-run",
        final_prompt="Final prompt",
        llm_output="LLM output",
        created_at=datetime(2024, 1, 1),
        execution_time=1.5,
        variables={"var1": "val1"},
        llm_config={"temp": 0.7},
    )
    mock_ps.get_run.return_value = mock_run

    result = runner.invoke(cli, ["run", "get", "test-prompt", "v1", "test-run"])

    assert result.exit_code == 0
    assert "test-run" in result.output
    assert "Final prompt" in result.output
    assert "LLM output" in result.output
    assert "Variables" in result.output
    assert "LLM config" in result.output
    mock_ps.get_run.assert_called_once_with("test-prompt", "v1", "test-run")


def test_run_get_not_found(runner, mock_ps, mocker):
    """Test getting a non-existent run."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)
    mock_ps.get_run.side_effect = PromptSiteError("Run not found")

    result = runner.invoke(cli, ["run", "get", "test-prompt", "v1", "nonexistent"])

    assert result.exit_code == 0
    assert "Error: Run not found" in result.output
    mock_ps.get_run.assert_called_once_with("test-prompt", "v1", "nonexistent")


def test_last_run(runner, mock_ps, mocker):
    """Test getting the last run for a prompt."""
    mocker.patch("promptsite.cli.get_promptsite", return_value=mock_ps)

    mock_run = mocker.Mock(
        run_id="test-run",
        created_at="2024-01-01T00:00:00",
        execution_time=1.5,
        final_prompt="Final prompt",
        llm_output="LLM output",
        variables=None,
        llm_config=None,
    )
    mock_ps.get_last_run.return_value = mock_run

    result = runner.invoke(cli, ["prompt", "last-run", "test-prompt"])

    assert result.exit_code == 0
    assert "test-run" in result.output
