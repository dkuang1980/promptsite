import json
import sys
from typing import Optional

import click

from .config import Config
from .core import PromptSite
from .exceptions import PromptNotFoundError, PromptSiteError, StorageError

pass_promptsite = click.make_pass_decorator(PromptSite)


def get_promptsite() -> PromptSite:
    config = Config()
    config.load_config()
    return PromptSite(config.get_storage_backend())


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """promptsite CLI - Manage your prompts with version control"""
    if ctx.invoked_subcommand not in ["init", "commands"]:
        # Only validate configuration if we're not running init or commands
        try:
            ctx.obj = get_promptsite()
        except (FileNotFoundError, KeyError):
            click.echo(
                "Error: promptsite not initialized. Run 'promptsite init' first",
                err=True,
            )
            ctx.exit(1)
    else:
        # For init and commands, use temporary instance
        ctx.obj = None


@cli.command()
@click.option("--config", "-s", default=None, help="Configuration in JSON format")
def init(config: Optional[str]):
    """Initialize promptsite in the current directory"""
    # Parse storage config if provided
    config_kwargs = {}
    if config:
        try:
            config_kwargs = json.loads(config)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON in storage-config", err=True)
            return

    # Initialize config
    conf = Config()
    conf.save_config(config_kwargs)

    # Display initialization info in a cleaner format
    click.echo("Initialized promptsite in current directory")
    click.echo("\nConfiguration:")
    if config_kwargs:
        for key, value in config_kwargs.items():
            click.echo(f"  {key}: {value}")


@cli.group()
def prompt():
    """Manage prompts"""
    pass


@prompt.command("register")
@click.argument("prompt_id")
@click.option("--content", "-c", help="Initial prompt content")
@click.option("--description", "-d", default="", help="Prompt description")
@click.option("--tags", "-t", multiple=True, help="Tags for the prompt")
@pass_promptsite
def prompt_register(
    ps: PromptSite,
    prompt_id: str,
    content: Optional[str],
    description: str,
    tags: tuple,
):
    """Register a new prompt"""

    try:
        ps.register_prompt(
            prompt_id=prompt_id,
            description=description,
            tags=list(tags),
            initial_content=content,
        )
        click.echo(f"Registered prompt '{prompt_id}'")
    except PromptSiteError as e:
        click.echo(f"Error: {str(e)}", err=True)


@prompt.command("get")
@click.argument("prompt_id")
@pass_promptsite
def prompt_get(ps: PromptSite, prompt_id: str):
    """Get prompt details"""
    try:
        prompt = ps.get_prompt(prompt_id)
        latest_version = prompt.get_latest_version()
        click.echo(f"ID: {prompt.id}")
        click.echo(f"Description: {prompt.description}")
        click.echo(f"Tags: {', '.join(prompt.tags)}")
        click.echo(f"Total Versions: {len(prompt.versions)}")
        click.echo(f"Active Version: {latest_version.version_id}")
        click.echo("Content:")
        click.echo(latest_version.content)
    except PromptSiteError as e:
        click.echo(f"Error: {str(e)}", err=True)


@prompt.command("list")
@pass_promptsite
def prompt_list(ps: PromptSite):
    """List all prompts"""
    prompts = ps.list_prompts()
    if not prompts:
        click.echo("No prompts found")
        return

    for prompt in prompts:
        # Get latest version timestamp
        latest_timestamp = None
        for version in prompt.versions.values():
            if latest_timestamp is None or version.created_at > latest_timestamp:
                latest_timestamp = version.created_at

        # Format output
        parts = [prompt.id]
        if prompt.description:
            parts.append(f": {prompt.description}")
        if latest_timestamp:
            parts.append(
                f" ({len(prompt.versions)} versions, updated: {latest_timestamp.strftime('%Y-%m-%d %H:%M')})"
            )

        click.echo("".join(parts))


@prompt.command("delete")
@click.argument("prompt_id")
@click.option("--force", is_flag=True, help="Force deletion without confirmation")
@pass_promptsite
def prompt_delete(ps: PromptSite, prompt_id: str, force: bool):
    """Delete a prompt."""
    try:
        if not force:
            if not click.confirm(
                f"Are you sure you want to delete prompt '{prompt_id}'?"
            ):
                click.echo("Deletion cancelled.")
                sys.exit(1)

        ps.delete_prompt(prompt_id)
        click.echo(f"Prompt '{prompt_id}' deleted successfully.")
    except PromptNotFoundError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)  # Add explicit exit code for errors
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)  # Add explicit exit code for errors


@cli.group()
def version():
    """Manage prompt versions"""
    pass


