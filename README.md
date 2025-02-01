# PromptSite

[![Test](https://github.com/dkuang1980/promptsite/actions/workflows/test.yml/badge.svg)](https://github.com/dkuang1980/promptsite/actions/workflows/test.yml)
[![Release](https://img.shields.io/github/release/dkuang1980/promptsite?style=flat-square)](https://github.com/dkuang1980/promptsite/releases)

## Overview

PromptSite is a lightweight prompt management package that helps you version control, develop, and experiment with your LLM prompts with ease. 

## Key Features
- **Version Control**: Track and manage different versions of your prompts during the engineering process
- **Flexible Storage**: Choose between local file storage or Git-based storage backends
- **Run Tracking**: Automatically track and analyze prompt executions and LLM responses  
- **Synthetic Data Generation**: Generate synthetic relational data to quickly test prompts
- **CLI Interface**: Comprehensive command-line tools for prompt management
- **Python Decorator**: Simple integration with existing LLM code through decorators
- **Variable Management**: Define, validate and manage variables used in prompts

## Key Differentiators 
- **No Heavy Lifting**: Minimal setup, no servers, databases, or API keys required - works directly with your local filesystem or Git
- **Seamless Integration**: Automatically tracks prompt versions and runs through simple Python decorators
- **Developer-Centric**: Designed for data scientists and engineers to easily integrate into existing ML/LLM workflows
- **Designed for Experimentation**: Optimized for rapid prompt iteration, debugging, and experimentation for LLM development


Checkout the [documentation](https://dkuang1980.github.io/promptsite/).

## Installation

```bash
pip install promptsite
```

## Quick Start with the Decorator

The following example shows how to use the `@tracker` decorator to auto track your prompt versions andruns in your LLM calls.

### Define LLM call function with the `@tracker` decorator

```python
import os
from openai import OpenAI
from promptsite.decorator import tracker
from pydantic import BaseModel, Field

os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

client = OpenAI()

# simple prompt
@tracker(
    prompt_id="email-writer"
)
def write_email(content=None, **kwargs):
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": content}]
    )
    return response.choices[0].message.content


# A complex prompt with variables
from promptsite.model.variable import ArrayVariable
from promptsite.model.dataset import Dataset
from pydantic import BaseModel, Field


class Customer(BaseModel):
    user_id: str = Field(description="The user id of the customer")
    name: str = Field(description="The name of the customer")
    gender: str = Field(description="The gender of the customer")
    product_name: str = Field(description="The name of the product")
    complaint: str = Field(description="The complaint of the customer")

class Email(BaseModel):
    user_id: str = Field(description="The user id of the customer")
    subject: str = Field(description="The subject of the email")
    body: str = Field(description="The body of the email")

@tracker(
    prompt_id="email-writer-to-customers",
    variables={
        "customers": ArrayVariable(model=Customer),
        "emails": ArrayVariable(model=Email, is_output=True)
    }
)
def write_email_to_customers(content=None, **kwargs):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": content}]
    )
    return response.choices[0].message.content
    
```

### Run the function with different versions of content

```python

# Run multiple times to see what LLM outputs
for i in range(3):
    write_email(content="Please write an email to apologize to a customer who had a bad experience with our product")

write_email(content="Please write an email to apologize to a customer who had a bad experience with our product and offer a discount")

write_email(content="Please write an email to apologize to a customer who had a bad experience with our product and give a refund")


# pass in existing data
customers = [
    {"user_id": "1", "name": "John Doe", "gender": "male", "product_name": "Product A",  "complaint": "The product is not good"},
    {"user_id": "2", "name": "Jane Doe", "gender": "female", "product_name": "Product B",  "complaint": "I need refund"},
]

# Or generate data using your own LLM backend
from promptsite.config import Config
config = Config()
config.save_config({"llm_backend": "openai", "llm_config": {"model": "gpt-4o-mini"}})

customers = Dataset.generate(
    id="customers_with_different_complaints",
    variable=ArrayVariable(model=Customer),
    description="Customers with different complaints",
    num_rows=10
).data

write_email_to_customers(
    content="""
    Based on the following CUSTOMERS dataset 
    
    CUSTOMERS:
    {{ customers }}

    Please write an email to apologize to each customer, and return the emails in the following format:

    {{ emails }}
""", 
    llm_config={"model": "gpt-4o-mini"},
    variables={"customers": customers}
)

```

### Check the data for the prompt, versions and runs

```python
from promptsite import PromptSite

ps = PromptSite()

# Get the prompt as a dictionary
simple_prompt = ps.prompts.where(prompt_id="email-writer").one()

# Get the versions as a list of dictionaries
simple_prompt_versions = ps.versions.where(prompt_id=simple_prompt["id"]).all()

# Get all the runs for the prompt as a pandas dataframe
simple_prompt_runs = ps.runs.where(prompt_id=simple_prompt["id"]).only(["run_id", "llm_config", "llm_output", "execution_time"]).as_df()

# Get the prompt as a dictionary
variable_prompt = ps.prompts.where(prompt_id="email-writer-to-customers").one()

# Get the versions as a list of dictionaries
variable_prompt_versions = ps.versions.where(prompt_id=variable_prompt["id"]).all()

# Get all the runs for the prompt as a pandas dataframe
variable_prompt_runs = ps.runs.where(prompt_id=variable_prompt["id"]).as_df()
```

## Python Core APIs

Besides using the decorator, you can directly use PromptSite's core functionality in your Python code:

```python
from promptsite import PromptSite
from promptsite.config import Config

# you can use either file or git storage
ps = PromptSite()


# Register a new prompt
prompt = ps.register_prompt(
    prompt_id="translation-prompt",
    initial_content="Translate this text to Spanish: Hi",
    description="Basic translation prompt",
    tags=["translation", "basic"]
)

# Add a new version
new_version = ps.add_prompt_version(
    prompt_id="translation-prompt",
    new_content="Please translate the following text to Spanish: Hello world",
)

# Get prompt and version information
prompt = ps.get_prompt("translation-prompt")

# List all versions
all_versions = ps.list_versions("translation-prompt")

# Add an LLM run
run = ps.add_run(
    prompt_id="translation-prompt",
    version_id=new_version.version_id,
    llm_output="Hola mundo",
    execution_time=0.5,
    llm_config={
        "model": "gpt-4",
        "temperature": 0.7
    },
    final_prompt="Please translate the following text to Spanish: Hello"
)

# List all runs
runs = ps.list_runs("translation-prompt", new_version.version_id)

# Get a specific run
run = ps.get_run("translation-prompt", version_id=new_version.version_id, run_id=runs[-1].run_id)
```

## CLI Commands

### Storage Backend Setup

#### File Storage (Default)
Initialize PromptSite with the defaultfile storage:

```bash
promptsite init
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

For more detailed documentation and examples, visit our [documentation](https://dkuang1980.github.io/promptsite/).
