from contextlib import contextmanager

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def create_progress(transient: bool = True) -> Progress:
    return Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("{task.description}", style="bright_white"),
        TextColumn("{task.completed}/{task.total}", style="dim"),
        transient=transient,
        console=console,
    )


@contextmanager
def activity(message: str, status: str = "dots"):
    with console.status(f"[bold blue]{message}", spinner=status):
        yield
