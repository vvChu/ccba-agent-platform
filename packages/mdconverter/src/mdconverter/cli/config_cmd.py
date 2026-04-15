"""
Config command for mdconverter CLI.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mdconverter.config import get_settings

app_config = typer.Typer(help="Manage configuration.", name="config")
console = Console()


@app_config.command(name="show")
def config_show() -> None:
    """Show current configuration."""
    settings = get_settings()
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Gateway URL", settings.ai_gateway_url)
    table.add_row(
        "Gateway Key",
        (settings.ai_gateway_key[:10] + "...") if settings.ai_gateway_key else "[dim]None[/dim]",
    )
    table.add_row("Models", ", ".join(settings.models))
    table.add_row("Max Tokens", str(settings.max_output_tokens))
    table.add_row("Timeout", f"{settings.timeout_seconds}s")
    table.add_row("Temperature", str(settings.temperature))

    console.print(table)


@app_config.command(name="set")
def config_set(
    key: str = typer.Option(..., "--key", "-k", help="Setting key to update."),
    value: str = typer.Option(..., "--value", "-v", help="New value for the setting."),
) -> None:
    """Update a configuration setting in .env file."""
    # Reject values containing newlines to prevent env injection
    if "\n" in value or "\r" in value:
        console.print("[red]Error: Value must not contain newline characters.[/red]")
        raise typer.Exit(1)

    valid_keys = {
        "ai_gateway_url": "AI_GATEWAY_URL",
        "ai_gateway_key": "AI_GATEWAY_KEY",
        "llama_cloud_api_key": "MDCONVERT_LLAMA_CLOUD_API_KEY",
    }

    if key not in valid_keys:
        console.print(f"[red]Invalid key: {key}[/red]")
        console.print(f"Valid keys: {', '.join(valid_keys.keys())}")
        raise typer.Exit(1)

    env_var = valid_keys[key]
    env_path = Path(".env")

    # Read existing content
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    # Update or append
    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{env_var}="):
            new_lines.append(f"{env_var}={value}")
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        new_lines.append(f"{env_var}={value}")

    # Write back
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    console.print(f"[green]Updated {key} ({env_var}) successfully![/green]")
