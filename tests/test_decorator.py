from pydantic import BaseModel, Field

from promptsite.decorator import tracker
from promptsite.model.variable import ArrayVariable, StringVariable


def test_decorator(promptsite):
    class TestModel(BaseModel):
        first_name: str = Field(description="The person's first name.")
        last_name: str = Field(description="The person's last name.")
        age: int = Field(description="Age in years.")

    # Mock LLM function that would normally call an actual LLM
    @tracker(
        prompt_id="test_prompt",
        description="Test prompt for decorator",
        tags=["test"],
        ps_config={"storage_backend": "file"},
        variables={"test_variable": ArrayVariable(model=TestModel)},
    )
    def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
        # Simulate LLM response
        return content

    # Call the decorated function
    response = mock_llm_call(
        content="This is a test prompt version {{ test_variable }}",
        llm_config={"temperature": 0.7},
        variables={
            "test_variable": [
                {"first_name": "John", "last_name": "Doe", "age": 30},
                {"first_name": "Jane", "last_name": "Doe", "age": 25},
            ]
        },
    )
    assert (
        response
        == "This is a test prompt version A dataset formatted as a list of JSON objects that conforms to the JSON schema below.\n{'properties': {'first_name': {'description': \"The person's first name.\", 'title': 'First Name', 'type': 'string'}, 'last_name': {'description': \"The person's last name.\", 'title': 'Last Name', 'type': 'string'}, 'age': {'description': 'Age in years.', 'title': 'Age', 'type': 'integer'}}, 'required': ['first_name', 'last_name', 'age'], 'title': 'TestModel', 'type': 'object'}\n\nThe actual dataset is: \n[{\"first_name\": \"John\", \"last_name\": \"Doe\", \"age\": 30}, {\"first_name\": \"Jane\", \"last_name\": \"Doe\", \"age\": 25}]\n"
    )

    # Verify prompt was registered
    prompt = promptsite.get_prompt("test_prompt")
    assert prompt.id == "test_prompt"
    assert prompt.description == "Test prompt for decorator"
    assert prompt.tags == ["test"]

    # Verify version was created
    version = promptsite.get_prompt("test_prompt").get_latest_version()
    assert version.content == "This is a test prompt version {{ test_variable }}"

    # Verify run was recorded
    _run = promptsite.list_runs("test_prompt", version.version_id)[0]
    assert (
        _run.final_prompt
        == "This is a test prompt version A dataset formatted as a list of JSON objects that conforms to the JSON schema below.\n{'properties': {'first_name': {'description': \"The person's first name.\", 'title': 'First Name', 'type': 'string'}, 'last_name': {'description': \"The person's last name.\", 'title': 'Last Name', 'type': 'string'}, 'age': {'description': 'Age in years.', 'title': 'Age', 'type': 'integer'}}, 'required': ['first_name', 'last_name', 'age'], 'title': 'TestModel', 'type': 'object'}\n\nThe actual dataset is: \n[{\"first_name\": \"John\", \"last_name\": \"Doe\", \"age\": 30}, {\"first_name\": \"Jane\", \"last_name\": \"Doe\", \"age\": 25}]\n"
    )
    assert _run.llm_config == {"temperature": 0.7}
    assert _run.execution_time is not None
    assert _run.variables == {
        "test_variable": [
            {"first_name": "John", "last_name": "Doe", "age": 30},
            {"first_name": "Jane", "last_name": "Doe", "age": 25},
        ]
    }

    response = mock_llm_call(
        content="This is a test prompt version {{ test_variable }}",
        llm_config={"temperature": 0.8},
        no_instructions=True,
        variables={
            "test_variable": [
                {"first_name": "John", "last_name": "Doe", "age": 30},
                {"first_name": "Jane", "last_name": "Doe", "age": 25},
            ]
        },
    )
    assert (
        response
        == 'This is a test prompt version [{"first_name": "John", "last_name": "Doe", "age": 30}, {"first_name": "Jane", "last_name": "Doe", "age": 25}]'
    )

    # Verify the last run
    _run = sorted(
        promptsite.list_runs("test_prompt", version.version_id),
        key=lambda x: x.created_at,
    )[-1]
    assert (
        _run.final_prompt
        == 'This is a test prompt version [{"first_name": "John", "last_name": "Doe", "age": 30}, {"first_name": "Jane", "last_name": "Doe", "age": 25}]'
    )
    assert _run.llm_config == {"temperature": 0.8}
    assert _run.execution_time is not None
    assert _run.variables == {
        "test_variable": [
            {"first_name": "John", "last_name": "Doe", "age": 30},
            {"first_name": "Jane", "last_name": "Doe", "age": 25},
        ]
    }

    response = mock_llm_call(
        content="This is a test prompt version {{ test_variable }}",
        llm_config={"temperature": 0.9},
        custom_instructions="Schema: {schema}, Dataset: {dataset}",
        variables={
            "test_variable": [
                {"first_name": "John", "last_name": "Doe", "age": 30},
                {"first_name": "Jane", "last_name": "Doe", "age": 25},
            ]
        },
    )
    assert (
        response
        == "This is a test prompt version Schema: {'properties': {'first_name': {'description': \"The person's first name.\", 'title': 'First Name', 'type': 'string'}, 'last_name': {'description': \"The person's last name.\", 'title': 'Last Name', 'type': 'string'}, 'age': {'description': 'Age in years.', 'title': 'Age', 'type': 'integer'}}, 'required': ['first_name', 'last_name', 'age'], 'title': 'TestModel', 'type': 'object'}, Dataset: The actual dataset is: \n[{\"first_name\": \"John\", \"last_name\": \"Doe\", \"age\": 30}, {\"first_name\": \"Jane\", \"last_name\": \"Doe\", \"age\": 25}]"
    )

    # Verify the last run
    _run = sorted(
        promptsite.list_runs("test_prompt", version.version_id),
        key=lambda x: x.created_at,
    )[-1]
    assert (
        _run.final_prompt
        == "This is a test prompt version Schema: {'properties': {'first_name': {'description': \"The person's first name.\", 'title': 'First Name', 'type': 'string'}, 'last_name': {'description': \"The person's last name.\", 'title': 'Last Name', 'type': 'string'}, 'age': {'description': 'Age in years.', 'title': 'Age', 'type': 'integer'}}, 'required': ['first_name', 'last_name', 'age'], 'title': 'TestModel', 'type': 'object'}, Dataset: The actual dataset is: \n[{\"first_name\": \"John\", \"last_name\": \"Doe\", \"age\": 30}, {\"first_name\": \"Jane\", \"last_name\": \"Doe\", \"age\": 25}]"
    )
    assert _run.llm_config == {"temperature": 0.9}
    assert _run.execution_time is not None
    assert _run.variables == {
        "test_variable": [
            {"first_name": "John", "last_name": "Doe", "age": 30},
            {"first_name": "Jane", "last_name": "Doe", "age": 25},
        ]
    }

    response = mock_llm_call(
        content="This is a new test prompt version {{ test_variable }}",
        llm_config={"temperature": 0},
        variables={
            "test_variable": [
                {"first_name": "Alice", "last_name": "Smith", "age": 35},
                {"first_name": "Bob", "last_name": "Jones", "age": 40},
            ]
        },
    )

    assert (
        response
        == "This is a new test prompt version A dataset formatted as a list of JSON objects that conforms to the JSON schema below.\n{'properties': {'age': {'description': 'Age in years.', 'title': 'Age', 'type': 'integer'}, 'first_name': {'description': \"The person's first name.\", 'title': 'First Name', 'type': 'string'}, 'last_name': {'description': \"The person's last name.\", 'title': 'Last Name', 'type': 'string'}}, 'required': ['age', 'first_name', 'last_name'], 'title': 'TestModel', 'type': 'object'}\n\nThe actual dataset is: \n[{\"first_name\": \"Alice\", \"last_name\": \"Smith\", \"age\": 35}, {\"first_name\": \"Bob\", \"last_name\": \"Jones\", \"age\": 40}]\n"
    )

    # Verify a new version is created
    version = promptsite.get_prompt("test_prompt").get_latest_version()
    assert version.content == "This is a new test prompt version {{ test_variable }}"

    # Verify the run was recorded
    _run = sorted(
        promptsite.list_runs("test_prompt", version.version_id),
        key=lambda x: x.created_at,
    )[-1]
    assert (
        _run.final_prompt
        == "This is a new test prompt version A dataset formatted as a list of JSON objects that conforms to the JSON schema below.\n{'properties': {'age': {'description': 'Age in years.', 'title': 'Age', 'type': 'integer'}, 'first_name': {'description': \"The person's first name.\", 'title': 'First Name', 'type': 'string'}, 'last_name': {'description': \"The person's last name.\", 'title': 'Last Name', 'type': 'string'}}, 'required': ['age', 'first_name', 'last_name'], 'title': 'TestModel', 'type': 'object'}\n\nThe actual dataset is: \n[{\"first_name\": \"Alice\", \"last_name\": \"Smith\", \"age\": 35}, {\"first_name\": \"Bob\", \"last_name\": \"Jones\", \"age\": 40}]\n"
    )
    assert _run.llm_config == {"temperature": 0}
    assert _run.execution_time is not None
    assert _run.variables == {
        "test_variable": [
            {"first_name": "Alice", "last_name": "Smith", "age": 35},
            {"first_name": "Bob", "last_name": "Jones", "age": 40},
        ]
    }

    @tracker(
        prompt_id="new_test_prompt",
        description="New Test prompt for decorator",
        tags=["test"],
        variables={"test_variable": StringVariable()},
    )
    def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
        # Simulate LLM response
        return content

    response = mock_llm_call(
        content="This is a new test prompt version {{ test_variable }}",
        variables={"test_variable": "Hello, World!"},
    )

    assert response == "This is a new test prompt version Hello, World!"

    # verify a new prompt created
    prompt = promptsite.get_prompt("new_test_prompt")
    assert prompt.id == "new_test_prompt"
    assert prompt.description == "New Test prompt for decorator"
    assert prompt.tags == ["test"]
    assert prompt.variables["test_variable"].__class__ == StringVariable
