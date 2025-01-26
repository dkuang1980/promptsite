# PromptSite


## Overview

*You will never miss a prompt version again with PromptSite.*

PromptSite is a lightweight prompt management package that helps you version control, track, experiment and debug with your LLM prompts with ease. It mostly focuses on the experiemental and prototyping phase before shipping to production. The main features are:

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

The following example shows how to use the `@tracker` decorator to auto track your prompt in your LLM calls.

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


# prompt with variables
from promptsite.model.variable import ArrayVariable
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


customers = [
    {"user_id": "1", "name": "John Doe", "gender": "male", "product_name": "Product A",  "complaint": "The product is not good"},
    {"user_id": "2", "name": "Jane Doe", "gender": "female", "product_name": "Product B",  "complaint": "I need refund"},
]
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

For more detailed documentation and examples, visit our [documentation](https://dkuang1980.github.io/promptsite/).