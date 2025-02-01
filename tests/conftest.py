import os
import shutil
from pathlib import Path

import pytest

from promptsite.config import Config
from promptsite.core import PromptSite


@pytest.fixture
def storage_path():
    """Create a temporary directory for tests."""

    test_dir = Path(Config.BASE_DIRECTORY)
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    yield test_dir
    # Cleanup after test
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def config(storage_path):
    """Create a test configuration."""
    # Clean up any existing .promptsite directory
    if os.path.exists(".promptsite"):
        shutil.rmtree(".promptsite")

    config = Config({
        "storage_backend": "file",
        "llm_backend": "openai",
        "llm_config": {
            "model": "gpt-4o-mini"
        }
    })
    
    yield config
    # Cleanup config file and directory
    if os.path.exists(config.config_file):
        os.remove(config.config_file)
    if os.path.exists(os.path.dirname(config.config_file)):
        shutil.rmtree(os.path.dirname(config.config_file))


@pytest.fixture
def promptsite(config, storage_path):
    """Create a PromptSite instance for testing."""
    ps = PromptSite(config.get_storage_backend())
    yield ps
    # Cleanup storage directory
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)


@pytest.fixture
def git_config(storage_path):
    """Create a test configuration for git backend."""
    # Clean up any existing .promptsite directory
    if os.path.exists(".promptsite"):
        shutil.rmtree(".promptsite")

    config = Config()
    config.config = {"storage_backend": "git"}
    config.save_config(config.config)
    yield config
    # Cleanup config file and directory
    if os.path.exists(config.config_file):
        os.remove(config.config_file)
    if os.path.exists(os.path.dirname(config.config_file)):
        shutil.rmtree(os.path.dirname(config.config_file))


@pytest.fixture
def git_promptsite(git_config, storage_path):
    """Create a PromptSite instance with git backend for testing."""
    ps = PromptSite(git_config.get_storage_backend())
    yield ps
    # Cleanup storage directory
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)
