# Decorator Usage

The `@tracker` decorator provides a simple way to automatically track prompt executions in your existing LLM code. This guide covers how to use the decorator effectively.

## Basic Usage

The most basic usage of the decorator requires only a prompt ID:

```python
from promptsite.decorator import tracker

@tracker(prompt_id="my-prompt")
def call_llm(content=None, llm_config=None, variables=None):
    # Your LLM call logic here
    return response
```

## Full Configuration

The decorator supports several configuration options:

```python
from promptsite.model.variable import ArrayVariable
from pydantic import BaseModel, Field

class Weather(BaseModel):
    date: str = Field(description="The date of the weather data")
    temperature: float = Field(description="The temperature in Celsius")
    condition: str = Field(description="The weather condition (sunny, rainy, etc)")

@tracker(
    prompt_id="weather-prompt",
    description="Weather prompt with structured data",
    tags=["weather", "weather-analysis"],
    ps_config={"storage_backend": "git"},
    llm_config={"temperature": 0.7},
    variables={
        "weather": ArrayVariable(Weather)  # Pydantic model 
    }
)
def translate_text(content=None, llm_config=None, variables=None):
    # LLM call implementation
    pass
```

## Variable Validation

The decorator supports Pydantic models for variable validation. 

## Automatic Run Tracking

The decorator automatically tracks:
- Execution time
- LLM configuration
- Input variables
- Final prompt
- LLM output

Example tracked run data:

```python:tests/test_decorator.py
startLine: 58
endLine: 65
```

## Configuration Options

The `@tracker` decorator accepts the following parameters:

- `prompt_id` (str, required): Unique identifier for the prompt
- `content` (str, optional): Default content for the prompt
- `description` (str, optional): Description of the prompt
- `tags` (List[str], optional): Tags for categorizing the prompt
- `ps_config` (Dict, optional): PromptSite configuration
- `ps` (PromptSite, optional): Existing PromptSite instance
- `llm_config` (Dict, optional): Default LLM configuration
- `variables` (Dict, optional): Variable definitions using Pydantic models

## Working with Variables

The decorator supports both simple and complex variable types:

### Simple Variables

```python
from promptsite.model.variable import StringVariable

@tracker(
    prompt_id="simple-prompt",
    variables={
        "text": StringVariable()
    }
)
def process_text(content=None, **kwargs):
    return llm_call(content)
```

### Complex Variables

```python
from pydantic import BaseModel, Field

class Weather(BaseModel):
    date: str = Field(description="The date of the weather data")
    temperature: float = Field(description="The temperature in Celsius")
    condition: str = Field(description="The weather condition (sunny, rainy, etc)")

@tracker(
    prompt_id="complex-prompt",
    variables={
        "weather": ArrayVariable(model=Weather)
    }
)
def process_weather(content=None, **kwargs):
    return llm_call(content)
```

## Disable Validation

The decorator supports disabling validation of variables. It is useful when you have validated the variables in the prompt, it can reduce the run time of the decorated function.

```python
@tracker(
    prompt_id="my-prompt-with-disable-validation",
    variables={
        "weather": ArrayVariable(model=Weather, disable_validation=True)  # Disable validation of the variable
    }
)
def my_function(content=None, **kwargs):
    return llm_call(content)

my_function(
    content="This is a test", 
    variables={"weather": [{"date": "2021-01-01", "temperature": 20, "condition": "sunny"}]}
)
```

## Disable Tracking

The decorator supports disabling tracking of runs. It is useful when you want to call the LLM repeatly with the same content, i.e. in production.

```python
@tracker(
    prompt_id="my-prompt",
    disable_tracking=True
)
def my_function(content=None, **kwargs):
    pass    

my_function()
```

## Error Handling

The decorator will raise appropriate exceptions for:
- Missing required variables
- Invalid variable types
- Configuration errors
- Storage backend issues

Example error handling:

```python
try:
    @tracker(prompt_id="my-prompt")
    def my_function(content=None, **kwargs):
        pass
except ConfigError as e:
    print(f"Configuration error: {e}")
except PromptNotFoundError as e:
    print(f"Prompt not found: {e}")
```

## Best Practices

1. **Variable Validation**: Always define Pydantic models for complex variables to ensure proper validation

2. **Error Handling**: Implement proper error handling for potential exceptions

3. **Define PromptSite Instance**: Pass the PromptSite instance to the decorator to use the same instance for all decorators, this is useful when you want to use the same PromptSite instance to do other operations (i.e. get prompt, get version, get run, etc.)

## Next Steps

- Learn about [Variable Definitions](variable-definitions.md)
- Explore the [Python API](python-api.md)
- Check out [CLI Usage](cli.md)
```