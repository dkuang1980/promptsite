try:
    from datetime import UTC
except ImportError:
    from datetime import timezone as _timezone

    UTC = _timezone.utc

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from jinja2 import Template

from ..exceptions import VariableUnmatchError, VariableValidationError
from .run import Run
from .variable import Variable


@dataclass
class Version:
    """A class representing a version of a prompt with its associated runs.

    Attributes:
        content (str): The content of the version
        created_at (datetime): The date and time when the version was created
        version_id (str): The unique identifier for the version
        variables (Optional[Dict[str, Variable]]): The variables of the version, if any, it overrides the prompt variables
    """

    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version_id: str = None
    runs: Dict[str, Run] = field(default_factory=dict)
    variables: Optional[Dict[str, Variable]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the version_id if not provided."""
        if not self.version_id:
            self.version_id = self._generate_version_id(self.content)

    def _generate_version_id(self, content: str) -> str:
        """Generate a version ID based on the hash of the content.

        Args:
            content (str): The content of the version

        Returns:
            str: The generated version ID
        """
        timestamp = self.created_at.isoformat()
        content_with_timestamp = f"{content}{timestamp}"
        return hashlib.sha256(content_with_timestamp.encode()).hexdigest()[:8]

    def add_run(
        self,
        final_prompt: str,
        variables: Dict[str, Any],
        llm_output: Optional[str] = None,
        execution_time: Optional[float] = None,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> Run:
        """Create and add a new run to this version.

        Args:
            llm_output (Optional[str]): The output text from the LLM
            execution_time (Optional[float]): Time taken to execute in seconds
            llm_config (Optional[Dict[str, Any]]): Configuration used for the LLM

        Returns:
            Run: The newly created run
        """
        run = Run(
            final_prompt=final_prompt,
            variables=variables,
            llm_output=llm_output,
            execution_time=execution_time,
            llm_config=llm_config,
        )

        self.runs[run.run_id] = run
        return run

    def build_final_prompt(
        self,
        values: Dict[str, Any],
        no_instructions: bool = False,
        custom_instructions: Optional[str] = "",
    ) -> str:
        """Build the final prompt with the variables of the version.

        Args:
            values (Dict[str, Any]): The values of the variables

        Returns:
            str: The final prompt
        """
        template = Template(self.content)

        if self.variables:
            input_variables = [
                k
                for k, v in self.variables.items()
                if not getattr(v, "is_output", False)
            ]

            if set(input_variables) != set(values.keys()):
                raise VariableUnmatchError("The variables and the values do not match")

            for variable_name in input_variables:
                variable_type = self.variables[variable_name]
                if not variable_type.validate(values[variable_name]):
                    raise VariableValidationError(
                        f"The variable {variable_name} is not valid"
                    )

            prompt_inserts = {}
            for variable_name, variable_type in self.variables.items():
                has_prompt_insert = getattr(variable_type, "get_prompt_insert", False)
                if no_instructions or not has_prompt_insert:
                    prompt_inserts[variable_name] = variable_type.to_json(
                        values[variable_name]
                    )
                else:
                    prompt_inserts[variable_name] = variable_type.get_prompt_insert(
                        values.get(variable_name),
                        custom_instructions=custom_instructions,
                    )

            return template.render(**prompt_inserts)

        return template.render(**values)

    def compare_variables(self, variables: Dict[str, Variable]) -> bool:
        """Compare the variables of the version with the variables of the new version.

        Args:
            variables (Dict[str, Variable]): The variables of the new version

        Returns:
            bool: True if the variables are the same, False otherwise
        """
        my_variables = self.variables or {}
        new_variables = variables or {}
        if set([key for key in my_variables.keys()]) != set(
            [key for key in new_variables.keys()]
        ):
            return False

        for variable_name, variable in my_variables.items():
            if variable != new_variables[variable_name]:
                return False
        return True

    def to_dict(self) -> Dict:
        """Convert Version to a dictionary with serializable values.

        Returns:
            Dict: Dictionary containing the version's data
        """
        return {
            "content": self.content,
            "created_at": str(self.created_at),
            "version_id": self.version_id,
            "runs": [run.to_dict() for run in self.runs.values()],
            "variables": {k: v.to_dict() for k, v in self.variables.items()}
            if self.variables
            else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Version":
        """Create Version from dictionary.

        Args:
            data (Dict): Dictionary containing the version's data

        Returns:
            Version: The newly created Version
        """

        return cls(
            content=data["content"],
            created_at=data["created_at"]
            if isinstance(data["created_at"], datetime)
            else datetime.fromisoformat(data["created_at"]),
            version_id=data["version_id"],
            runs={run["run_id"]: Run.from_dict(run) for run in data.get("runs", [])},
            variables={
                k: Variable.from_dict(v) for k, v in data.get("variables", {}).items()
            }
            if data.get("variables")
            else None,
        )
