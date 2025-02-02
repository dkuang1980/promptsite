# Synthetic Datasets

The Dataset class in PromptSite provides functionality for managing and generating structured data that can be used in your prompts.

## Basic Usage

### Creating a Dataset

To create a dataset, you need to define a Pydantic model for your data structure and use either `ArrayVariable` or `ObjectVariable`:

```python
from pydantic import BaseModel, Field
from promptsite.model.dataset import Dataset
from promptsite.model.variable import ArrayVariable

class CustomerModel(BaseModel):
    id: int = Field(description="The id of the customer")
    name: str = Field(description="The name of the customer")
    age: int = Field(description="The age of the customer")
    gender: str = Field(description="The gender of the customer")

# Create a dataset with existing data
customers = Dataset(
    id="customers",
    variable=ArrayVariable(model=CustomerModel),
    data=[
        {"id": 1, "name": "John", "age": 25, "gender": "Male"},
        {"id": 2, "name": "Jane", "age": 22, "gender": "Female"}
    ],
    description="Customer dataset"
)
```

### Working with Related Datasets

You can create relationships between datasets using field references:

```python
class OrderModel(BaseModel):
    id: int = Field(description="The id of the order")
    customer_id: int = Field(description="The id of the customer")
    amount: float = Field(description="The amount of the order")

orders = Dataset(
    id="orders",
    variable=ArrayVariable(model=OrderModel),
    data=[
        {"id": 1, "customer_id": 1, "amount": 100},
        {"id": 2, "customer_id": 2, "amount": 200}
    ],
    description="Order dataset",
    relationships={
        "customer_id": customers["id"] # Establish relationship with customers dataset
    }
)
```

### Converting to DataFrame

You can easily convert a dataset to a pandas DataFrame:

```python
df = customers.to_df()
```

## Generating Data

PromptSite provides powerful data generation capabilities using LLMs. You can generate data that matches your schema and requirements:


### Configure your LLM backend

```python
from promptsite.config import Config

config = Config()
config.save_config({"llm_backend": "openai", "llm_config": {"model": "gpt-4o-mini"}})

```
### Simple Dataset Generation

```python
from promptsite.model.dataset import Dataset
from promptsite.model.variable import ArrayVariable

class CustomerModel(BaseModel):
    id: int = Field(description="The id of the customer")
    name: str = Field(description="The name of the customer")
    age: int = Field(description="The age of the customer")
    gender: str = Field(description="The gender of the customer")

customers = Dataset.generate(
    id="customers_between_20_and_30",
    variable=ArrayVariable(model=CustomerModel, description="The customers for product A"),
    description="Customers between 20 and 30 years old"
)
```

### Generating relatioanal Dataset

You can generate data with relationships with existing datasets:

```python
class OrderModel(BaseModel):
    id: int = Field(description="The id of the order")
    customer_id: int = Field(description="The id of the customer")
    amount: float = Field(description="The amount of the order")

orders = Dataset.generate(
    id="orders_below_100",
    variable=ArrayVariable(model=OrderModel, description="orders"),
    description="Orders below 100 dollars",
    relationships={"customer_id": customers["id"]} # Maintain relationship with "customers" dataset
)
```
### Controlling Generation Size

You can specify the number of rows to generate:

```python
customers = Dataset.generate(
    id="female_customers",
    variable=ArrayVariable(model=CustomerModel),
    description="Female customers",
    num_rows=5 # Generate exactly 5 customers
)
```
