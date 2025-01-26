from typing import TYPE_CHECKING, Any, Dict, List

import pandas as pd

if TYPE_CHECKING:
    from .core import PromptSite


class Query:
    """Query module for PromptSite.

    This module provides query functionality for retrieving and filtering prompts, versions,
    and runs from a PromptSite instance. It includes base Query class and specialized query
    classes for different types of data.

    Classes:
        Query: Base query class providing common query functionality
        PromptQuery: Query class for retrieving and filtering prompts
        VersionQuery: Query class for retrieving and filtering versions
        RunQuery: Query class for retrieving and filtering runs

    Example:
        ps = PromptSite()
        # Get all prompts as list of dicts
        prompts = ps.prompts.all()
        # Get all prompts as DataFrame
        prompts_df = ps.prompts.as_df()
        # Get specific columns from versions
        versions_df = ps.versions.only(['version_id', 'content']).as_df()
        # Filter runs by prompt_id
        runs_df = ps.runs.where(prompt_id='prompt1').as_df()
    """

    def __init__(self, ps: "PromptSite"):
        """Initialize the query.

        Args:
            ps: PromptSite instance
        """
        self.ps = ps
        self.columns = None

    def one(self) -> Dict[str, Any]:
        """Get the first item in the query."""
        return self.all()[0]

    def all(self) -> List[Dict[str, Any]]:
        """Get all prompts."""
        raise NotImplementedError("This method must be implemented by the subclass.")

    def only(self, columns: List[str]) -> "Query":
        """Select only the specified columns."""
        self.columns = columns
        return self

    def where(self, **kwargs) -> "Query":
        """Filter the query."""
        raise NotImplementedError("This method must be implemented by the subclass.")

    def as_df(self) -> pd.DataFrame:
        """Get the results as a pandas DataFrame."""
        return pd.DataFrame(self.all())


class PromptQuery(Query):
    """Query Class for prompts.

    This class provides a query interface for retrieving and filtering prompts from a PromptSite instance.
    It allows for selecting specific columns, filtering by attributes, and retrieving the prompts.
    """

    def __init__(self, ps: "PromptSite"):
        """Initialize the query."""
        super().__init__(ps)
        self.prompt_id = None

    def all(self) -> List[Dict[str, Any]]:
        """Get all prompts.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing prompt data
        """
        prompt_dicts = []
        if self.prompt_id is not None:
            prompt_dict = self.ps.get_prompt(
                self.prompt_id, exclude_versions=True
            ).to_dict(**({"columns": self.columns} if self.columns else {}))
            prompt_dicts.append(prompt_dict)
        else:
            for p in self.ps.list_prompts(exclude_versions=True):
                prompt_dict = p.to_dict(
                    **({"columns": self.columns} if self.columns else {})
                )
                prompt_dicts.append(prompt_dict)
        return prompt_dicts

    def where(self, prompt_id: str) -> "PromptQuery":
        """Filter the query."""
        self.prompt_id = prompt_id
        return self


class VersionQuery(Query):
    """Query Class for versions.

    This class provides a query interface for retrieving and filtering versions from a PromptSite instance.
    It allows for selecting specific columns, filtering by attributes, and retrieving the versions.
    """

    def __init__(self, ps: "PromptSite"):
        """Initialize the query.

        Args:
            ps: PromptSite instance
        """
        super().__init__(ps)
        self.prompt_id = None
        self.version_id = None

    def all(self) -> List[Dict[str, Any]]:
        """Get all versions.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries for versions
        """
        versions = []
        if self.prompt_id is not None:
            for version in self.ps.list_versions(self.prompt_id, exclude_runs=True):
                version.prompt_id = self.prompt_id
                versions.append(version)
        else:
            for prompt in self.ps.list_prompts(exclude_versions=True):
                for version in self.ps.list_versions(prompt.id, exclude_runs=True):
                    version.prompt_id = prompt.id
                    versions.append(version)

        version_dicts = []
        for version in versions:
            version_dict = version.to_dict(
                **({"columns": self.columns} if self.columns else {})
            )
            if "runs" in version_dict:
                del version_dict["runs"]
            if self.columns is None or "prompt_id" in self.columns:
                version_dict["prompt_id"] = version.prompt_id
            version_dicts.append(version_dict)
        return version_dicts

    def where(self, prompt_id: str, version_id: str = None) -> "VersionQuery":
        """Filter the query.

        Args:
            prompt_id: The ID of the prompt to filter by

        Returns:
            VersionQuery: The filtered query
        """
        self.prompt_id = prompt_id
        self.version_id = version_id
        return self


class RunQuery(Query):
    """Query Class for runs.

    This class provides a query interface for retrieving and filtering runs from a PromptSite instance.
    It allows for selecting specific columns, filtering by attributes, and retrieving the runs.
    """

    def __init__(self, ps: "PromptSite"):
        """Initialize the query.

        Args:
            ps: PromptSite instance
        """
        super().__init__(ps)
        self.prompt_id = None
        self.version_id = None
        self.run_id = None

    def all(self) -> List[Dict[str, Any]]:
        """Get all runs.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries for runs
        """
        if self.prompt_id is not None and self.version_id is not None:
            runs = []
            for run in self.ps.list_runs(self.prompt_id, self.version_id):
                run.prompt_id = self.prompt_id
                run.version_id = self.version_id
                runs.append(run)

        elif self.prompt_id is not None:
            runs = []
            for version in self.ps.list_versions(self.prompt_id, exclude_runs=True):
                for run in self.ps.list_runs(self.prompt_id, version.version_id):
                    run.prompt_id = self.prompt_id
                    run.version_id = version.version_id
                    runs.append(run)
        else:
            runs = []
            for prompt in self.ps.list_prompts(exclude_versions=True):
                for version in self.ps.list_versions(prompt.id, exclude_runs=True):
                    for run in self.ps.list_runs(prompt.id, version.version_id):
                        run.prompt_id = prompt.id
                        run.version_id = version.version_id
                        runs.append(run)

        run_dicts = []
        for r in runs:
            run_dict = r.to_dict(**({"columns": self.columns} if self.columns else {}))
            if self.columns is None or "prompt_id" in self.columns:
                run_dict["prompt_id"] = r.prompt_id
            if self.columns is None or "version_id" in self.columns:
                run_dict["version_id"] = r.version_id
            run_dicts.append(run_dict)
        return run_dicts

    def where(
        self, prompt_id: str, version_id: str = None, run_id: str = None
    ) -> "RunQuery":
        """Filter the query.

        Args:
            prompt_id: The ID of the prompt to filter by
            version_id: The ID of the version to filter by

        Returns:
            RunQuery: The filtered query
        """
        self.prompt_id = prompt_id
        self.version_id = version_id
        self.run_id = run_id
        return self
