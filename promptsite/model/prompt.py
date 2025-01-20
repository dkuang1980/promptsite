from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from datetime import UTC  # type: ignore
except ImportError:
    from datetime import timezone as _timezone

    UTC = _timezone.utc

from .variable import Variable
from .version import Version


@dataclass
class Prompt:
    """
    A class representing a prompt with version control capabilities.

    Attributes:
        id (str): Unique identifier for the prompt
        description (str): Description of the prompt
        tags (List[str]): List of tags associated with the prompt
        versions (Dict[str, Version]): Dictionary of versions for the prompt
        variables (Optional[Dict[str, Variable]]): Dictionary of variables for the prompt
    """

    id: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    versions: Dict[str, Version] = field(default_factory=dict)
    variables: Optional[Dict[str, Variable]] = field(default_factory=dict)

    def add_version(
        self, content: str, variables: Optional[Dict[str, Variable]] = None
    ) -> Version:
        """Add a new version of the prompt.

        Args:
            content (str): The content of the new version
            variables (Optional[Dict[str, Variable]]): Dictionary of variables for the new version

        Returns:
            Version: The newly created version object
        """
        # Create new version with all required fields
        version = Version(content=content, variables=variables or self.variables)

        # Add to versions dict and set as active
        self.versions[version.version_id] = version

        return version

    def get_latest_version(self) -> Optional[Version]:
        """Get the latest version of the prompt.

        Returns:
            Optional[Version]: The latest version, or None if no versions exist
        """
        if not self.versions:
            return None
        return sorted(self.versions.values(), key=lambda v: v.created_at)[-1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the prompt to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary containing the prompt's data
        """
        return {
            "id": self.id,
            "description": self.description,
            "tags": self.tags,
            "versions": [v.to_dict() for v in self.versions.values()],
            "variables": {k: v.to_dict() for k, v in self.variables.items()}
            if self.variables
            else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prompt":
        """
        Create a Prompt instance from a dictionary.

        Args:
            data: Dictionary containing the prompt's data.

        Returns:
            Prompt: A new Prompt instance.
        """
        prompt = cls(
            id=data["id"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            variables={
                k: Variable.from_dict(v) for k, v in data.get("variables", {}).items()
            }
            if data.get("variables")
            else None,
        )
        for version_data in data.get("versions", []):
            version = Version.from_dict(version_data)
            prompt.versions[version.version_id] = version
        return prompt
