# CLI Usage Guide

PromptSite provides a comprehensive command-line interface (CLI) for managing prompts, versions, and runs. This guide covers all available commands and their usage.

## Basic Commands

### Initialize PromptSite

Before using PromptSite, you need to initialize it in your project directory:

```bash
promptsite init
```

For Git storage backend:

```bash
promptsite init --config '{"storage_backend": "git", "remote": "https://github.com/user/repo.git", "branch": "main"}'
```

## Prompt Management

### Register a New Prompt

Create a new prompt with initial content:

```bash
promptsite prompt register my-prompt --content "Translate this text: {{ text }}" --description "Translation prompt" --tags translation gpt
```

Options:
- `--content, -c`: Initial prompt content
- `--description, -d`: Prompt description
- `--tags, -t`: Tags for categorizing the prompt (can be used multiple times)

### List All Prompts

View all registered prompts:

```bash
promptsite prompt list
```

This shows:
- Prompt ID
- Description
- Number of versions
- Last update timestamp

### Get Prompt Details

View details of a specific prompt:

```bash
promptsite prompt get my-prompt
```

Shows:
- Prompt ID
- Description
- Tags
- Total versions
- Active version
- Current content

### Delete a Prompt

Remove a prompt and all its versions:

```bash
promptsite prompt delete my-prompt
```

Add `--force` to skip confirmation:

```bash
promptsite prompt delete my-prompt --force
```

## Version Management

### Add a New Version

Create a new version of an existing prompt:

```bash
promptsite version add my-prompt --content "Please translate the following text: {{ text }}"
```

### List Versions

View all versions of a prompt:

```bash
promptsite version list my-prompt
```

Shows:
- Version ID
- Creation timestamp
- Active version indicator (*)

### Get Version Details

View details of a specific version:

```bash
promptsite version get my-prompt <version-id>
```

Shows:
- Version content
- Creation timestamp
- Associated runs

## Run Management

### List Runs

View all runs for a specific prompt version:

```bash
promptsite run list my-prompt <version-id>
```

Shows:
- Run ID
- Creation timestamp
- Execution time
- LLM configuration

### Get Run Details

View details of a specific run:

```bash
promptsite run get my-prompt <version-id> <run-id>
```

### Get last run

Get the last run for a specific prompt version:

```bash
promptsite prompt last-run my-prompt
```

Shows:
- Run ID
- Creation timestamp
- Final prompt
- LLM output
- Variables used
- LLM configuration
- Execution time

## Git Integration

If using Git storage backend, sync changes with remote:

```bash
promptsite sync-git
```

## Command Help

Get help on any command:

```bash
promptsite --help
promptsite <command> --help
```

List all available commands:

```bash
promptsite commands
```

## Storage Structure

When using PromptSite, the following directory structure is created:

```
.promptsite/
├── prompts/
│   ├── <prompt_id>/
│   │   ├── prompt.yaml        # Prompt metadata
│   │   └── versions/
│   │       ├── <version_id>/
│   │       │   ├── version.yaml   # Version data
│   │       │   └── runs/
│   │       │       └── <run_id>.yaml  # Run data
```

## Environment Variables

PromptSite respects the following environment variables:

- `PROMPTSITE_CONFIG_PATH`: Override default config file location
- `PROMPTSITE_STORAGE_BACKEND`: Override storage backend setting
- `PROMPTSITE_GIT_REMOTE`: Set Git remote URL
- `PROMPTSITE_GIT_BRANCH`: Set Git branch name

## Error Handling

The CLI provides clear error messages for common issues:

- Uninitialized PromptSite
- Non-existent prompts
- Invalid configurations
- Storage backend errors
- Git synchronization issues

Each error includes a descriptive message and appropriate exit code for scripting purposes.
