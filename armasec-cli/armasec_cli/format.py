import json
from typing import Any

import snick
from rich.console import Console
from rich.panel import Panel


def terminal_message(message, subject=None, color="green", footer=None, indent=True):
    panel_kwargs = dict(padding=1)
    if subject is not None:
        panel_kwargs["title"] = f"[{color}]{subject}"
    if footer is not None:
        panel_kwargs["subtitle"] = f"[dim italic]{footer}[/dim italic]"
    text = snick.dedent(message)
    if indent:
        text = snick.indent(text, prefix="  ")
    console = Console()
    console.print()
    console.print(Panel(text, **panel_kwargs))
    console.print()


def render_json(data: Any):
    console = Console()
    console.print()
    console.print_json(json.dumps(data))
    console.print()
