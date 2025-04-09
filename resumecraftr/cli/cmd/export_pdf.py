import click
import os
import json
import subprocess
import shutil
import time
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from resumecraftr.cli.agent import execute_prompt, create_or_get_agent
from resumecraftr.cli.prompts.pdf import MARKDOWN_PROMPT
import openai
from datetime import datetime

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

def check_latex_packages():
    """Check if required LaTeX packages are installed."""
    required_packages = [
        "biblatex",
        "csquotes",
        "enumitem",
        "fancyhdr",
        "geometry",
        "graphicx",
        "hyperref",
        "listings",
        "titlesec",
        "xcolor"
    ]
    
    # En sistemas Linux, es mejor asumir que los paquetes están instalados
    # si el usuario está usando el sistema, ya que la verificación puede dar falsos positivos
    if os.name == 'posix':  # Linux/Unix
        console.print("[bold yellow]Skipping LaTeX package verification on Linux system.[/bold yellow]")
        console.print("[bold yellow]If you encounter LaTeX errors, please install the required packages manually.[/bold yellow]")
        return []
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Try to compile a minimal LaTeX document that uses the package
            with open("temp_check.tex", "w") as f:
                f.write(f"\\documentclass{{article}}\n\\usepackage{{{package}}}\n\\begin{{document}}\nTest\n\\end{{document}}")
            
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "temp_check.tex"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            
            if result.returncode != 0:
                missing_packages.append(package)
        except Exception:
            missing_packages.append(package)
        finally:
            # Clean up temporary files
            for ext in [".aux", ".log", ".pdf"]:
                if os.path.exists(f"temp_check{ext}"):
                    os.remove(f"temp_check{ext}")
    
    return missing_packages

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

def print_latex_installation_guide(missing_packages):
    """Prints installation instructions for missing LaTeX packages."""
    instructions = f"""
# 🚀 Installing Required LaTeX Packages

ResumeCraftr requires the following LaTeX packages to generate PDFs:
{', '.join(missing_packages)}

### 🟢 Windows
1. Install a complete LaTeX distribution like [MiKTeX](https://miktex.org/download) or [TeX Live](https://tug.org/texlive/windows.html).
2. During installation, select "Install missing packages on the fly = Yes".

### 🍏 macOS
1. Install MacTeX:
   ```
   brew install --cask mactex
   ```
   Or for a smaller installation:
   ```
   brew install --cask basictex
   ```
2. After installation, open Terminal and run:
   ```
   sudo tlmgr update --self
   sudo tlmgr install {' '.join(missing_packages)}
   ```

### 🐧 Linux (Ubuntu/Debian)
```
sudo apt-get update
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-latex-recommended texlive-publishers texlive-science
```

For other distributions, install the appropriate TeX Live packages.

After installation, retry running `resumecraftr export-pdf`! ✅
"""
    console.print(Markdown(instructions))

