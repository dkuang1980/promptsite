import json
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from .config import Config
from .core import PromptSite
from .exceptions import ConfigError, PromptNotFoundError


def tracker(
    prompt_id: str,
    content: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    ps_config: Optional[Dict] = None,
    ps: Optional[PromptSite] = None,
    llm_config: Optional[Dict] = None,
    variables: Optional[Dict] = None,
) -> Callable:
    """
    Decorator to automatically register prompts and track their executions.

    Args:
        prompt_id: Unique identifier for the prompt
        content: Optional content for the prompt
        description: Optional description of the prompt
        tags: Optional list of tags
        ps_config: Optional configuration dictionary for PromptSite
        ps: Optional PromptSite instance (will create new one if not provided)
        llm_config: Optional configuration dictionary for the LLM
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal ps
            if ps is None:
                # Save config
                conf = Config()
                conf.save_config(ps_config)

                # Get or create PromptSite instance
                ps = PromptSite(conf.get_storage_backend())

            # Get prompt content
            prompt_content = kwargs.get("content")
            prompt_variables_config = kwargs.get("variables_config", variables)

            if prompt_content is None:
                prompt_content = content

            # Check if content is not provided
            if prompt_content is None or prompt_content == "":
                raise ConfigError("The prompt content is required")

            try:
                # Try to get existing prompt
                prompt = ps.get_prompt(prompt_id)

                latest_version = prompt.get_latest_version()

                # Add new version if content or variables changed
                if (
                    latest_version.content != prompt_content
                    or latest_version.compare_variables(prompt_variables_config or {})
                ):
                    version = ps.add_prompt_version(prompt_id, prompt_content)
                else:
                    version = prompt.get_latest_version()
            except PromptNotFoundError:
                # Register new prompt if it doesn't exist
                prompt = ps.register_prompt(
                    prompt_id=prompt_id,
                    initial_content=prompt_content,
                    description=description,
                    tags=tags or [],
                    variables=variables,
                )
                version = prompt.get_latest_version()

            prompt_content = version.content

            if kwargs.get("variables"):
                prompt_content = version.build_final_prompt(
                    kwargs["variables"],
                    no_instructions=kwargs.get("no_instructions", False),
                    custom_instructions=kwargs.get("custom_instructions", ""),
                )

            _llm_config = kwargs.get("llm_config", llm_config)

            # Execute the function to call llm
            start_time = time.time()
            kwargs["content"] = prompt_content
            kwargs["llm_config"] = _llm_config
            kwargs["prompt_variables_config"] = prompt_variables_config
            response = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Add run to version
            ps.add_run(
                prompt_id=prompt.id,
                version_id=version.version_id,
                final_prompt=prompt_content,
                variables=kwargs.get("variables", {}),
                llm_output=response,
                execution_time=execution_time,
                llm_config=kwargs.get("llm_config", llm_config),
            )

            try:
                return json.loads(response.replace("```json", "").replace("```", ""))
            except json.JSONDecodeError:
                return response

        return wrapper

    return decorator
