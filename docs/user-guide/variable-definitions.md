# Variable Definitions

PromptSite provides a flexible system for defining and validating variables used in your prompts. This guide covers the different types of variables available and how to use them effectively.

## Variable Types

PromptSite supports several variable types to handle different kinds of inputs:

### Simple Variables

1. **StringVariable**: For text inputs
2. **NumberVariable**: For numeric values
3. **BooleanVariable**: For true/false values

### Complex Variables

1. **ArrayVariable**: For lists/arrays of values
2. **ObjectVariable**: For structured data using Pydantic models

## Using Variables in Code

### Simple Variable Example

```python
from promptsite import PromptSite
from promptsite.model.variable import StringVariable

ps = PromptSite()

# Register prompt with string variable
ps.register_prompt(
    prompt_id="greeting",
    initial_content="Hello {{ name }}!",
    variables={
        "name": StringVariable()
    }
)
```

### Complex Variable Example

```python
from promptsite.decorator import tracker
from pydantic import BaseModel, Field
from promptsite.model.variable import ArrayVariable

class Weather(BaseModel):
    date: str = Field(description="The date of the weather data.")
    temperature: float = Field(description="The temperature in Celsius.")
    condition: str = Field(description="The weather condition (sunny, rainy, etc).")

ps = PromptSite()

# Register prompt with complex variable
ps.register_prompt(
    prompt_id="weather-analysis",
    initial_content="Analyze the following weather data: {{ weather }}",
    variables={
        "weather": ArrayVariable(model=Weather)
    }
)
```

## Variable Validation

Variables are automatically validated when used in prompts. The validation ensures:

1. All required variables are provided
2. Values match their expected types
3. Complex objects conform to their Pydantic models

We validate the values of the variables in the decorator @tracker when the final prompt is built.

## Array Variables

Array variables are particularly useful for handling lists of structured data. They support Pydantic models as their item type:

```python
from promptsite.model.variable import ArrayVariable

ps.register_prompt(
    prompt_id="group-greeting",
    initial_content="Analyze the following weather data: {{ weather }}",
    variables={
        "weather": ArrayVariable(model=Weather)
    }
)
```

## Variable Schema Instructions

When using complex variables, PromptSite automatically generates schema instructions for the LLM. These instructions help the model understand the expected structure of the data.

For example, with an ArrayVariable:

```python
@tracker(
    prompt_id="group-greeting",
    description="Greeting for multiple people",
    variables={
        "people": ArrayVariable(Person)
    }
)
def greet_people(content=None, llm_config=None, variables=None):
    # The content will include schema instructions
    return llm_call(content)
```

## Output Variables

Output variables are variables that are returned by the LLM. To define an output variable, you need to set the `is_output` attribute to `True` in the variable definition.

```python
from promptsite.model.variable import ArrayVariable

class Weather(BaseModel):
    date: str = Field(description="The date of the weather data.")
    temperature: float = Field(description="The temperature in Celsius.")
    condition: str = Field(description="The weather condition (sunny, rainy, etc).")

class Prediction(BaseModel):
    date: str = Field(description="The date of the weather data.")
    temperature: float = Field(description="The temperature in Celsius.")
    condition: str = Field(description="The weather condition (sunny, rainy, etc).")

ps.register_prompt(
    prompt_id="weather-prediction",
    initial_content="Predict the weather for the next 7 days based on \n {{ last_week_weather }} \n\n {{ prediction }}",
    variables={
        "last_week_weather": ArrayVariable(Weather),
        "prediction": ArrayVariable(Prediction, is_output=True)
    }
)
```

## Storage Format

Variables are stored in YAML format along with their prompts and versions. Here's an example of how they're stored:

```yaml
version_id: v1
content: "Analyze the following weather data: {{ weather }}"
variables:
  weather:
    type: ComplexVariable
    model_class: Weather
    model:
      title: Weather
      type: object
      properties:
        date:
          type: string
          description: The date of the weather data
        temperature:
          type: number
          description: The temperature in Celsius
        condition:
          type: string
          description: The weather condition (sunny, rainy, etc)
      required:
        - date
        - temperature
        - condition
```

## Best Practices

1. **Type Safety**: Always use appropriate variable types to ensure data validation
2. **Documentation**: Include descriptions in your Pydantic models to help document the expected data
3. **Validation**: Take advantage of Pydantic's validation features for complex variables
4. **Reusability**: Define common variable models in a central location for reuse
5. **Schema Instructions**: Consider customizing schema instructions for complex variables when needed

## Variable Inheritance

Variables can be defined at both the prompt and version level:

1. Prompt-level variables are inherited by all versions
2. Version-level variables override prompt-level variables
3. Each version can define its own variable set

Example:

```python
# Define prompt with base variables
prompt = ps.register_prompt(
    prompt_id="greeting",
    initial_content="Hello {{ name }} !",
    variables={
        "name": StringVariable()
    }
)

# Add version with additional variable
version = ps.add_prompt_version(
    prompt_id="greeting",
    content="Hello {{ name }}  from {{ location }} !",
    variables={
        "name": StringVariable(),
        "location": StringVariable()
    }
)
```

## Next Steps

- Learn about [Python API](python-api.md) usage
- Explore [Decorator Usage](decorator.md) for tracking
- Check out [Configuration](configuration.md) options
```