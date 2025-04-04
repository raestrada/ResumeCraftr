import click
import os
import subprocess
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
LATEX_TEMPLATE = "cv-workspace/resume_template.tex"

def check_xelatex():
    """Check if xelatex is installed and provide installation instructions if not."""
    try:
        subprocess.run(
            ["xelatex", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def print_xelatex_installation_guide():
    """Prints installation instructions for XeLaTeX in Markdown format using rich."""
    instructions = """
# 🚀 Installing XeLaTeX

ResumeCraftr requires **XeLaTeX** to compile PDFs. Follow the instructions below for your system:

### 🟢 Windows
1. Download and install [MiKTeX](https://miktex.org/download).
2. Ensure `xelatex` is in your system's PATH by running:
   ```
   xelatex --version
   ```
   If not, restart your computer or manually add the MiKTeX `bin` directory to your PATH.

### 🍏 macOS
1. Install **MacTeX** (includes XeLaTeX) via Homebrew:
   ```
   brew install mactex
   ```
2. Verify the installation:
   ```
   xelatex --version
   ```

### 🐧 Linux
For Debian/Ubuntu:
   ```
   sudo apt update && sudo apt install texlive-xetex
   ```
For Arch Linux:
   ```
   sudo pacman -S texlive-bin
   ```
For Fedora:
   ```
   sudo dnf install texlive-xetex
   ```

After installation, re-run:
   ```
   xelatex --version
   ```

Once installed, retry running `resumecraftr tex-to-pdf`! ✅
"""
    console.print(Markdown(instructions))

@click.command()
@click.argument("tex_file", type=click.Path(exists=True), required=False)
def tex_to_pdf(tex_file):
    """Generate a PDF resume directly from a LaTeX file without using OpenAI."""
    if not check_xelatex():
        console.print("[bold red]Error: XeLaTeX is not installed.[/bold red]")
        print_xelatex_installation_guide()
        return

    # If no tex file is provided, find all tex files in the workspace
    if not tex_file:
        tex_files = []
        for file in os.listdir("cv-workspace"):
            if file.endswith(".tex") and not file == "resume_template.tex":
                tex_files.append(file)

        if not tex_files:
            console.print(
                "[bold red]No LaTeX files found in the workspace. Please provide a LaTeX file path.[/bold red]"
            )
            return

        if len(tex_files) > 1:
            tex_file = Prompt.ask(
                "Multiple LaTeX files detected. Choose one", choices=tex_files
            )
            tex_file = os.path.join("cv-workspace", tex_file)
        else:
            tex_file = os.path.join("cv-workspace", tex_files[0])
    else:
        # If the file is not in the workspace, copy it there
        if not os.path.dirname(tex_file) == "cv-workspace":
            filename = os.path.basename(tex_file)
            dest_path = os.path.join("cv-workspace", filename)
            try:
                import shutil
                shutil.copy(tex_file, dest_path)
                tex_file = dest_path
                console.print(f"[bold green]Copied file to workspace: {dest_path}[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error copying file to workspace: {e}[/bold red]")
                return

    # Verify the file exists
    if not os.path.exists(tex_file):
        console.print(f"[bold red]LaTeX file not found: {tex_file}[/bold red]")
        return

    # Get the output PDF file path
    output_pdf_file = tex_file.replace(".tex", ".pdf")

    console.print(f"[bold cyan]Compiling LaTeX file: {tex_file}[/bold cyan]")

    # Compile LaTeX to PDF
    try:
        subprocess.run(
            [
                "xelatex",
                "-interaction=nonstopmode",
                "-output-directory=cv-workspace",
                tex_file,
            ],
            check=True,
        )
        console.print(
            f"[bold green]PDF successfully generated: {output_pdf_file}[/bold green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error during LaTeX compilation: {e}[/bold red]")
        console.print(
            "[bold yellow]You can edit the LaTeX file manually and try again.[/bold yellow]"
        )

if __name__ == "__main__":
    tex_to_pdf() 