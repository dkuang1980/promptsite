# Configuration

PromptSite provides flexible configuration options to customize its behavior according to your needs. This guide covers the available configuration options and how to set them.

## Configuration File

PromptSite uses a YAML configuration file located at `.promptsite/config.yaml`. This file is created automatically when you initialize PromptSite, but you can modify it manually or through the CLI.

## Storage Backend Configuration

So far, PromptSite supports two storage backends:

### File Storage (Default)

The file storage backend stores prompts and related data in your local filesystem. To use file storage:

```bash
promptsite init
```

Or explicitly specify file storage:

```bash
promptsite init --config '{"storage_backend": "file"}'
```

```python
from promptsite.config import Config
config = Config()
config.save_config({"storage_backend": "file"})
```

### Git Storage

The Git storage backend stores prompts in a Git repository, enabling version control and collaboration. To use Git storage:

```bash
promptsite init --config '{"storage_backend": "git", "remote": "https://github.com/user/repo.git", "branch": "main"}'
```

```python
from promptsite.config import Config
config = Config()
config.save_config({"storage_backend": "git", "remote": "https://github.com/user/repo.git", "branch": "main"})
```

Or explicitly specify Git storage:
Available Git configuration options:

- `storage_backend`: Set to "git"
- `remote`: URL of the Git remote repository
- `branch`: Git branch to use (defaults to "main")
- `auto_sync`: Whether to automatically sync with remote (defaults to false)

#### Auto Sync

If `auto_sync` is set to `true`, PromptSite will automatically sync with the remote repository when you make changes to the prompts. Otherwise, you need to manually sync with the remote repository using `ps.sync_git()` or run cli command`promptsite sync-git`.

```bash
promptsite init --config '{"storage_backend": "git", "remote": "https://github.com/user/repo.git", "branch": "main", "auto_sync": true}'
```

### LLM Backend Configuration

PromptSite supports multiple LLM backends. You can configure the LLM backend and its configuration in the configuration file.

The following example shows how to configure the OpenAI backend and its configuration.
```bash
promptsite init --config '{"llm_backend": "openai", "llm_config": {"model": "gpt-4o-mini"}}'
```

```python
from promptsite.config import Config
config = Config()
config.save_config({"llm_backend": "openai", "llm_config": {"model": "gpt-4o-mini"}})
```

The following example shows how to configure the Anthropic backend and its configuration.
```bash
promptsite init --config '{"llm_backend": "anthropic", "llm_config": {"model": "claude-3-5-sonnet-20240620"}}'
```

```python
from promptsite.config import Config
config = Config()
config.save_config({"llm_backend": "anthropic", "llm_config": {"model": "claude-3-5-sonnet-20240620"}})
```

The following example shows how to configure the Ollama backend and its configuration.
```bash
promptsite init --config '{"llm_backend": "ollama", "llm_config": {"model": "deepseek-r1:8b"}}'
```

```python
from promptsite.config import Config
config = Config()
config.save_config({"llm_backend": "ollama", "llm_config": {"model": "deepseek-r1:8b"}})
```


## Storage Structure

PromptSite organizes prompts in a clear directory structure:

```
.promptsite/
├── prompts/
│   ├── <prompt_id>/
│   │   ├── prompt.yaml        # Prompt metadata
│   │   └── versions/
│   │       ├── <version_id>/
│   │       │   ├── version.yaml   # Version data
│   │       │   └── runs/
│   │       │       └── <run_id>.yaml  # Run data
```

### YAML File Structures

#### prompt.yaml
This file stores the prompt's metadata:

```yaml
id: translation-prompt
description: A prompt for translating text between languages
tags: 
  - translation
  - multilingual
variables:
  text:
    type: SingleVariable
  language:
    type: SingleVariable
created_at: "2024-01-17T10:30:00Z"
```

#### version.yaml
This file contains data for a specific version of the prompt:

```yaml
version_id: v1_a1b2c3
content: "Please translate the following text to {{ language }}: {{ text }}"
created_at: "2024-01-17T10:30:00Z"
variables:
  text:
    type: SingleVariable
  language:
    type: SingleVariable
```

