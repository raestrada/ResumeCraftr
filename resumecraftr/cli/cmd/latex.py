import click
import os
import json
import subprocess
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
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

Once installed, retry running `resumecraftr generate-pdf`! ✅
"""
    console.print(Markdown(instructions))

@click.command()
def generate_pdf():
    """Generate a PDF resume using the optimized LaTeX template with OpenAI."""
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

    extracted_files = config.get("extracted_files", [])
    if not extracted_files:
        console.print(
            "[bold red]No extracted CV sections found in configuration.[/bold red]"
        )
        return

    extracted_files = [
        f.replace(".txt", ".optimized_sections.json") for f in extracted_files
    ]
    sections_file = extracted_files[0]

    if len(extracted_files) > 1:
        sections_file = Prompt.ask(
            "Multiple optimized CV files detected. Choose one", choices=extracted_files
        )

    sections_path = os.path.abspath(os.path.join("cv-workspace", sections_file))
    if not os.path.exists(sections_path):
        console.print(
            f"[bold red]Selected optimized sections file '{sections_file}' does not exist.[/bold red]"
        )
        return

    console.print(f"[bold blue]Generating PDF using: {sections_file}[/bold blue]")

    with open(sections_path, "r", encoding="utf-8") as f:
        optimized_sections = json.load(f)

    # Load LaTeX template
    if not os.path.exists(LATEX_TEMPLATE):
        console.print(
            f"[bold red]LaTeX template '{LATEX_TEMPLATE}' not found.[/bold red]"
        )
        return

    with open(LATEX_TEMPLATE, "r", encoding="utf-8") as f:
        latex_template = f.read()

    # Load extracted CV text
    original_cv_text = ""
    for txt_file in config.get("extracted_files", []):
        txt_path = os.path.abspath(os.path.join("cv-workspace", txt_file))
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                original_cv_text = f.read()
                break

    # Load job description
    job_desc_files = config.get("job_descriptions", [])
    if not job_desc_files:
        console.print(
            "[bold red]No job descriptions found in configuration.[/bold red]"
        )
        return

    job_desc_path = os.path.abspath(
        os.path.join("cv-workspace", "job_descriptions", job_desc_files[0])
    )
    if not os.path.exists(job_desc_path):
        console.print(
            f"[bold red]Selected job description file '{job_desc_files[0]}' does not exist.[/bold red]"
        )
        return

    with open(job_desc_path, "r", encoding="utf-8") as f:
        job_description = f.read()

    # 🔹 Convert JSON to string for OpenAI
    optimized_sections_text = json.dumps(
        optimized_sections, indent=4, ensure_ascii=False
    )

    # 🔹 Generate the prompt
    prompt = (
        RAW_PROMPT.format(
            latex_template=latex_template,
            optimized_sections=optimized_sections_text,
            job_description=job_description,
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
        "cv-workspace", sections_file.replace(".optimized_sections.json", ".tex")
    )
    output_pdf_file = output_tex_file.replace(".tex", ".pdf")

    with open(output_tex_file, "w", encoding="utf-8") as f:
        f.write(latex_content.replace("```latex", "").replace("```", ""))

    console.print(f"[bold cyan]Compiling LaTeX file: {output_tex_file}[/bold cyan]")

    # Get the maximum number of correction attempts from config
    max_corrections = config.get("max_latex_corrections", 5)
    correction_attempts = 0
    compilation_successful = False

    # Compile LaTeX to PDF
    while not compilation_successful and correction_attempts <= max_corrections:
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
                f"[bold green]PDF successfully generated: {output_pdf_file}[/bold green]"
            )
            compilation_successful = True
        except subprocess.CalledProcessError as e:
            if correction_attempts < max_corrections:
                console.print(f"[bold red]Error during LaTeX compilation (attempt {correction_attempts + 1}/{max_corrections}): {e}[/bold red]")
                console.print(
                    f"[bold yellow]Attempting automatic LaTeX correction (attempt {correction_attempts + 1}/{max_corrections})...[/bold yellow]"
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
                    
                    latex_content = corrected_latex
                    correction_attempts += 1
                else:
                    console.print(
                        "[bold red]OpenAI could not correct the LaTeX document. Manual intervention required.[/bold red]"
                    )
                    break
            else:
                console.print(
                    f"[bold red]Maximum correction attempts ({max_corrections}) reached. Please review the LaTeX file manually.[/bold red]"
                )
                break

if __name__ == "__main__":
    generate_pdf()