@click.command()
@click.option(
    "--skip-md-gen",
    is_flag=True,
    help="Skip Markdown generation with OpenAI and use an existing Markdown file. Useful for debugging PDF generation issues.",
)
@click.option(
    "--language",
    type=str,
    help="Language to generate the resume in (e.g., 'en', 'es'). Defaults to the language in resumecraftr.json.",
)
@click.option(
    "--translate",
    is_flag=True,
    help="Generate the resume in a different language than the default.",
)
@click.option(
    "--target-language",
    type=str,
    help="Target language for translation (e.g., 'en', 'es'). Required if --translate is used.",
)
def export_pdf(
    skip_md_gen: bool = False,
    language: str = None,
    translate: bool = False,
    target_language: str = None,
):
    """Export a PDF resume using Pandoc."""
    if not check_pandoc():
        print_pandoc_installation_guide()
        return

    # Load configuration
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        console.print("[bold red]Configuration file not found. Please run 'resumecraftr init' first.[/bold red]")
        return
    except json.JSONDecodeError:
        console.print("[bold red]Invalid configuration file. Please run 'resumecraftr init' first.[/bold red]")
        return

    # Determine language
    if translate and target_language:
        language = target_language
    elif not language:
        language = config.get("default_language", "en")

    console.print(f"[bold blue]Generating resume in language: {language}[/bold blue]")

    # Only create the agent when we're about to use OpenAI
    if not skip_md_gen:
        create_or_get_agent()

    # Get the Markdown file to use
    if skip_md_gen:
        # Find existing Markdown files in the workspace that start with "openai-response"
        md_files = [f for f in os.listdir("cv-workspace") if f.endswith(".md") and f.startswith("openai-response")]
        
        if not md_files:
            console.print("[bold red]No OpenAI response Markdown files found in cv-workspace directory.[/bold red]")
            return
            
        if len(md_files) > 1:
            # Let user choose which Markdown file to use
            md_file = Prompt.ask(
                "Multiple OpenAI response files detected. Choose one", choices=md_files
            )
        else:
            md_file = md_files[0]
            
        output_md_file = os.path.join("cv-workspace", md_file)
        console.print(f"[bold blue]Using OpenAI response file: {md_file}[/bold blue]")
    else:
        # Normal flow - generate Markdown with OpenAI
        # Load the Markdown template
        try:
            with open(MD_TEMPLATE, "r", encoding="utf-8") as f:
                template = f.read()
        except FileNotFoundError:
            console.print("[bold red]Markdown template not found.[/bold red]")
            return

        # Load the parsed CV sections
        try:
            # Find all optimized sections files
            sections_files = [f for f in os.listdir("cv-workspace") if f.endswith(".optimized_sections.json")]
            
            if not sections_files:
                console.print("[bold red]No optimized CV sections files found. Please run 'resumecraftr tailor-cv' first.[/bold red]")
                return
                
            if len(sections_files) > 1:
                # Let user choose which sections file to use
                sections_file = Prompt.ask(
                    "Multiple optimized CV files detected. Choose one", choices=sections_files
                )
            else:
                sections_file = sections_files[0]
                
            with open(f"cv-workspace/{sections_file}", "r", encoding="utf-8") as f:
                cv_sections = json.load(f)
        except FileNotFoundError:
            console.print("[bold red]Selected CV sections file not found.[/bold red]")
            return
        except json.JSONDecodeError:
            console.print("[bold red]Invalid CV sections file.[/bold red]")
            return

        # Load the job description
        try:
            # Find all job description files
            job_files = [f for f in os.listdir("cv-workspace/job_descriptions") if f.endswith(".txt")]
            
            if not job_files:
                console.print("[bold red]No job description files found. Please run 'resumecraftr add-job' first.[/bold red]")
                return
                
            if len(job_files) > 1:
                # Let user choose which job description to use
                job_file = Prompt.ask(
                    "Multiple job descriptions detected. Choose one", choices=job_files
                )
            else:
                job_file = job_files[0]
                
            with open(f"cv-workspace/job_descriptions/{job_file}", "r", encoding="utf-8") as f:
                job_description = f.read()
        except FileNotFoundError:
            console.print("[bold red]Selected job description file not found.[/bold red]")
            return

        # Load the tailored CV if it exists
        tailored_cv_path = "cv-workspace/tailored/tailored_cv.json"
        if os.path.exists(tailored_cv_path):
            try:
                with open(tailored_cv_path, "r", encoding="utf-8") as f:
                    tailored_cv = json.load(f)
            except json.JSONDecodeError:
                console.print("[bold red]Invalid tailored CV file.[/bold red]")
                return
        else:
            tailored_cv = None

        # Prepare the prompt
        prompt = MARKDOWN_PROMPT.format(
            template=template,
            cv_sections=json.dumps(cv_sections, indent=2),
            job_description=job_description,
            tailored_cv=json.dumps(tailored_cv, indent=2) if tailored_cv else "None",
            language=language,
        )

        # Generate the Markdown content
        try:
            # Generate Markdown with the agent
            markdown_content = execute_prompt(prompt)
            
            if not markdown_content.strip():
                console.print("[bold red]Error: OpenAI did not return a valid Markdown document.[/bold red]")
                return

            # Save the OpenAI response
            output_md_file = os.path.join(
                "cv-workspace",
                f"openai-response-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md",
            )
            with open(output_md_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            console.print(f"[bold green]Markdown content saved to: {output_md_file}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error generating Markdown content: {e}[/bold red]")
            return

    # Get the base name of the sections file for the PDF output
    sections_base_name = os.path.splitext(sections_file)[0].replace("_optimized_sections", "")
    output_pdf_file = os.path.join("cv-workspace", f"{sections_base_name}_{language.lower()}.pdf")

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
            "--variable", "documentclass=article",
            "--variable", "mainfont=DejaVu Sans",
            "--variable", "sansfont=DejaVu Sans",
            "--variable", "monofont=DejaVu Sans Mono",
            "--variable", "fontsize=11pt",
            "--variable", "geometry=margin=2.5cm",
            "--variable", "linestretch=1.25",
            "--variable", "header-includes=\\usepackage[utf8]{inputenc}\\usepackage[T1]{fontenc}\\usepackage{hyperref}\\usepackage{listings}\\usepackage{xcolor}",
            "--standalone",
            "--from", "markdown+yaml_metadata_block",
            "--to", "latex",
        ]
        
        result = subprocess.run(pandoc_cmd, check=False, capture_output=True, text=True)
        
        if result.returncode != 0:
            console.print(f"[bold red]Error during PDF export:[/bold red]")
            console.print(result.stderr)
            
            # Verificar si el error está relacionado con paquetes LaTeX faltantes
            if "biblatex.sty not found" in result.stderr or "Package biblatex Error" in result.stderr:
                console.print("[bold red]Missing LaTeX packages detected.[/bold red]")
                console.print("[bold yellow]Please install the required LaTeX packages:[/bold yellow]")
                console.print("""
For Ubuntu/Debian:
```
sudo apt-get update
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-latex-recommended texlive-publishers texlive-science texlive-bibtex-extra biber
```

For Arch Linux:
```
sudo pacman -S texlive-most
```

For Fedora:
```
sudo dnf install texlive-scheme-full
```
""")
            else:
                console.print("[bold yellow]You can edit the Markdown file manually and try again.[/bold yellow]")
            return
        
        console.print(
            f"[bold green]PDF successfully exported: {output_pdf_file}[/bold green]"
        )
    except Exception as e:
        console.print(f"[bold red]Error during PDF export: {e}[/bold red]")
        console.print(
            "[bold yellow]You can edit the Markdown file manually and try again.[/bold yellow]"
        )

if __name__ == "__main__":
    export_pdf() 