For versions with complex variables using Pydantic models:

```yaml
version_id: v2_x1y2z3
content: "Generate a greeting for this person: {{ person }}"
created_at: "2024-01-17T11:45:00Z"
variables:
  person:
    type: ComplexVariable
    model_class: Person
    model:
      title: Person
      type: object
      properties:
        first_name:
          type: string
          description: The person's first name
        last_name:
          type: string
          description: The person's last name
        age:
          type: integer
          description: Age in years
      required:
        - first_name
        - last_name
```

#### run.yaml
This file stores data from each execution of a prompt version:

```yaml
run_id: run_123abc
created_at: "2024-01-17T10:35:00Z"
run_at: "2024-01-17T10:35:02Z"
final_prompt: "Please translate the following text to Spanish: Hello world"
variables:
  language: Spanish
  text: Hello world
llm_output: "Hola mundo"
execution_time: 0.5
llm_config:
  model: gpt-4
  temperature: 0.7
  max_tokens: 100
```

For runs with complex variable inputs:

```yaml
run_id: run_456def
created_at: "2024-01-17T11:50:00Z"
run_at: "2024-01-17T11:50:03Z"
final_prompt: "Generate a greeting for this person: {\"first_name\": \"John\", \"last_name\": \"Doe\", \"age\": 30}"
variables:
  person:
    first_name: John
    last_name: Doe
    age: 30
llm_output: "Hello John Doe! How does it feel to be 30?"
execution_time: 0.8
llm_config:
  model: gpt-4
  temperature: 0.5
  max_tokens: 150
```

### Field Descriptions

#### prompt.yaml Fields
- `id`: Unique identifier for the prompt
- `description`: Human-readable description of the prompt's purpose
- `tags`: List of categorization tags
- `variables`: Dictionary of variable definitions used in the prompt
- `created_at`: Timestamp of prompt creation

#### version.yaml Fields
- `version_id`: Unique identifier for this version
- `content`: The actual prompt template with variable placeholders
- `created_at`: Timestamp of version creation
- `variables`: Dictionary of variable definitions specific to this version (inherits from prompt.yaml if not specified)

#### run.yaml Fields
- `run_id`: Unique identifier for this execution
- `created_at`: Timestamp when run record was created
- `run_at`: Timestamp of actual execution
- `final_prompt`: The fully rendered prompt with variables replaced
- `variables`: The actual values used for variables in this run
- `llm_output`: The response from the language model
- `execution_time`: Time taken in seconds
- `llm_config`: Configuration used for the language model

## Configuration Through Code

You can also configure PromptSite programmatically:

```python
from promptsite import PromptSite
from promptsite.config import Config

# Configure Git storage
config = Config()
config.save_config({
    "storage_backend": "git",
    "remote": "https://github.com/user/repo.git",
    "branch": "main",
    "auto_sync": True
})

# Initialize PromptSite with config
ps = PromptSite(config.get_storage_backend())
```

## Default Configuration

If no configuration is provided, PromptSite uses these defaults:

```yaml
storage_backend: file
base_directory: .promptsite
```

## Configuration Validation

PromptSite validates your configuration when initializing. Invalid configurations will raise a `ConfigError` with details about the issue.

Example error handling:

```python
from promptsite.exceptions import ConfigError

try:
    config = Config()
    config.save_config({
        "storage_backend": "invalid_backend"
    })
except ConfigError as e:
    print(f"Configuration error: {str(e)}")
```

## Best Practices

1. **Version Control**: When using Git storage, commit your `.promptsite/config.yaml` file to version control
2. **File Backend**: Use the File backend for fast development, it will get you started quickly
3. **Git Backend**: Use the Git backend when you need to collaborate with others, choose different `branch` to work on
4. **Backup**: Regularly backup your prompt data, especially when using file storage
5. **Documentation**: Document any custom configuration for team collaboration

## Next Steps

- Learn about [Storage Backends](storage-backends.md) in detail
- Explore [CLI Usage](cli.md) for managing prompts
- Check out [Python API](python-api.md) for programmatic control