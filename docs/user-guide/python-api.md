# Python API Reference

This guide covers the core Python API for PromptSite, showing how to programmatically manage prompts, versions, and runs.

## Core API

### Initialization

Initialize PromptSite with either file storage (default) or Git storage:

```python
from promptsite import PromptSite
from promptsite.config import Config

# Default file storage
ps = PromptSite()

# Or with Git storage
config = Config()
config.save_config({
    "storage_backend": "git",
    "remote": "https://github.com/user/repo.git",
    "branch": "main"
})
ps = PromptSite(config.get_storage_backend())
```

### Managing Prompts

#### Register a New Prompt

```python
prompt = ps.register_prompt(
    prompt_id="translation-prompt",
    initial_content="Translate this text: {{ text }}",
    description="Basic translation prompt", 
    tags=["translation", "basic"]
)
```

#### Get Prompt Details

```python
prompt = ps.get_prompt("translation-prompt")
print(f"ID: {prompt.id}")
print(f"Description: {prompt.description}")
print(f"Tags: {prompt.tags}")
```

#### List All Prompts

```python
prompts = ps.list_prompts()
for prompt in prompts:
    print(f"Prompt ID: {prompt.id}")
```

#### Delete a Prompt

```python
ps.delete_prompt("translation-prompt")
```

### Managing Versions

#### Add a New Version

```python
new_version = ps.add_prompt_version(
    prompt_id="translation-prompt",
    content="Please translate to {{ language }}: {{ text }}"
)
```

#### Get Version Details

```python
version = ps.get_version("translation-prompt", version_id)
print(f"Content: {version.content}")
print(f"Created: {version.created_at}")
```

#### List All Versions

```python
versions = ps.list_versions("translation-prompt")
for version in versions:
    print(f"Version ID: {version.version_id}")
    print(f"Content: {version.content}")
```

#### Find Version by Content

```python
version = ps.get_version_by_content(
    prompt_id="translation-prompt",
    content="Please translate to {{ language }}: {{ text }}"
)
```

### Tracking Runs

#### Add a Run

```python
run = ps.add_run(
    prompt_id="translation-prompt",
    version_id=version_id,
    llm_output="Hola mundo",
    execution_time=0.5,
    llm_config={
        "model": "gpt-4",
        "temperature": 0.7
    },
    variables={
        "language": "Spanish",
        "text": "Hello world"
    },
    final_prompt="Please translate to Spanish: Hello world"
)
```

#### List Runs for a Version

```python
runs = ps.list_runs(
    prompt_id="translation-prompt",
    version_id=version_id
)
for run in runs:
    print(f"Run ID: {run.run_id}")
    print(f"Output: {run.llm_output}")
    print(f"Execution Time: {run.execution_time}s")
```
#### Get Run Details

```python
run = ps.get_run(
    prompt_id="translation-prompt",
    run_id=run_id
)
print(f"Run ID: {run.run_id}")
print(f"Output: {run.llm_output}")
print(f"Execution Time: {run.execution_time}s")
```

#### Get Last Run

```python
run = ps.get_last_run(
    prompt_id="translation-prompt"
)
print(f"Run ID: {run.run_id}")
print(f"Output: {run.llm_output}")
print(f"Execution Time: {run.execution_time}s")
```  

### Use Query API

PromptSite supports a query API to get prompts, versions and runs.

#### Get All Prompts

```python
prompts = ps.prompts.all()
```

#### Get All Versions for a Prompt

```python
versions = ps.versions.where(prompt_id="translation-prompt").all()
```

#### Get All Runs for a Prompt

```python
runs = ps.runs.where(prompt_id="translation-prompt").all()
```


#### Get All Runs for a Version

```python
runs = ps.runs.where(prompt_id="translation-prompt", version_id="translation-prompt-1").all()
```

#### Limit the columns returned

```python
runs = ps.runs.where(prompt_id="translation-prompt", version_id="translation-prompt-1").only(["run_id", "llm_output", "execution_time"]).all()
```

#### Get the prompt as a dictionary

```python
prompt = ps.prompts.where(prompt_id="translation-prompt").one()
```

#### Get the versions as a dataframe

```python
versions = ps.versions.where(prompt_id="translation-prompt").as_df()
```

#### Get the runs as a dataframe

```python
runs = ps.runs.where(prompt_id="translation-prompt").as_df()
```


### Using Variables

PromptSite supports both simple and complex variable types:

#### Simple Variables

```python
from promptsite.model.variable import SingleVariable

prompt = ps.register_prompt(
    prompt_id="simple-prompt",
    initial_content="Hello {{ name }}!",
    variables={
        "name": SingleVariable()
    }
)
```

#### Complex Variables with Pydantic Models

```python
from pydantic import BaseModel, Field
from promptsite.model.variable import ComplexVariable

class Person(BaseModel):
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    age: int = Field(description="Age in years")

prompt = ps.register_prompt(
    prompt_id="complex-prompt",
    initial_content="Generate profile for: {{ person }}",
    variables={
        "person": ComplexVariable(model=Person)
    }
)
```

### Git Integration

When using Git storage backend, you can sync with the remote repository using `ps.sync_git()`.

```python
# Sync with remote repository
ps.sync_git()
```

The API uses custom exceptions for error handling:

```python
from promptsite.exceptions import (
    PromptNotFoundError,
    PromptAlreadyExistsError,
    InvalidPromptContentError,
    StorageError
)

try:
    prompt = ps.get_prompt("nonexistent-prompt")
except PromptNotFoundError:
    print("Prompt not found")
except StorageError as e:
    print(f"Storage error: {str(e)}")
```


## Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks to handle potential errors
2. **Run Tracking**: Include comprehensive metadata in run tracking for better analysis
3. **Git Storage**: Regularly sync with remote when using Git storage backend
4. **Variable Validation**: Use Pydantic models for complex variable validation

## Next Steps

- Learn about the [CLI Interface](cli.md)
- Explore [Variable Definitions](variable-definitions.md)
- Check out [Decorator Usage](decorator.md)