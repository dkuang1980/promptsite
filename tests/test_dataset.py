import pytest
from pydantic import BaseModel, Field

from promptsite.exceptions import DatasetFieldNotFoundError
from promptsite.model.dataset import Dataset
from promptsite.model.variable import ArrayVariable, ObjectVariable


# Test models
class CustomerModel(BaseModel):
    id: int = Field(description="The id of the customer")
    name: str = Field(description="The name of the customer")
    age: int = Field(description="The age of the customer")
    gender: str = Field(description="The gender of the customer")


class OrderModel(BaseModel):
    id: int = Field(description="The id of the order")
    customer_id: int = Field(description="The id of the customer")
    amount: float = Field(description="The amount of the order")


@pytest.fixture
def customer_data():
    return [
        {"id": 1, "name": "John", "age": 25, "gender": "Male"},
        {"id": 2, "name": "Jane", "age": 22, "gender": "Female"},
    ]


@pytest.fixture
def order_data():
    return [
        {"id": 1, "customer_id": 1, "amount": 100},
        {"id": 2, "customer_id": 2, "amount": 200},
    ]


@pytest.fixture
def customers_dataset(customer_data):
    return Dataset(
        id="customers",
        variable=ArrayVariable(model=CustomerModel),
        data=customer_data,
        description="Test customers",
    )


@pytest.fixture
def orders_dataset(order_data, customers_dataset):
    return Dataset(
        id="orders",
        variable=ArrayVariable(model=OrderModel),
        data=order_data,
        description="Test orders",
        relationships={"customer_id": customers_dataset["id"]},
    )


@pytest.fixture
def mock_llm(mocker):
    mock = mocker.Mock()
    mock.run.return_value = ""
    return mock


def test_dataset_initialization(customers_dataset):
    assert customers_dataset.id == "customers"
    assert isinstance(customers_dataset.variable, ArrayVariable)
    assert len(customers_dataset.data) == 2
    assert customers_dataset.description == "Test customers"


def test_dataset_getitem(customers_dataset):
    field_info = customers_dataset["id"]
    assert field_info["field"] == "id"
    assert field_info["dataset"] == customers_dataset


def test_dataset_getitem_invalid_field(customers_dataset):
    with pytest.raises(DatasetFieldNotFoundError):
        customers_dataset["invalid_field"]


def test_dataset_to_df(customers_dataset):
    df = customers_dataset.to_df()
    assert len(df) == 2
    assert list(df.columns) == ["id", "name", "age", "gender"]


def test_dataset_validate_valid_data(customers_dataset):
    assert customers_dataset.validate() is True


def test_dataset_validate_invalid_data():
    invalid_data = [
        {"id": "not_an_int", "name": "John", "age": 25, "gender": "Male"}
    ]  # id should be int
    dataset = Dataset(
        id="invalid_customers",
        variable=ArrayVariable(model=CustomerModel),
        data=invalid_data,
    )
    assert dataset.validate() is False


def test_dataset_with_relationships(orders_dataset):
    assert orders_dataset.relationships is not None
    assert "customer_id" in orders_dataset.relationships
    relationship = orders_dataset.relationships["customer_id"]
    assert relationship["field"] == "id"
    assert relationship["dataset"].id == "customers"


def test_object_variable_dataset():
    class SingleCustomerModel(BaseModel):
        id: int
        name: str

    single_customer = Dataset(
        id="single_customer",
        variable=ObjectVariable(model=SingleCustomerModel),
        data={"id": 1, "name": "John"},
    )

    assert single_customer.validate() is True
    df = single_customer.to_df()
    assert len(df) == 1


