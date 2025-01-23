from pydantic import BaseModel, Field

from promptsite.decorator import tracker
from promptsite.model.variable import (
    ArrayVariable,
    BooleanVariable,
    NumberVariable,
    ObjectVariable,
    StringVariable,
)


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
        == 'This is a test prompt version A dataset formatted as a list of JSON objects that conforms to the JSON schema below.\n{"properties": {"age": {"description": "Age in years.", "title": "Age", "type": "integer"}, "first_name": {"description": "The person\'s first name.", "title": "First Name", "type": "string"}, "last_name": {"description": "The person\'s last name.", "title": "Last Name", "type": "string"}}, "required": ["first_name", "last_name", "age"], "title": "TestModel", "type": "object"}\n\nThe actual dataset is: \n[{"age": 30, "first_name": "John", "last_name": "Doe"}, {"age": 25, "first_name": "Jane", "last_name": "Doe"}]\n'
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
        == 'This is a test prompt version A dataset formatted as a list of JSON objects that conforms to the JSON schema below.\n{"properties": {"age": {"description": "Age in years.", "title": "Age", "type": "integer"}, "first_name": {"description": "The person\'s first name.", "title": "First Name", "type": "string"}, "last_name": {"description": "The person\'s last name.", "title": "Last Name", "type": "string"}}, "required": ["first_name", "last_name", "age"], "title": "TestModel", "type": "object"}\n\nThe actual dataset is: \n[{"age": 30, "first_name": "John", "last_name": "Doe"}, {"age": 25, "first_name": "Jane", "last_name": "Doe"}]\n'
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
    _run = promptsite.get_last_run("test_prompt")
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
        == 'This is a test prompt version Schema: {"properties": {"age": {"description": "Age in years.", "title": "Age", "type": "integer"}, "first_name": {"description": "The person\'s first name.", "title": "First Name", "type": "string"}, "last_name": {"description": "The person\'s last name.", "title": "Last Name", "type": "string"}}, "required": ["first_name", "last_name", "age"], "title": "TestModel", "type": "object"}, Dataset: The actual dataset is: \n[{"age": 30, "first_name": "John", "last_name": "Doe"}, {"age": 25, "first_name": "Jane", "last_name": "Doe"}]'
    )

    # Verify the last run
    _run = promptsite.get_last_run("test_prompt")
    assert (
        _run.final_prompt
        == 'This is a test prompt version Schema: {"properties": {"age": {"description": "Age in years.", "title": "Age", "type": "integer"}, "first_name": {"description": "The person\'s first name.", "title": "First Name", "type": "string"}, "last_name": {"description": "The person\'s last name.", "title": "Last Name", "type": "string"}}, "required": ["first_name", "last_name", "age"], "title": "TestModel", "type": "object"}, Dataset: The actual dataset is: \n[{"age": 30, "first_name": "John", "last_name": "Doe"}, {"age": 25, "first_name": "Jane", "last_name": "Doe"}]'
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
        == 'This is a new test prompt version A dataset formatted as a list of JSON objects that conforms to the JSON schema below.\n{"properties": {"age": {"description": "Age in years.", "title": "Age", "type": "integer"}, "first_name": {"description": "The person\'s first name.", "title": "First Name", "type": "string"}, "last_name": {"description": "The person\'s last name.", "title": "Last Name", "type": "string"}}, "required": ["first_name", "last_name", "age"], "title": "TestModel", "type": "object"}\n\nThe actual dataset is: \n[{"age": 35, "first_name": "Alice", "last_name": "Smith"}, {"age": 40, "first_name": "Bob", "last_name": "Jones"}]\n'
    )

    # Verify a new version is created
    version = promptsite.get_prompt("test_prompt").get_latest_version()
    assert version.content == "This is a new test prompt version {{ test_variable }}"

    # Verify the run was recorded
    _run = promptsite.get_last_run("test_prompt")
    assert (
        _run.final_prompt
        == 'This is a new test prompt version A dataset formatted as a list of JSON objects that conforms to the JSON schema below.\n{"properties": {"age": {"description": "Age in years.", "title": "Age", "type": "integer"}, "first_name": {"description": "The person\'s first name.", "title": "First Name", "type": "string"}, "last_name": {"description": "The person\'s last name.", "title": "Last Name", "type": "string"}}, "required": ["first_name", "last_name", "age"], "title": "TestModel", "type": "object"}\n\nThe actual dataset is: \n[{"age": 35, "first_name": "Alice", "last_name": "Smith"}, {"age": 40, "first_name": "Bob", "last_name": "Jones"}]\n'
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
        prompt_id="new_test_prompt_boolean",
        description="New Test prompt for decorator",
        tags=["test"],
        variables={"test_variable": BooleanVariable()},
    )
    def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
        # Simulate LLM response
        return content

    response = mock_llm_call(
        content="This is a new test prompt version {{ test_variable }}",
        variables={"test_variable": True},
    )

    assert response == "This is a new test prompt version True"

    @tracker(
        prompt_id="new_test_prompt_string",
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
    prompt = promptsite.get_prompt("new_test_prompt_string")
    assert prompt.id == "new_test_prompt_string"
    assert prompt.description == "New Test prompt for decorator"
    assert prompt.tags == ["test"]
    assert prompt.variables["test_variable"].__class__ == StringVariable

    response = mock_llm_call(
        content="This is a new test prompt version {{ test_variable }}",
        variables={"test_variable": 123},
        variables_config={"test_variable": NumberVariable()},
    )

    version = promptsite.get_prompt("new_test_prompt_string").get_latest_version()
    assert version.variables["test_variable"].__class__ == NumberVariable

    
    @tracker(
        prompt_id="new_test_prompt_with_object_variable",
        description="New Test prompt for decorator",
        tags=["test"],
        variables={"test_variable": ObjectVariable(model=TestModel)},
    )
    def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
        # Simulate LLM response
        return content

    response = mock_llm_call(
        content="This is a new test prompt version {{ test_variable }}",
        variables={"test_variable": {"first_name": "John", "last_name": "Doe", "age": 30}},
    )

    assert response == 'This is a new test prompt version A dataset formatted as one JSON object that conforms to the JSON schema below.\n{"properties": {"age": {"description": "Age in years.", "title": "Age", "type": "integer"}, "first_name": {"description": "The person\'s first name.", "title": "First Name", "type": "string"}, "last_name": {"description": "The person\'s last name.", "title": "Last Name", "type": "string"}}, "required": ["first_name", "last_name", "age"], "title": "TestModel", "type": "object"}\n\nThe actual dataset is: \n{"age": 30, "first_name": "John", "last_name": "Doe"}\n'

    @tracker(
        prompt_id="new_test_prompt_with_output_variable",
        description="New Test prompt for decorator",
        tags=["test"],
        variables={"test_variable": ObjectVariable(model=TestModel, is_output=True)},
    )
    def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
        # Simulate LLM response
        return '{"first_name": "Alice", "last_name": "Smith", "age": 35}'

    response = mock_llm_call(
        content="Please return {{ test_variable }}"
    )

    assert response == {"first_name": "Alice", "last_name": "Smith", "age": 35} 

    prompt = promptsite.get_prompt("new_test_prompt_with_output_variable")
    _run = promptsite.get_last_run("new_test_prompt_with_output_variable")
    assert _run.final_prompt == 'Please return The output should be formatted as a JSON instance that conforms to the JSON schema below.\n\nAs an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}\nthe object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.\n\nHere is the output schema:\n```\n{"properties": {"age": {"description": "Age in years.", "title": "Age", "type": "integer"}, "first_name": {"description": "The person\'s first name.", "title": "First Name", "type": "string"}, "last_name": {"description": "The person\'s last name.", "title": "Last Name", "type": "string"}}, "required": ["first_name", "last_name", "age"], "title": "TestModel", "type": "object"}\n```\n'

    @tracker(
        prompt_id="new_test_prompt_without_variable",
        description="New Test prompt for decorator",
        tags=["test"]
    )
    def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
        # Simulate LLM response
        return content

    response = mock_llm_call(
        content="Please return {{ test_variable }}",
        variables={"test_variable": "Hello, World!"}
    )

    assert response == "Please return Hello, World!"

    @tracker(
        prompt_id="new_test_prompt_no_content",
        description="New Test prompt for decorator",
        content="This is a new test prompt version without content in the call",
    )
    def mock_llm_call(content=None, llm_config=None, variables=None, **kwargs):
        # Simulate LLM response
        return content
    
    response = mock_llm_call()

    assert response == "This is a new test prompt version without content in the call"
    
    