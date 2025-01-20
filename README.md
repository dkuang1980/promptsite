# PromptSite


## Overview

*You will never miss a prompt version again with PromptSite.*

PromptSite is a powerful prompt lifecycle management package that helps you version control, track, experiment and debug with your LLM prompts with ease. It mostly focuses on the experiemental and prototyping phase before shipping to production. The main features are:

- **Version Control**: Track versions during prompt engineering
- **Flexible Storage**: Choose between local file storage or Git-based storage
- **Run Tracking**: Automatically track and analyze prompt executions
- **CLI Interface**: Comprehensive command-line tools for prompt management
- **Python Decorator**: Simple integration with existing LLM code
- **Variable Management**: Manage and validate variables for prompts

## Key Differentiators
- **Focused on Experimentation**: Optimized for rapid prompt iteration, debugging, and experimentation during development
- **No Heavy Lifting**: Minimal setup, no servers, databases, or API keys required - works directly with your local filesystem or Git
- **Seamless Integration**: Automatically tracks prompt versions and runs through simple Python decorators
- **Developer-Centric**: Designed for data scientists and engineers to easily integrate into existing ML/LLM workflows


Checkout the [documentation](https://dkuang1980.github.io/promptsite/).

## Installation

```bash
pip install promptsite
```

## Quick Start

### Use PromptSite API

```python
from promptsite import PromptSite

# Initialize PromptSite with the defile storage
ps = PromptSite()

# Register a new prompt
prompt = ps.register_prompt(
    prompt_id="translation-prompt",
    description="Basic translation prompt",
    tags=["translation", "basic"]
)

```

## Python APIs

Besides using the decorator, you can directly use PromptSite's core functionality in your Python code:

```python
from promptsite import PromptSite
from promptsite.config import Config
from promptsite.variables import StringVariable

# you can use either file or git storage
ps = PromptSite()

# Initialize PromptSite with git storage
# config = Config()
# config.save_config({"storage_backend": "git", "remote": "https://github.com/user/repo.git"})
# ps = PromptSite(config.get_storage_backend())

# Register a new prompt
prompt = ps.register_prompt(
    prompt_id="translation-prompt",
    initial_content="Translate this text: {{text}}",
    description="Basic translation prompt",
    tags=["translation", "basic"],
    variables={
        "text": StringVariable(description="The text to translate")
    }
)

# Add a new version
new_version = ps.add_prompt_version(
    prompt_id="translation-prompt",
    content="Please translate the following text to {{language}}: {{text}}",
    variables={
        "language": StringVariable(description="The language to translate to"),
        "text": StringVariable(description="The text to translate")
    }
)

# Get prompt and version information
prompt = ps.get_prompt("translation-prompt")

# List all versions
all_versions = ps.list_versions("translation-prompt")

# Add an LLM run
run = ps.add_run(
    prompt_id="translation-prompt",
    version_id=active_version.version_id,
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
    final_prompt="Please translate the following text to Spanish: Hello world"
)

# Find a specific version by content
version = ps.get_version_by_content(
    prompt_id="translation-prompt",
    content="Please translate the following text to {{language}}: {{text}}"
)

# List all runs
runs = ps.list_runs("translation-prompt")

# Get a specific run
run = ps.get_run("translation-prompt", run_id="some_run_id")
```

## Prompt Auto tracking 

You can use the decorator to auto track your prompt in your LLM calls.

```python
from promptsite.decorator import tracker
from pydantic import BaseModel, Field
from promptsite.variables import ArrayVariable

class Weather(BaseModel):
    date: str = Field(description="The date of the weather data.")
    temperature: float = Field(description="The temperature in Celsius.")
    condition: str = Field(description="The weather condition (sunny, rainy, etc).")

@tracker(
    prompt_id="analyze-weather-prompt",
    description="Analyze weather data and predict which day is best for a picnic",
    tags=["weather", "analysis"],
    variables={
        "weather": ArrayVariable(model=Weather)
    }
)
def analyze_weather(content=None, llm_config=None, variables=None):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": content}]
    )
    return response.choices[0].message.content

# Run the function
response = analyze_weather(content="""The following dataset describes the weather for each day:
{{ weather }}

Based on the weather data, predict which day is best for a picnic.
""")

```

## CLI Commands

### Storage Backend Setup

#### File Storage (Default)
Initialize PromptSite with the defaultfile storage:

```bash
promptsite init
```

#### Git Storage
Initialize with Git storage and remote repository:

```bash
promptsite init --config '{"storage_backend": "git", "remote": "https://github.com/user/repo.git", "branch": "main", "auto_sync": true}'
```

### Prompt Management

1. Register a new prompt:
```bash
promptsite prompt register my-prompt --content "Translate this text: {{text}}" --description "Translation prompt" --tags translation gpt
```

2. List all prompts:
```bash
promptsite prompt list
```

3. Add a new version:
```bash
promptsite version add my-prompt --content "Please translate the following text: {{text}}"
```

4. View version history:
```bash
promptsite version list my-prompt
```

5. Get a specific version:
```bash
promptsite version get my-prompt <version-id>
```

6. View run history:
```bash
promptsite run list my-prompt
```

7. Get a specific run:
```bash
promptsite run get my-prompt <run-id>
```

8. Get the last run:
```bash
promptsite run last-run my-prompt
```

8. Sync with Git remote (if using Git storage):
```bash
promptsite sync-git
```

For more detailed documentation and examples, visit our [documentation](https://dkuang1980.github.io/promptsite/).