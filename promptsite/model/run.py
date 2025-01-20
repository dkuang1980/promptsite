from dataclasses import dataclass, field
from datetime import datetime

try:
    from datetime import UTC  # type: ignore
except ImportError:
    from datetime import timezone as _timezone

    UTC = _timezone.utc
from typing import Any, Dict, Optional


@dataclass
class Run:
    """
    A Run represents a single execution of a prompt version, storing the output,
    execution time, and configuration used.

    Attributes:
        run_id (str): Unique identifier for this run
        created_at (str): ISO format timestamp when run was created
        run_at (str): ISO format timestamp when run was executed
        final_prompt (str): The final prompt that was executed
        variables (Dict[str, Any]): The variables that were used in the run
        llm_output (Optional[str]): The output text from the LLM
        execution_time (Optional[float]): Time taken to execute in seconds
        llm_config (Optional[Dict[str, Any]]): Configuration used for the LLM
    """

    run_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    run_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    final_prompt: str = field(default_factory=lambda: "")
    variables: Dict[str, Any] = field(default_factory=dict)
    llm_output: Optional[str] = None
    execution_time: Optional[float] = None
    llm_config: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Initialize the run_id if not provided."""
        if not self.run_id:
            self.run_id = self._generate_run_id()

    def _generate_run_id(self) -> str:
        """Generate a run ID based on the hash of the run_at timestamp."""
        return f"run_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{id(self)}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the run to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary containing the run's data.
        """
        return {
            "run_id": self.run_id,
            "created_at": str(self.created_at),
            "llm_output": self.llm_output,
            "final_prompt": self.final_prompt,
            "variables": self.variables,
            "execution_time": self.execution_time,
            "llm_config": self.llm_config,
            "run_at": str(self.run_at),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Run":
        """
        Create a Run instance from a dictionary.

        Args:
            data: Dictionary containing the run's data.

        Returns:
            Run: A new Run instance.
        """
        kwargs = {}
        for attr in ["created_at", "run_at"]:
            if attr in data:
                kwargs[attr] = (
                    data[attr]
                    if isinstance(data[attr], datetime)
                    else datetime.fromisoformat(data[attr])
                )
        if "run_id" in data:
            kwargs["run_id"] = data["run_id"]
        return cls(
            llm_output=data.get("llm_output"),
            execution_time=data.get("execution_time"),
            llm_config=data.get("llm_config"),
            **kwargs,
            final_prompt=data["final_prompt"],
            variables=data.get("variables", {}),
        )
