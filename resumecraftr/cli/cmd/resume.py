import os
import json
import click
import concurrent.futures
from rich.console import Console
from rich.prompt import Prompt
from cli.agent import execute_prompt
from cli.prompts.resume import RAW_PROMPTS

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
OUTPUT_FILE = "cv-workspace/{0}.optimized_sections.json"

@click.command()
def optimize_resume():
    """Optimize a resume based on a job description."""
    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print("[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]")
        return
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    job_descriptions = config.get("job_descriptions", [])
    extracted_files = config.get("extracted_files", [])
    
    if not extracted_files:
        console.print("[bold red]No extracted CV sections found in configuration.[/bold red]")
        return
    
    if not job_descriptions:
        console.print("[bold red]No job descriptions found in configuration.[/bold red]")
        return
    
    # Let the user choose files
    extracted_files = [f.replace('.txt', '.extracted_sections.json') for f in extracted_files]
    sections_file = extracted_files[0]
    job_desc_file = job_descriptions[0]
    
    if len(extracted_files) > 1:
        sections_file = Prompt.ask("Multiple extracted CV files detected. Choose one", choices=extracted_files)
    
    if len(job_descriptions) > 1:
        job_desc_file = Prompt.ask("Multiple job descriptions detected. Choose one", choices=job_descriptions)
    
    sections_path = os.path.abspath(os.path.join("cv-workspace", sections_file)) 
    job_desc_path = os.path.abspath(os.path.join("cv-workspace", "job_descriptions", job_desc_file)) 
    
    if not os.path.exists(sections_path):
        console.print(f"[bold red]Selected CV sections file '{sections_file}' does not exist.[/bold red]")
        return
    
    if not os.path.exists(job_desc_path):
        console.print(f"[bold red]Selected job description file '{job_desc_file}' does not exist.[/bold red]")
        return
    
    console.print(f"[bold blue]Optimizing resume using: {sections_file} and {job_desc_file}[/bold blue]")
    
    with open(sections_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            console.print(f"[bold red]Error: The CV sections file '{sections_file}' is empty.[/bold red]")
            return
        try:
            sections_content = json.loads(content)
        except json.JSONDecodeError as e:
            console.print(f"[bold red]Error: The CV sections file '{sections_file}' is not a valid JSON file.\nDetails: {e}[bold red]")
            return
    
    with open(job_desc_path, "r", encoding="utf-8") as f:
        job_description = f.read()
    
    console.print("[cyan]Processing optimization in parallel...[/cyan]")
    
    def optimize_section(section_name, content):
        prompt = RAW_PROMPTS["optimize_resume"] + "\n\n" + json.dumps({
            "section_name": section_name,
            "content": content,
            "job_description": job_description
        }, indent=4)
        return section_name, execute_prompt(prompt)
    
    optimized_resume = {}
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_section = {executor.submit(optimize_section, section, content): section for section, content in sections_content.items()}
        
        for future in concurrent.futures.as_completed(future_to_section):
            section_name, result = future.result()
            if result:
                optimized_resume[section_name] = result
    
    with open(OUTPUT_FILE.format(sections_file.replace(".txt", "").replace(".extracted_sections.json", "")), "w", encoding="utf-8") as f:
        json.dump(optimized_resume, f, indent=4)
    
    console.print(f"[bold green]Optimized resume saved to: {OUTPUT_FILE}[/bold green]")

if __name__ == "__main__":
    optimize_resume()
