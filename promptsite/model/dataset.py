import pandas as pd
from typing import Dict, Any, TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from promptsite.model.variable import Variable
from promptsite.config import Config
from jinja2 import Template
import json
from promptsite.exceptions import DatasetFieldNotFoundError

class Dataset:
    """Class for dataset model.
    
    Args:
        id: The id of the dataset.
        variable: The Variable object of the dataset.
        data: The actual data of the dataset.
        description: The description of the dataset.
        relationships: The relationships with other datasets.

    Usage:
        ```
        from pydantic import BaseModel
        from promptsite.model.variable import ArrayVariable

        class CustomerModel(BaseModel):
            id: int
            name: str
            created_at: datetime

        customers = Dataset(
            id="customers",
            variable=ArrayVariable(model=CustomerModel, description="customers"),
            data=[
                {"id": 1, "name": "John", "created_at": "2021-01-01"}, 
                {"id": 2, "name": "Jane", "created_at": "2021-01-02"}
            ],
            description="customers description"
        )

        class OrderModel(BaseModel):
            id: int
            customer_id: int
            product_id: int
            amount: float

        orders = Dataset(
            id="orders",
            variable=ArrayVariable(model=OrderModel, description="orders"),
            data=[
                {"id": 1, "customer_id": 1, "product_id": 1, "amount": 100},
                {"id": 2, "customer_id": 2, "product_id": 2, "amount": 200}
            ],
            description="orders description",
            relationships = {
                "customer_id": customers["id"]
            }
        )
        ```
    """
    def __init__(
        self,
        id: str,
        variable: "Variable",
        data: Any, 
        description: str = None,
        relationships: Dict[str, "Dataset"] = None
    ):
        self.id = id
        self.variable = variable
        self.data = data
        self.description = description  
        self.relationships = relationships

    def __getitem__(self, field: str):
        """Get an metadata of a field from the dataset when defining the relationships."""
        if field not in self.variable.model.model_fields:
            raise DatasetFieldNotFoundError(f"{field} is not a valid field for this dataset.")
        return {
            "field": field,
            "dataset": self
        }

    @classmethod
    def generate(
        cls,
        id: str,
        variable: "Variable",
        description: str = None,
        relationships: Dict[str, Callable] = None,
        num_rows: int = None
    ) -> "Dataset":
        """Generate the dataset.
        
        Args:
            id: The id of the dataset.
            variable: The Variable object of the dataset.
            description: The description of the dataset.
            relationships: The relationships with other datasets.
            num_rows: The number of rows to generate.
        """
        from promptsite.model.variable import ArrayVariable

        prompt = Template("""You are a data expert who can generates data that satisfies the{% if description %} DATA DESCRIPTION,{% endif %} the DATA REQUIREMENT and the OUTPUT SCHEMA{% if extra_datasets %}, given the EXTRA DATASETS{% endif %}.

{% if description %}
DATA DESCRIPTION:
{{ description }}
{% endif %}

{% if extra_datasets %}
EXTRA DATASETS:
{% for dataset in extra_datasets %}
- DATASET "{{ dataset.id }}":
    * SCHEMA:
    {{ dataset.variable.model.model_json_schema() }}
    * DATASET:
    {{ dataset.data }}
{% endfor %}
{% endif %}

DATA REQUIREMENT: 
{{ requirement }}
{% if relationships %}
{% for field, mapped in relationships.items() %}
- Make sure "{{ field }}" field matches "{{ mapped.field }}" field in the DATASET "{{ mapped.dataset.id }}"
{% endfor %}
{% endif %}

OUTPUT SCHEMA:
The output should be formatted as {{ json_instructions }} that conforms to the JSON schema below. Please only output the JSON , nothing else in the output.

                          
As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.

Here is the instance schema in the output:
```
{{ schema }}
```

Here is an example of the output:
```
[{"foo": ["bar", "baz"]}, {"foo": ["bar", "baz"]}]
```
""").render(
            requirement=description,
            extra_datasets=set([relationship["dataset"] for relationship in relationships.values()]) if relationships else None,
            relationships=relationships,
            description=variable.description,
            json_instructions=f"a list of {num_rows or ''} JSON instances" if isinstance(variable, ArrayVariable) else "a JSON instance",
            schema=json.dumps(variable.model.model_json_schema())
        ) 
        print(prompt)
        config = Config()
        llm = config.get_llm_backend()
        response = llm.run(prompt)
        
        try:
            data = json.loads(response.strip().replace("```json", "").replace("```", ""))
        except json.JSONDecodeError:
            data = response

        return Dataset(id, variable, data, description=description)

    def to_df(self) -> pd.DataFrame:
        """Convert the dataset to a pandas DataFrame.
        
        Returns:
            pd.DataFrame: The pandas DataFrame of the dataset.
        """
        if isinstance(self.data, list):
            return pd.DataFrame(self.data)
        else:
            return pd.DataFrame([self.data])

    def validate(self) -> bool:
        """Validate the dataset.
        
        Returns:
            bool: True if the dataset is valid according to the variable model, False otherwise.
        """
        return self.variable.validate(self.data)
