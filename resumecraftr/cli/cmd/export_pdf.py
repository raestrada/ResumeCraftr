import click
import os
import json
import subprocess
import shutil
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from resumecraftr.cli.agent import execute_prompt, create_or_get_agent
from resumecraftr.cli.prompts.pdf import MARKDOWN_PROMPT

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
MD_TEMPLATE = "cv-workspace/resume_template.md"
CUSTOM_PROMPT = "cv-workspace/custom.md"
EISVOGEL_TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "templates", "eisvogel.latex")
PANDOC_TEMPLATES_DIR = os.path.expanduser("~/.local/share/pandoc/templates")

def check_pandoc():
    """Check if pandoc is installed and provide installation instructions if not."""
    try:
        subprocess.run(
            ["pandoc", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def ensure_eisvogel_template():
    """Ensure the eisvogel template is available in the pandoc templates directory."""
    # Create pandoc templates directory if it doesn't exist
    os.makedirs(PANDOC_TEMPLATES_DIR, exist_ok=True)
    
    # Check if eisvogel template already exists
    eisvogel_path = os.path.join(PANDOC_TEMPLATES_DIR, "eisvogel.latex")
    if not os.path.exists(eisvogel_path):
        # Copy the template from our package to the pandoc templates directory
        try:
            shutil.copy2(EISVOGEL_TEMPLATE, eisvogel_path)
            console.print("[bold green]Successfully installed eisvogel template.[/bold green]")
            return True
        except Exception as e:
            console.print(f"[bold red]Error installing eisvogel template: {e}[/bold red]")
            return False
    return True

def print_pandoc_installation_guide():
    """Prints installation instructions for Pandoc in Markdown format using rich."""
    instructions = """
# 🚀 Installing Pandoc

ResumeCraftr requires **Pandoc** to compile PDFs. Follow the instructions below for your system:

### 🟢 Windows
1. Download and install [Pandoc](https://pandoc.org/installing.html).
2. Ensure `pandoc` is in your system's PATH by running:
   ```
   pandoc --version
   ```
   If not, restart your computer or manually add the Pandoc directory to your PATH.

### 🍏 macOS
1. Install Pandoc via Homebrew:
   ```
   brew install pandoc
   ```
2. Verify the installation:
   ```
   pandoc --version
   ```

### 🐧 Linux
For Debian/Ubuntu:
   ```
   sudo apt update && sudo apt install pandoc
   ```
For Arch Linux:
   ```
   sudo pacman -S pandoc
   ```
For Fedora:
   ```
   sudo dnf install pandoc
   ```

After installation, re-run:
   ```
   pandoc --version
   ```

Once installed, retry running `resumecraftr export-pdf`! ✅
"""
    console.print(Markdown(instructions))

@click.command()
@click.option(
    "--translate",
    "-t",
    help="Translate the resume to a different language (e.g., EN, ES). If not provided, uses the language from resumecraftr.json",
)
def export_pdf(translate):
    """Export a PDF resume using Pandoc to convert from Markdown to PDF.
    
    By default, the resume will be generated in the language specified in resumecraftr.json.
    Use the --translate option to generate the resume in a different language.
    """
    # Only create the agent when we're about to use OpenAI
    create_or_get_agent("ResumeCraftr Agent PDF gen")

    if not check_pandoc():
        console.print("[bold red]Error: Pandoc is not installed.[/bold red]")
        print_pandoc_installation_guide()
        return

    # Ensure eisvogel template is available
    if not ensure_eisvogel_template():
        console.print("[bold red]Error: Failed to install eisvogel template.[/bold red]")
        return

    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr setup' first.[/bold red]"
        )
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Determine the language to use
    language = translate if translate else config.get("primary_language", "EN")
    console.print(f"[bold blue]Generating resume in language: {language}[/bold blue]")

    with open(CUSTOM_PROMPT, "r", encoding="utf-8") as f:
        custom_promt = f.readlines()

    extracted_files = config.get("extracted_files", [])
    if not extracted_files:
        console.print(
            "[bold red]No parsed CV sections found in configuration.[/bold red]"
        )
        return

    extracted_files = [
        f.replace(".txt", ".optimized_sections.json") for f in extracted_files
    ]
    sections_file = extracted_files[0]

    if len(extracted_files) > 1:
        sections_file = Prompt.ask(
            "Multiple tailored CV files detected. Choose one", choices=extracted_files
        )

    sections_path = os.path.abspath(os.path.join("cv-workspace", sections_file))
    if not os.path.exists(sections_path):
        console.print(
            f"[bold red]Selected tailored sections file '{sections_file}' does not exist.[/bold red]"
        )
        return

    console.print(f"[bold blue]Exporting PDF using: {sections_file}[/bold blue]")

    with open(sections_path, "r", encoding="utf-8") as f:
        optimized_sections = json.load(f)

    # Load Markdown template
    if not os.path.exists(MD_TEMPLATE):
        console.print(
            f"[bold red]Markdown template '{MD_TEMPLATE}' not found.[/bold red]"
        )
        return

    with open(MD_TEMPLATE, "r", encoding="utf-8") as f:
        md_template = f.read()

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

    # Convert JSON to string for OpenAI
    optimized_sections_text = json.dumps(
        optimized_sections, indent=4, ensure_ascii=False
    )

    # Generate the prompt
    prompt = (
        MARKDOWN_PROMPT.format(
            md_template=md_template,
            optimized_sections=optimized_sections_text,
            job_description=job_description,
            language=language,
            custom=custom_promt
        )
        .replace("{{", "{")
        .replace("}}", "}")
    )

    # Generate Markdown with OpenAI
    markdown_content = execute_prompt(prompt, "ResumeCraftr Agent PDF gen")

    if not markdown_content.strip():
        console.print(
            "[bold red]Error: OpenAI did not return a valid Markdown document.[/bold red]"
        )
        return

    # Save the Markdown file
    output_md_file = os.path.join(
        "cv-workspace", sections_file.replace(".optimized_sections.json", ".md")
    )
    # Add language suffix to PDF filename
    output_pdf_file = output_md_file.replace(".md", f"_{language.lower()}.pdf")

    with open(output_md_file, "w", encoding="utf-8") as f:
        f.write(markdown_content.replace("```markdown", "").replace("```", ""))

    console.print(f"[bold cyan]Converting Markdown to PDF: {output_md_file}[/bold cyan]")

    # Convert Markdown to PDF using Pandoc
    try:
        pandoc_cmd = [
            "pandoc",
            output_md_file,
            "-o", output_pdf_file,
            "--pdf-engine=xelatex",
            "--template=eisvogel",
            "--listings",
            "--toc",
            "--toc-depth=2",
            "--number-sections",
            "--highlight-style=tango",
            "--variable", "colorlinks:true",
            "--variable", "linkcolor:blue",
            "--variable", "urlcolor:blue",
            "--variable", "toccolor:blue",
        ]
        
        subprocess.run(pandoc_cmd, check=True)
        console.print(
            f"[bold green]PDF successfully exported: {output_pdf_file}[/bold green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error during PDF export: {e}[/bold red]")
        console.print(
            "[bold yellow]You can edit the Markdown file manually and try again.[/bold yellow]"
        )

if __name__ == "__main__":
    export_pdf() 