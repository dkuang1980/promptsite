import pytest


@pytest.fixture
def query_ps(promptsite):
    """Create a PromptSite instance with some test data."""
    # Create prompts
    promptsite.register_prompt("prompt1", "Test Prompt 1", tags=["test"])
    promptsite.register_prompt("prompt2", "Test Prompt 2", tags=["test"])

    # Add versions
    p1_v1 = promptsite.add_prompt_version("prompt1", "content1-v2")
    p1_v2 = promptsite.add_prompt_version("prompt1", "content2-v2")
    p2_v1 = promptsite.add_prompt_version("prompt2", "content2-v1")

    # Add runs
    promptsite.add_run(
        "prompt1", p1_v1.version_id, "final prompt 1", llm_output="output1"
    )
    promptsite.add_run(
        "prompt1", p1_v2.version_id, "final prompt 2", llm_output="output2"
    )
    promptsite.add_run(
        "prompt2", p2_v1.version_id, "final prompt 3", llm_output="output3"
    )

    return promptsite


def test_prompt_query_all(query_ps):
    """Test retrieving all prompts."""
    prompts_df = query_ps.prompts.as_df()
    assert len(prompts_df) == 2
    assert set(prompts_df["id"]) == {"prompt1", "prompt2"}


def test_prompt_query_only(query_ps):
    """Test retrieving specific columns from prompts."""
    prompts_df = query_ps.prompts.only(["id", "description"]).as_df()
    assert set(prompts_df.columns) == {"id", "description"}


def test_version_query_all(query_ps):
    """Test retrieving all versions."""
    versions_df = query_ps.versions.as_df()
    assert len(versions_df) == 3
    assert set(versions_df["prompt_id"]) == {"prompt1", "prompt2"}


def test_version_query_where(query_ps):
    """Test filtering versions by prompt_id."""
    versions_df = query_ps.versions.where("prompt1").as_df()
    assert len(versions_df) == 2
    assert all(versions_df["prompt_id"] == "prompt1")


def test_version_query_only(query_ps):
    """Test retrieving specific columns from versions."""
    versions_df = query_ps.versions.only(["version_id", "content", "prompt_id"]).as_df()
    assert set(versions_df.columns) == {"version_id", "content", "prompt_id"}


def test_run_query_all(query_ps):
    """Test retrieving all runs."""
    runs_df = query_ps.runs.as_df()
    assert len(runs_df) == 3
    assert set(runs_df.columns) == {
        "prompt_id",
        "created_at",
        "version_id",
        "llm_config",
        "run_id",
        "run_at",
        "execution_time",
        "final_prompt",
        "llm_output",
        "variables",
    }


def test_prompt_query_one(query_ps):
    """Test retrieving one prompt."""
    prompt = query_ps.prompts.where(prompt_id="prompt1").one()
    assert prompt["id"] == "prompt1"


def test_run_query_where_prompt(query_ps):
    """Test filtering runs by prompt_id."""
    runs_df = query_ps.runs.where("prompt1").as_df()
    assert len(runs_df) == 2
    assert all(runs_df["prompt_id"] == "prompt1")


def test_run_query_where_prompt_and_version(query_ps):
    """Test filtering runs by prompt_id and version_id."""
    version = query_ps.versions.where("prompt1").all()[0]
    runs_df = query_ps.runs.where("prompt1", version["version_id"]).as_df()
    assert len(runs_df) == 1
    assert runs_df.iloc[0]["prompt_id"] == "prompt1"
    assert runs_df.iloc[0]["version_id"] == version["version_id"]


def test_run_query_only(query_ps):
    """Test retrieving specific columns from runs."""
    runs_df = query_ps.runs.only(["llm_output"]).as_df()
    assert set(runs_df.columns) == {"llm_output"}


def test_empty_queries(promptsite):
    """Test queries on empty PromptSite."""
    assert len(promptsite.prompts.as_df()) == 0
    assert len(promptsite.versions.as_df()) == 0
    assert len(promptsite.runs.as_df()) == 0
