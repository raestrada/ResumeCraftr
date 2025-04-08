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
    "--translate",
    "-t",
    help="Translate the resume to a different language (e.g., EN, ES). If not provided, uses the language from resumecraftr.json",
)
@click.option(
    "--skip-md-gen",
    "-s",
    is_flag=True,
    help="Skip Markdown generation with OpenAI and use an existing Markdown file. Useful for debugging PDF generation issues.",
)
def export_pdf(translate, skip_md_gen):
    """Export a PDF resume using Pandoc to convert from Markdown to PDF.
    
    By default, the resume will be generated in the language specified in resumecraftr.json.
    Use the --translate option to generate the resume in a different language.
    Use the --skip-md-gen option to skip OpenAI Markdown generation and use an existing file.
    """
    # Only create the agent when we're about to use OpenAI
    if not skip_md_gen:
        create_or_get_agent("ResumeCraftr Agent PDF gen")

    if not check_pandoc():
        console.print("[bold red]Error: Pandoc is not installed.[/bold red]")
        print_pandoc_installation_guide()
        return

    # Check for required LaTeX packages
    missing_packages = check_latex_packages()
    if missing_packages:
        console.print(f"[bold red]Error: Missing required LaTeX packages: {', '.join(missing_packages)}[/bold red]")
        print_latex_installation_guide(missing_packages)
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
        
        # Add language suffix to PDF filename
        output_pdf_file = output_md_file.replace(".md", f"_{language.lower()}.pdf")

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
    else:
        # Normal flow - generate Markdown with OpenAI
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

        # Load consolidated Markdown if it exists
        consolidated_md = None
        consolidated_md_path = os.path.join("cv-workspace", "Rodrigo Estrada CV EN.md")
        if os.path.exists(consolidated_md_path):
            with open(consolidated_md_path, "r", encoding="utf-8") as f:
                consolidated_md = f.read()
            console.print(f"[bold green]Found consolidated Markdown file: {consolidated_md_path}[/bold green]")

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
        prompt = f"""
You are an expert at generating Markdown documents for ATS-friendly resumes. Your task is to generate a well-formatted Markdown file based on the provided CV text, optimized CV sections, and the job description.

IMPORTANT: DO NOT GENERATE LOREM IPSUM OR PLACEHOLDER TEXT. Use ONLY the actual content from the provided data.

### Instructions:
1. Use the provided **Markdown template** structure to generate the final document.
2. Use the **consolidated Markdown** as your primary source of content. This is the most up-to-date version of the CV.
3. Use the **optimized CV sections** and **job description** to enhance and tailor the content, but maintain the structure and information from the consolidated Markdown.
4. Ensure all sections from the consolidated Markdown are preserved.
5. Do not introduce new information that doesn't exist in the provided data.
6. Generate the resume in {language}.

### Consolidated Markdown (USE THIS AS PRIMARY SOURCE):
```markdown
{consolidated_md if consolidated_md else "No consolidated Markdown available"}
```

### Optimized CV Sections (USE TO ENHANCE CONTENT):
```json
{optimized_sections_text}
```

### Job Description (USE FOR TAILORING):
```
{job_description}
```

### Output:
Provide ONLY the final Markdown file content in {language}, properly formatted and ready for conversion to PDF using Pandoc. Do not include any explanations or code blocks.
"""

        # Generate Markdown with OpenAI
        console.print("[bold cyan]Generating Markdown content with OpenAI...[/bold cyan]")
        markdown_content = execute_prompt(prompt, "ResumeCraftr Agent PDF gen")

        if not markdown_content.strip():
            console.print(
                "[bold red]Error: OpenAI did not return a valid Markdown document.[/bold red]"
            )
            return

        # Save the OpenAI response to a file with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        openai_response_file = os.path.join("cv-workspace", f"openai-response-{timestamp}.md")
        with open(openai_response_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        console.print(f"[bold yellow]OpenAI response saved to: {openai_response_file}[/bold yellow]")

        # Save the Markdown file
        with open(output_md_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        console.print(f"[bold green]Markdown content saved to: {output_md_file}[/bold green]")

        # Add language suffix to PDF filename
        output_pdf_file = output_md_file.replace(".md", f"_{language.lower()}.pdf")

        console.print(f"[bold cyan]Converting Markdown to PDF: {output_md_file}[/bold cyan]")

        # Convert Markdown to PDF using Pandoc
        try:
            # Create a temporary file with the exact content we want to convert
            temp_md_file = os.path.join("cv-workspace", "temp_for_pandoc.md")
            with open(temp_md_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                
            pandoc_cmd = [
                "pandoc",
                temp_md_file,  # Use the temporary file instead of output_md_file
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
            
            result = subprocess.run(pandoc_cmd, check=False, capture_output=True, text=True)
            
            # Clean up the temporary file
            if os.path.exists(temp_md_file):
                os.remove(temp_md_file)
            
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