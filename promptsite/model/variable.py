import io
import json
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Any, Dict

from datamodel_code_generator import generate
from pydantic import *  # noqa F403
from pydantic import BaseModel


class Variable:
    def validate(self, value: str) -> bool:
        """Validate if the given value matches the variable type.

        Args:
            value (str): The value to validate

        Returns:
            bool: True if value is valid for this variable type, False otherwise

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses
        """
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Convert the variable instance to a dictionary representation.

        Returns:
            Dict[str, Any]: A dictionary containing the variable type information
        """
        return {"type": self.__class__.__name__}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Variable":
        """Create a Variable instance from a dictionary representation.

        Args:
            data (Dict[str, Any]): Dictionary containing variable configuration

        Returns:
            Variable: A new instance of the appropriate Variable subclass
        """
        klass = globals()[data["type"]]
        if klass == cls:
            return cls()
        return klass.from_dict(data)

    def __eq__(self, other: "Variable") -> bool:
        """Compare this variable instance with another for equality.

        Args:
            other (Variable): Another Variable instance to compare with

        Returns:
            bool: True if the variables are of the same type and have the same configuration,
                 False otherwise
        """
        if not isinstance(other, Variable):
            return False
        return self.to_dict() == other.to_dict()


class SingleVariable(Variable):
    """Base class for simple variable types that don't require complex validation or transformation."""

    pass

    def to_json(self, value: Any) -> str:
        """Convert a value to its JSON string representation.

        Args:
            value (Any): The value to convert to JSON

        Returns:
            str: The JSON string representation of the value
        """
        return value


@dataclass
class ComplexVariable(Variable):
    """Complex variable type that uses Pydantic models for validation and schema handling.

    This class handles structured data that needs to conform to a specific schema defined
    by a Pydantic model.

    Attributes:
        model (BaseModel): The Pydantic model used for validation and schema generation
    """

    model: BaseModel
    is_output: bool = False

    @property
    def schema_instructions(self) -> str:
        if self.is_output:
            return self._output_schema_instructions
        return self._input_schema_instructions

    def to_json(self, value: Any) -> str:
        """Convert a complex value to its JSON string representation.

        Args:
            value (Any): The value to convert to JSON

        Returns:
            str: The JSON string representation of the value
        """
        return json.dumps(value)

    def get_prompt_insert(self, value: Any, custom_instructions: str = "") -> str:
        """Generate a formatted prompt string with schema and dataset information.

        Args:
            value (Any): The dataset value to include in the prompt
            custom_instructions (str, optional): Custom instructions template to use.
                                               Defaults to schema_instructions.

        Returns:
            str: Formatted prompt string containing schema and dataset information
        """
        instructions = (
            custom_instructions if custom_instructions else self.schema_instructions
        )

        return instructions.format(
            schema=self.model.model_json_schema(),
            dataset="The actual dataset is: \n" + json.dumps(value)
            if not self.is_output
            else "",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the complex variable instance to a dictionary representation.

        Returns:
            Dict[str, Any]: A dictionary containing the variable type, model class name,
                           and model schema information
        """
        return {
            "type": self.__class__.__name__,
            "model_class": self.model.__name__,
            "model": self.model.model_json_schema(),
            "is_output": self.is_output,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComplexVariable":
        """Create a ComplexVariable instance from a dictionary representation.

        Args:
            data (Dict[str, Any]): Dictionary containing variable configuration including
                                  model schema information

        Returns:
            ComplexVariable: A new instance of ComplexVariable with the reconstructed
                           Pydantic model
        """
        f = io.StringIO()
        with redirect_stdout(f):
            generate(input_=json.dumps(data["model"]), input_file_type="jsonschema")
        exec(f.getvalue())
        cls = globals()[data["type"]]
        model = eval(data["model_class"])
        model.model_rebuild()
        return cls(model=model, is_output=data.get("is_output", False))


class StringVariable(SingleVariable):
    """Variable type for string values.

    Validates that values are Python string instances.
    """

    def validate(self, value: str) -> bool:
        """Validate if the given value is a string.

        Args:
            value (str): The value to validate

        Returns:
            bool: True if value is a string instance, False otherwise
        """
        return isinstance(value, str)


class NumberVariable(Variable):
    """Variable type for numeric values.

    Validates that values are Python integer instances.
    """

    def validate(self, value: str) -> bool:
        """Validate if the given value is an integer.

        Args:
            value (str): The value to validate

        Returns:
            bool: True if value is an integer instance, False otherwise
        """
        return isinstance(value, int)


class BooleanVariable(Variable):
    """Variable type for boolean values.

    Validates that values are Python boolean instances.
    """

    def validate(self, value: str) -> bool:
        """Validate if the given value is a boolean.

        Args:
            value (str): The value to validate

        Returns:
            bool: True if value is a boolean instance, False otherwise
        """
        return isinstance(value, bool)


class ArrayVariable(ComplexVariable):
    """Variable type for array/list values that conform to a Pydantic model schema.

    Validates that values are Python lists where each item conforms to the specified
    Pydantic model schema.

    Attributes:
        schema_instructions (str): Template for formatting schema and dataset information
    """

    _input_schema_instructions = """A dataset formatted as a list of JSON objects that conforms to the JSON schema below.
{schema}

{dataset}
"""

    _output_schema_instructions = """The output should be formatted as a list of a JSON instances that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{schema}
```
"""

    def validate(self, value: Any) -> bool:
        """Validate if the given value is a list conforming to the model schema.

        Args:
            value (Any): The value to validate

        Returns:
            bool: True if value is a list and all items conform to the model schema,
                 False otherwise
        """
        if not isinstance(value, list):
            return False
        for item in value:
            if not self.model.model_validate(item):
                return False
        return True


class ObjectVariable(ComplexVariable):
    """Variable type for object/dict values that conform to a Pydantic model schema.

    Validates that values are Python dictionaries that conform to the specified
    Pydantic model schema.

    Attributes:
        schema_instructions (str): Template for formatting schema and dataset information
    """

    _input_schema_instructions = """A dataset formatted as one JSON object that conforms to the JSON schema below.
{schema}

{dataset}
"""
    _output_schema_instructions = """The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{schema}
```
"""

    def validate(self, value: Any) -> bool:
        """Validate if the given value is a dict conforming to the model schema.

        Args:
            value (Any): The value to validate

        Returns:
            bool: True if value is a dict and conforms to the model schema,
                 False otherwise
        """
        if not isinstance(value, dict):
            return False
        if not self.model.model_validate(value):
            return False
        return True
