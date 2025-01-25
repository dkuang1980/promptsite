# Quick Start Guide

This guide will help you get started with PromptSite by walking through the basic functionality.

## Installation

First, install PromptSite using pip:

```bash
pip install promptsite
```

## Basic Usage

### Initialize PromptSite

The first step is to initialize PromptSite. You can use either the file storage (default) or Git storage backend:

```python
from promptsite import PromptSite

# Initialize with default file storage
ps = PromptSite()
```

### Managing Prompts

#### Register a New Prompt

```python
prompt = ps.register_prompt(
    prompt_id="translation-prompt",
    initial_content="Translate this text: {{ text }}",
    description="Basic translation prompt",
    tags=["translation", "basic"],
    variables={
        "text": StringVariable(description="The text to translate.")
    }
)
```

#### Add New Versions

```python
new_version = ps.add_prompt_version(
    prompt_id="translation-prompt",
    content="Please translate the following text to {{ language }}: {{ text }}",
    variables={
        "text": StringVariable(description="The text to translate."),
        "language": StringVariable(description="The language to translate to.")
    }
)
```

#### Track LLM Runs

```python
run = ps.add_run(
    prompt_id="translation-prompt",
    version_id=new_version.version_id,
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
```

## Using the Decorator to automatically track LLM runs

PromptSite provides a decorator for easy integration with your existing LLM code:

```python
from promptsite.decorator import tracker
from pydantic import BaseModel, Field
from promptsite.model.variable import ArrayVariable

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
analyze_weather(content="""The following dataset describes the weather for each day:
{{ weather }}

Based on the weather data, predict which day is best for a picnic.
""")
```

## Using the CLI

PromptSite provides a comprehensive CLI for managing prompts:

### Initialize Storage

```bash
promptsite init
```

For Git storage:

```bash
promptsite init --config '{"storage_backend": "git", "remote": "https://github.com/user/repo.git", "branch": "main"}'
```

### Basic PromptCommands

Register a new prompt:
```bash
promptsite prompt register my-prompt --content "Translate this text: {{{text}}}" --description "Translation prompt" --tags translation gpt
```

List all prompts:
```bash
promptsite prompt list
```

Add a new version:
```bash
promptsite version add my-prompt --content "Please translate the following text: {{{text}}}"
```

View version history:
```bash
promptsite version list my-prompt
```

## Next Steps

- Learn more about [Configuration](../user-guide/configuration.md)
- Explore different [Storage Backends](../user-guide/storage-backends.md)
- Check out the complete [CLI Usage Guide](../user-guide/cli.md)
- Read about [Variable Definitions](../user-guide/variable-definitions.md)
