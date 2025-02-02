# PromptSite

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

## Quick Start

### Installation

```bash
pip install promptsite
```

### Basic Usage

```python
from promptsite import PromptSite

# Initialize PromptSite
ps = PromptSite()

# Register a new prompt
prompt = ps.register_prompt(
    prompt_id="translation-prompt",
    initial_content="Translate this text: {{ text }}",
    description="Basic translation prompt",
    tags=["translation", "basic"]
)

# Add a new version
new_version = ps.add_prompt_version(
    prompt_id="translation-prompt", 
    new_content="Please translate the following text to {{ language }}: {{ text }}"
)

# Track an LLM run
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
    final_prompt="Please translate the following text to Spanish: {{ text }}"
)
```

### Using the Decorator to automatically track prompt versions and runs

```python
from promptsite.decorator import tracker
from pydantic import BaseModel, Field
from promptsite.model.variable import ArrayVariable
from promptsite.model.dataset import Dataset
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
content = """The following dataset describes the weather for each day:
{{ weather }}

Based on the weather data, predict which day is best for a picnic.
"""

# pass in existing data
data = [
    {"date": "2024-01-01", "temperature": 20, "condition": "sunny"},
    {"date": "2024-01-02", "temperature": 15, "condition": "rainy"},
    {"date": "2024-01-03", "temperature": 25, "condition": "sunny"}
]

# Or generate weather data using your own LLM backend
weather_data = Dataset.generate(
    id="weather_data",
    variable=ArrayVariable(model=Weather),
    description="Weather with some variety",
    num_rows=7
)
data = weather_data.data

analyze_weather(content=content, variables={"weather": data})
```

### CLI Usage

Initialize storage:

```bash
promptsite init
```

Register a new prompt:

```bash
promptsite prompt register my-prompt --content "Translate this text: {{ text }}" --description "Translation prompt" --tags translation gpt
```

List all prompts:

```bash
promptsite prompt list
```

Add a new version:

```bash
promptsite version add my-prompt --content "Please translate the following text: {{ text }}"
```

View version history:

```bash
promptsite version list my-prompt
```

## Contributing

We welcome contributions! Please check out our [contribution guidelines](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```