def test_generate_single_dataset(config, mock_llm, mocker):
    mock_llm.run.return_value = """```json
        [
            {"id": 1, "name": "John", "age": 25, "gender": "Male"},
            {"id": 2, "name": "Jane", "age": 22, "gender": "Female"}
        ]
    ```"""
    mocker.patch("promptsite.config.Config.get_llm_backend", return_value=mock_llm)

    dataset = Dataset.generate(
        id="customers",
        variable=ArrayVariable(model=CustomerModel, description="customers"),
        description="customers between 20 and 30 years old",
    )

    assert dataset.validate() is True
    assert dataset.data == [
        {"id": 1, "name": "John", "age": 25, "gender": "Male"},
        {"id": 2, "name": "Jane", "age": 22, "gender": "Female"},
    ]

    assert (
        mock_llm.run.call_args[0][0]
        == 'You are a data expert who can generates data that satisfies the DATA DESCRIPTION, the DATA REQUIREMENT and the OUTPUT SCHEMA.\n\n\nDATA DESCRIPTION:\ncustomers\n\n\n\n\nDATA REQUIREMENT: \ncustomers between 20 and 30 years old\n\n\nOUTPUT SCHEMA:\nThe output should be formatted as a list of  JSON instances that conforms to the JSON schema below. Please only output the JSON , nothing else in the output.\n\n                          \nAs an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}\nthe object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.\n\nHere is the instance schema in the output:\n```\n{"properties": {"id": {"description": "The id of the customer", "title": "Id", "type": "integer"}, "name": {"description": "The name of the customer", "title": "Name", "type": "string"}, "age": {"description": "The age of the customer", "title": "Age", "type": "integer"}, "gender": {"description": "The gender of the customer", "title": "Gender", "type": "string"}}, "required": ["id", "name", "age", "gender"], "title": "CustomerModel", "type": "object"}\n```\n\nHere is an example of the output:\n```\n[{"foo": ["bar", "baz"]}, {"foo": ["bar", "baz"]}]\n```'
    )


def test_generate_dataset_with_relationships(config, mock_llm, mocker):
    mock_llm.run.return_value = """```json
        [
            {"id": 1, "name": "John", "age": 25, "gender": "Male"},
            {"id": 2, "name": "Jane", "age": 22, "gender": "Female"}
        ]
    ```"""
    mocker.patch("promptsite.config.Config.get_llm_backend", return_value=mock_llm)

    customers = Dataset.generate(
        id="customers_between_20_and_30",
        variable=ArrayVariable(model=CustomerModel, description="customers"),
        description="customers between 20 and 30 years old",
    )

    mock_llm.run.return_value = """```json
        [
            {"id": 1, "customer_id": 1, "amount": 92},
            {"id": 2, "customer_id": 2, "amount": 50}
        ]
    ```"""

    orders = Dataset.generate(
        id="orders_below_100_dollars",
        variable=ArrayVariable(model=OrderModel, description="orders"),
        description="orders below 100 dollars for customers between 20 and 30 years old",
        relationships={"customer_id": customers["id"]},
    )

    assert orders.validate() is True
    assert orders.data == [
        {"id": 1, "customer_id": 1, "amount": 92},
        {"id": 2, "customer_id": 2, "amount": 50},
    ]
    assert (
        mock_llm.run.call_args[0][0]
        == 'You are a data expert who can generates data that satisfies the DATA DESCRIPTION, the DATA REQUIREMENT and the OUTPUT SCHEMA, given the EXTRA DATASETS.\n\n\nDATA DESCRIPTION:\norders\n\n\n\nEXTRA DATASETS:\n\n- DATASET "customers_between_20_and_30":\n    * SCHEMA:\n    {\'properties\': {\'id\': {\'description\': \'The id of the customer\', \'title\': \'Id\', \'type\': \'integer\'}, \'name\': {\'description\': \'The name of the customer\', \'title\': \'Name\', \'type\': \'string\'}, \'age\': {\'description\': \'The age of the customer\', \'title\': \'Age\', \'type\': \'integer\'}, \'gender\': {\'description\': \'The gender of the customer\', \'title\': \'Gender\', \'type\': \'string\'}}, \'required\': [\'id\', \'name\', \'age\', \'gender\'], \'title\': \'CustomerModel\', \'type\': \'object\'}\n    * DATASET:\n    [{\'id\': 1, \'name\': \'John\', \'age\': 25, \'gender\': \'Male\'}, {\'id\': 2, \'name\': \'Jane\', \'age\': 22, \'gender\': \'Female\'}]\n\n\n\nDATA REQUIREMENT: \norders below 100 dollars for customers between 20 and 30 years old\n\n\n- Make sure "customer_id" field matches "id" field in the DATASET "customers_between_20_and_30"\n\n\n\nOUTPUT SCHEMA:\nThe output should be formatted as a list of  JSON instances that conforms to the JSON schema below. Please only output the JSON , nothing else in the output.\n\n                          \nAs an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}\nthe object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.\n\nHere is the instance schema in the output:\n```\n{"properties": {"id": {"description": "The id of the order", "title": "Id", "type": "integer"}, "customer_id": {"description": "The id of the customer", "title": "Customer Id", "type": "integer"}, "amount": {"description": "The amount of the order", "title": "Amount", "type": "number"}}, "required": ["id", "customer_id", "amount"], "title": "OrderModel", "type": "object"}\n```\n\nHere is an example of the output:\n```\n[{"foo": ["bar", "baz"]}, {"foo": ["bar", "baz"]}]\n```'
    )
