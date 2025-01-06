import click
import os
import json
import subprocess
from rich.console import Console
from rich.prompt import Prompt
from cli.agent import execute_prompt
from cli.prompts.pdf import RAW_PROMPT

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
LATEX_TEMPLATE = "cv-workspace/resume_template.tex"

@click.command()
def generate_pdf():
    """Generate a PDF resume using the optimized LaTeX template with OpenAI."""
    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print("[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]")
        return
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    extracted_files = config.get("extracted_files", [])
    
    if not extracted_files:
        console.print("[bold red]No extracted CV sections found in configuration.[/bold red]")
        return
    
    extracted_files = [f.replace('.txt', '.optimized_sections.json') for f in extracted_files]
    sections_file = extracted_files[0]
    
    if len(extracted_files) > 1:
        sections_file = Prompt.ask("Multiple optimized CV files detected. Choose one", choices=extracted_files)
    
    sections_path = os.path.abspath(os.path.join("cv-workspace", sections_file))
    
    if not os.path.exists(sections_path):
        console.print(f"[bold red]Selected optimized sections file '{sections_file}' does not exist.[/bold red]")
        return
    
    console.print(f"[bold blue]Generating PDF using: {sections_file}[/bold blue]")
    
    with open(sections_path, "r", encoding="utf-8") as f:
        optimized_sections = json.load(f)
    
    # Load LaTeX template
    if not os.path.exists(LATEX_TEMPLATE):
        console.print(f"[bold red]LaTeX template '{LATEX_TEMPLATE}' not found.[/bold red]")
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
        console.print("[bold red]No job descriptions found in configuration.[/bold red]")
        return
    
    job_desc_path = os.path.abspath(os.path.join("cv-workspace", "job_descriptions", job_desc_files[0]))
    
    if not os.path.exists(job_desc_path):
        console.print(f"[bold red]Selected job description file '{job_desc_files[0]}' does not exist.[/bold red]")
        return
    
    with open(job_desc_path, "r", encoding="utf-8") as f:
        job_description = f.read()
    
    # 🔹 Convertir JSON a string para OpenAI
    optimized_sections_text = json.dumps(optimized_sections, indent=4, ensure_ascii=False)

    # 🔹 Generar el prompt
    prompt = RAW_PROMPT.format(
        latex_template=latex_template,
        cv_text=original_cv_text,
        optimized_sections=optimized_sections_text,
        job_description=job_description
    ).replace("{{", "{").replace("}}", "}")
    
    # 🔹 Generar LaTeX con OpenAI
    latex_content = execute_prompt(prompt)
    
    if not latex_content.strip():
        console.print("[bold red]Error: OpenAI did not return a valid LaTeX document.[/bold red]")
        return
    
    # Guardar el archivo .tex
    output_tex_file = os.path.join("cv-workspace", sections_file.replace(".optimized_sections.json", ".tex"))
    output_pdf_file = output_tex_file.replace(".tex", ".pdf")
    
    with open(output_tex_file, "w", encoding="utf-8") as f:
        f.write(latex_content)
    
    console.print(f"[bold cyan]Compiling LaTeX file: {output_tex_file}[/bold cyan]")
    
    # Compilar LaTeX a PDF
    try:
        subprocess.run(["xelatex", "-output-directory=cv-workspace", output_tex_file], check=True)
        console.print(f"[bold green]PDF successfully generated: {output_pdf_file}[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error during LaTeX compilation: {e}[bold red]")
        return

if __name__ == "__main__":
    generate_pdf()
