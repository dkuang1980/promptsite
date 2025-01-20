class PromptSiteError(Exception):
    """Base exception class for PromptSite errors."""


class PromptAlreadyExistsError(PromptSiteError):
    """Raised when attempting to register a prompt that already exists."""


class PromptNotFoundError(PromptSiteError):
    """Raised when attempting to access a prompt that doesn't exist."""


class InvalidPromptContentError(PromptSiteError):
    """Raised when prompt content is invalid or empty."""


class StorageFileNotFoundError(PromptSiteError):
    """Raised when the storage file is not found."""


class StorageBackendNotFoundError(PromptSiteError):
    """Raised when specified storage backend is not found."""

    pass


class StorageError(PromptSiteError):
    """Base exception for storage-related errors."""

    pass


class ConfigFileNotFoundError(PromptSiteError):
    """Raised when config file is not found."""

    pass


class ConfigError(PromptSiteError):
    """Base exception for config-related errors."""

    pass


class VersionNotFoundError(PromptSiteError):
    """Raised when a prompt version is not found."""

    pass


class VariableUnmatchError(PromptSiteError):
    """Raised when the variables and the values do not match."""

    pass


class VariableValidationError(PromptSiteError):
    """Raised when the variable is not valid."""

    pass


class RunNotFoundError(PromptSiteError):
    """Raised when a run is not found."""

    pass
