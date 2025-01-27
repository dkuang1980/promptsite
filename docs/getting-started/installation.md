# Installation

PromptSite can be installed using pip:

```bash
pip install promptsite
```

## Requirements

PromptSite requires Python 3.8 or later and has the following core dependencies:

- click: Command line interface toolkit
- pyyaml: YAML file handling
- pydantic: Data validation
- gitpython: Git repository management
- datamodel-code-generator: Data model code generator
- pandas: Data analysis library

## Development Installation

For development, you can clone the repository and install using Poetry:

```bash
# Clone the repository
git clone https://github.com/dkuang1980/promptsite.git
cd promptsite

# Install poetry if you haven't already
pip install poetry

# Install dependencies including development packages
poetry install
```

## Verifying Installation

To verify that PromptSite is installed correctly, run:

```bash
promptsite --help
```

This should display the available commands and options.

## Storage Backend Configuration

PromptSite supports two storage backends:

### File Storage (Default)
Initialize with local file storage:

```bash
promptsite init
```

### Git Storage
Initialize with Git storage and remote repository:

```bash
promptsite init --config '{"storage_backend": "git", "remote": "https://github.com/user/repo.git", "branch": "main"}'
```

## Next Steps

After installation, check out the [Quick Start](quickstart.md) guide to begin using PromptSite.

## Troubleshooting

If you encounter any issues during installation:

1. Ensure you have Python 3.8 or later installed
2. Check that all dependencies are properly installed
3. Verify your Git configuration if using Git storage backend
4. Make sure you have appropriate permissions for the installation directory

For more detailed troubleshooting, please refer to our [documentation](https://promptsite.readthedocs.io/) or open an issue on our [GitHub repository](https://github.com/dkuang1980/promptsite).
```