@version.command("list")
@click.argument("prompt_id")
@pass_promptsite
def version_list(ps: PromptSite, prompt_id: str):
    """List versions for a prompt in a tree structure"""
    try:
        prompt = ps.get_prompt(prompt_id)
        versions = ps.list_versions(prompt_id)
        # Sort versions by creation timestamp
        versions = sorted(versions.values(), key=lambda v: v.created_at)

        # Print each version with active marker for latest
        for version in versions:
            active_marker = (
                "*"
                if version.version_id == prompt.get_latest_version().version_id
                else " "
            )

            click.echo(
                f"[{version.version_id[:8]}] {active_marker} "
                f"Created: {version.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
    except PromptSiteError as e:
        click.echo(f"Error: {str(e)}", err=True)


@version.command("get")
@click.argument("prompt_id")
@click.argument("version_id")
@pass_promptsite
def version_get(ps: PromptSite, prompt_id: str, version_id: str):
    """Get specific version of a prompt"""
    try:
        version = ps.get_version(prompt_id, version_id)
        click.echo(f"Content: {version.content}")
        click.echo(f"Created at: {version.created_at}")
        click.echo(f"Version ID: {version.version_id}")
        if version.runs:
            click.echo("\nRuns:")
            for run in version.runs:
                click.echo(f"  - {run}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@version.command("add")
@click.argument("prompt_id")
@click.option("--content", "-c", help="New version content")
@pass_promptsite
def version_add(ps: PromptSite, prompt_id: str, content: Optional[str]):
    """Add new version to a prompt"""
    try:
        version = ps.add_prompt_version(prompt_id, content)
        click.echo(
            f"Added new version [{version.version_id[:8]}] to prompt '{prompt_id}'"
        )
    except PromptSiteError as e:
        click.echo(f"Error: {str(e)}", err=True)


@cli.group()
def run():
    """Manage prompt runs"""
    pass


@run.command("list")
@click.argument("prompt_id")
@click.argument("version_id")
@pass_promptsite
def list_runs(ps: PromptSite, prompt_id: str, version_id: str):
    """List all runs for a specific prompt version"""
    try:
        runs = ps.list_runs(prompt_id, version_id)
        if not runs:
            click.echo("No runs found")
            return

        for run in runs:
            click.echo(f"Run ID: {run.run_id}")
            click.echo(f"  Created: {run.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"  Execution time: {run.execution_time:.2f}s")
            if run.llm_config:
                click.echo(f"  LLM config: {run.llm_config}")
            click.echo("")
    except PromptSiteError as e:
        click.echo(f"Error: {str(e)}", err=True)


@run.command("get")
@click.argument("prompt_id")
@click.argument("version_id")
@click.argument("run_id")
@pass_promptsite
def get_run(ps: PromptSite, prompt_id: str, version_id: str, run_id: str):
    """Get details of a specific run"""
    try:
        run = ps.get_run(prompt_id, version_id, run_id)
        click.echo(f"Run ID: {run.run_id}")
        click.echo(f"Created at: {run.created_at}")
        click.echo(f"Execution time: {run.execution_time:.2f}s")
        click.echo("\nFinal prompt:")
        click.echo(run.final_prompt)
        click.echo("\nLLM output:")
        click.echo(run.llm_output)
        if run.variables:
            click.echo("\nVariables:")
            click.echo(json.dumps(run.variables, indent=2))
        if run.llm_config:
            click.echo("\nLLM config:")
            click.echo(json.dumps(run.llm_config, indent=2))
    except PromptSiteError as e:
        click.echo(f"Error: Run not found {str(e)}", err=True)


@prompt.command("last-run")
@click.argument("prompt_id")
@pass_promptsite
def get_last_run(ps: PromptSite, prompt_id: str):
    """Get the last run for a specific prompt version"""
    run = ps.get_last_run(prompt_id)
    click.echo(f"Run ID: {run.run_id}")
    click.echo(f"Created at: {run.created_at}")
    if run.execution_time:
        click.echo(f"Execution time: {run.execution_time:.2f}s")
    else:
        click.echo("Execution time: N/A")
    click.echo("\nFinal prompt:")
    click.echo(run.final_prompt)
    click.echo("\nLLM output:")
    click.echo(run.llm_output)
    if run.variables:
        click.echo("\nVariables:")
        click.echo(json.dumps(run.variables, indent=2))
    if run.llm_config:
        click.echo("\nLLM config:")
        click.echo(json.dumps(run.llm_config, indent=2))


@cli.command()
def commands():
    """List all available promptsite commands"""
    ctx = click.get_current_context()
    click.echo("Available promptsite commands:")

    def format_commands(command, prefix=""):
        commands = []
        # Add the current command if it has a help message and isn't a group
        if command.help and not command.hidden and not isinstance(command, click.Group):
            display_prefix = (
                "promptsite " if not prefix else prefix.replace("cli ", "promptsite ")
            )
            commands.append(f"{display_prefix}{command.name}: {command.help}")

        # Add subcommands
        if isinstance(command, click.Group):
            for subcommand in command.commands.values():
                commands.extend(format_commands(subcommand, f"{prefix}{command.name} "))

        return commands

    # Get all commands
    all_commands = format_commands(ctx.find_root().command)

    # Print commands sorted alphabetically
    for cmd in sorted(all_commands):
        click.echo(f"  {cmd}")


@cli.command("sync-git")
@pass_promptsite
def sync_git(ps: PromptSite):
    """Synchronize changes with git remote repository."""
    try:
        ps.sync_git()
        click.echo("Successfully synchronized with git remote")
    except TypeError:
        click.echo(
            "Error: Current storage backend doesn't support git synchronization",
            err=True,
        )
    except StorageError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


if __name__ == "__main__":
    cli(ctx=None)
