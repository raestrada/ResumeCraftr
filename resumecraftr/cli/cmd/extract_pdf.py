import click
import os
import json
import subprocess
from rich.console import Console
from rich.prompt import Prompt
from resumecraftr.cli.agent import execute_prompt, create_or_get_agent
from resumecraftr.cli.prompts.pdf import RAW_PROMPT, LATEX_CORRECTION

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
LATEX_TEMPLATE = "cv-workspace/resume_template.tex"
CUSTOM_PROMPT = "cv-workspace/custom.md"

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

Once installed, retry running `resumecraftr extract-pdf`! ✅
"""
    console.print(Markdown(instructions))

@click.command()
def extract_pdf():
    """Generate a PDF resume directly from extracted sections without optimization."""
    # Only create the agent when we're about to use OpenAI
    create_or_get_agent("ResumeCraftr Agent PDF gen")

    if not check_xelatex():
        console.print("[bold red]Error: XeLaTeX is not installed.[/bold red]")
        print_xelatex_installation_guide()
        return

    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]"
        )
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    with open(CUSTOM_PROMPT, "r", encoding="utf-8") as f:
        custom_promt = f.readlines()

    # Find extracted sections files
    extracted_files = []
    for file in os.listdir("cv-workspace"):
        if file.endswith(".extracted_sections.json"):
            extracted_files.append(file)

    if not extracted_files:
        console.print(
            "[bold red]No extracted CV sections found. Run 'resumecraftr extract-sections' first.[/bold red]"
        )
        return

    sections_file = extracted_files[0]
    if len(extracted_files) > 1:
        sections_file = Prompt.ask(
            "Multiple extracted CV files detected. Choose one", choices=extracted_files
        )

    sections_path = os.path.abspath(os.path.join("cv-workspace", sections_file))
    if not os.path.exists(sections_path):
        console.print(
            f"[bold red]Selected extracted sections file '{sections_file}' does not exist.[/bold red]"
        )
        return

    console.print(f"[bold blue]Generating PDF using: {sections_file}[/bold blue]")

    with open(sections_path, "r", encoding="utf-8") as f:
        extracted_sections = json.load(f)

    # Load LaTeX template
    if not os.path.exists(LATEX_TEMPLATE):
        console.print(
            f"[bold red]LaTeX template '{LATEX_TEMPLATE}' not found.[/bold red]"
        )
        return

    with open(LATEX_TEMPLATE, "r", encoding="utf-8") as f:
        latex_template = f.read()

    # 🔹 Convert JSON to string for OpenAI
    extracted_sections_text = json.dumps(
        extracted_sections, indent=4, ensure_ascii=False
    )

    # 🔹 Generate the prompt
    prompt = (
        RAW_PROMPT.format(
            latex_template=latex_template,
            optimized_sections=extracted_sections_text,
            job_description="",  # No job description for direct PDF generation
            language=config.get("primary_language"),
            custom=custom_promt
        )
        .replace("{{", "{")
        .replace("}}", "}")
    )

    # 🔹 Generate LaTeX with OpenAI
    latex_content = execute_prompt(prompt, "ResumeCraftr Agent PDF gen")

    if not latex_content.strip():
        console.print(
            "[bold red]Error: OpenAI did not return a valid LaTeX document.[/bold red]"
        )
        return

    # Save the LaTeX file
    output_tex_file = os.path.join(
        "cv-workspace", sections_file.replace(".extracted_sections.json", ".tex")
    )
    output_pdf_file = output_tex_file.replace(".tex", ".pdf")

    with open(output_tex_file, "w", encoding="utf-8") as f:
        f.write(latex_content.replace("```latex", "").replace("```", ""))

    console.print(f"[bold cyan]Compiling LaTeX file: {output_tex_file}[/bold cyan]")

    # Compile LaTeX to PDF
    try:
        subprocess.run(
            [
                "xelatex",
                "-interaction=nonstopmode",
                "-output-directory=cv-workspace",
                output_tex_file,
            ],
            check=True,
        )
        console.print(
            f"[bold green]PDF successfully generated: {output_pdf_file}[bold green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error during LaTeX compilation: {e}[bold red]")
        console.print(
            "[bold yellow]Attempting automatic LaTeX correction...[bold yellow]"
        )

        # Use OpenAI to correct the LaTeX document
        correction_prompt = LATEX_CORRECTION.format(
            latex_code=latex_content, error_message=str(e)
        ).replace("{{","{").replace("}}","}")
        corrected_latex = execute_prompt(
            correction_prompt, "ResumeCraftr Agent PDF gen"
        )

        if corrected_latex.strip():
            with open(output_tex_file, "w", encoding="utf-8") as f:
                f.write(corrected_latex.replace("```latex", "").replace("```", ""))

            console.print(
                f"[bold cyan]Re-compiling corrected LaTeX file: {output_tex_file}[bold cyan]"
            )
            try:
                subprocess.run(
                    [
                        "xelatex",
                        "-interaction=nonstopmode",
                        "-output-directory=cv-workspace",
                        output_tex_file,
                    ],
                    check=True,
                )
                console.print(
                    f"[bold green]PDF successfully generated after correction: {output_pdf_file}[bold green]"
                )
            except subprocess.CalledProcessError:
                console.print(
                    "[bold red]Final LaTeX compilation failed. Please review the LaTeX file manually.[bold red]"
                )
        else:
            console.print(
                "[bold red]OpenAI could not correct the LaTeX document. Manual intervention required.[bold red]"
            )

if __name__ == "__main__":
    extract_pdf() 