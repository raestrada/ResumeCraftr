import os
import json
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from resumecraftr.cli.prompts.sections import RAW_PROMPTS

console = Console()
CONFIG_FILE = os.path.join("cv-workspace", "resumecraftr.json")

def get_cv_path(cv_name):
    """Get the path to a CV JSON file."""
    # Save directly in cv-workspace directory
    return os.path.join("cv-workspace", f"dummy_{cv_name}.extracted_sections.json")

def load_cv(cv_name):
    """Load a CV from its JSON file."""
    cv_path = get_cv_path(cv_name)
    if not os.path.exists(cv_path):
        console.print(f"[bold red]CV '{cv_name}' does not exist.[/bold red]")
        return None
    
    with open(cv_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cv(cv_name, cv_data):
    """Save a CV to its JSON file."""
    cv_path = get_cv_path(cv_name)
    with open(cv_path, "w", encoding="utf-8") as f:
        json.dump(cv_data, f, indent=2, ensure_ascii=False)

def update_config_file(cv_name):
    """Update the resumecraftr.json file to include the new CV."""
    if not os.path.exists(CONFIG_FILE):
        console.print("[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]")
        return False
    
    try:
        # Read the current configuration
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Create a dummy text file path to simulate extraction
        dummy_txt_path = f"dummy_{cv_name}.txt"
        
        # Ensure the extracted_files section exists
        if "extracted_files" not in config:
            config["extracted_files"] = []
            console.print("[bold yellow]Created 'extracted_files' section in configuration.[/bold yellow]")
        
        # Add the dummy text file to the extracted_files list if it's not already there
        if dummy_txt_path not in config["extracted_files"]:
            config["extracted_files"].append(dummy_txt_path)
            console.print(f"[bold green]Added '{dummy_txt_path}' to extracted_files.[/bold green]")
        
        # Create a dummy text file to simulate extraction
        dummy_txt_full_path = os.path.join("cv-workspace", dummy_txt_path)
        with open(dummy_txt_full_path, "w", encoding="utf-8") as f:
            f.write(f"# {cv_name}\n\nThis is a dummy file created for CV '{cv_name}'")
        
        # Save the updated configuration
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Verify the update was successful
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            updated_config = json.load(f)
            if dummy_txt_path in updated_config.get("extracted_files", []):
                console.print("[bold green]Configuration file updated successfully.[/bold green]")
                return True
            else:
                console.print("[bold red]Failed to update configuration file.[/bold red]")
                return False
    except Exception as e:
        console.print(f"[bold red]Error updating configuration file: {str(e)}[/bold red]")
        return False

@click.command()
@click.argument("cv_name")
def create_cv(cv_name):
    """Create a new empty CV with the given name."""
    # Check if CV already exists
    cv_path = get_cv_path(cv_name)
    if os.path.exists(cv_path):
        if not Confirm.ask(f"CV '{cv_name}' already exists. Overwrite?"):
            return
    
    # Create empty CV with all sections initialized
    cv_data = {}
    for section in RAW_PROMPTS.keys():
        if section == "Contact Information":
            cv_data[section] = {
                "Full Name": None,
                "Email": None,
                "Phone Number": None,
                "LinkedIn": None,
                "GitHub": None,
                "Portfolio": None
            }
        elif section == "Summary":
            cv_data[section] = {"Summary": None}
        elif section == "Technical Skills":
            cv_data[section] = {
                "Programming Languages": [],
                "Tools and Technologies": []
            }
        else:
            cv_data[section] = []
    
    # Ensure cv-workspace directory exists
    os.makedirs("cv-workspace", exist_ok=True)
    
    # Save the CV
    save_cv(cv_name, cv_data)
    
    # Update the configuration file
    if update_config_file(cv_name):
        console.print(f"[bold green]CV '{cv_name}' created successfully and added to configuration.[/bold green]")
    else:
        console.print(f"[bold yellow]CV '{cv_name}' created, but there was an issue updating the configuration file.[/bold yellow]")

@click.command()
@click.argument("cv_name")
@click.argument("section")
def add_section(cv_name, section):
    """Add or update a section in a CV."""
    # Check if CV already exists
    cv_path = get_cv_path(cv_name)
    if not os.path.exists(cv_path):
        console.print(f"[bold red]CV '{cv_name}' does not exist. Create it first with 'create-cv {cv_name}'[/bold red]")
        return
    
    cv_data = load_cv(cv_name)
    
    if section not in RAW_PROMPTS:
        console.print(f"[bold red]Invalid section: {section}[/bold red]")
        console.print("Available sections:")
        for s in RAW_PROMPTS.keys():
            console.print(f"  - {s}")
        return
    
    # Handle different section types
    if section == "Contact Information":
        contact_info = {}
        for field in ["Full Name", "Email", "Phone Number", "LinkedIn", "GitHub", "Portfolio"]:
            value = Prompt.ask(f"Enter {field}", default=cv_data[section].get(field, ""))
            contact_info[field] = value if value else None
        cv_data[section] = contact_info
    
    elif section == "Summary":
        summary = Prompt.ask("Enter your professional summary", default=cv_data[section].get("Summary", ""))
        cv_data[section] = {"Summary": summary if summary else None}
    
    elif section == "Technical Skills":
        skills = {
            "Programming Languages": [],
            "Tools and Technologies": []
        }
        
        # Programming Languages
        languages = Prompt.ask("Enter programming languages (comma-separated)", 
                             default=",".join(cv_data[section].get("Programming Languages", [])))
        skills["Programming Languages"] = [lang.strip() for lang in languages.split(",") if lang.strip()]
        
        # Tools and Technologies
        tools = Prompt.ask("Enter tools and technologies (comma-separated)", 
                          default=",".join(cv_data[section].get("Tools and Technologies", [])))
        skills["Tools and Technologies"] = [tool.strip() for tool in tools.split(",") if tool.strip()]
        
        cv_data[section] = skills
    
    else:  # Work Experience, Projects, Education, etc.
        entries = cv_data[section]
        while True:
            entry = {}
            
            if section == "Work Experience":
                entry = {
                    "Job Title": Prompt.ask("Job Title", default=""),
                    "Company": Prompt.ask("Company", default=""),
                    "Dates of Employment": Prompt.ask("Dates", default=""),
                    "Responsibilities": []
                }
                while Confirm.ask("Add a responsibility?"):
                    resp = Prompt.ask("Responsibility")
                    entry["Responsibilities"].append(resp)
            
            elif section == "Projects":
                entry = {
                    "Project Name": Prompt.ask("Project Name", default=""),
                    "Description": Prompt.ask("Description", default=""),
                    "Technologies Used": []
                }
                while Confirm.ask("Add a technology used?"):
                    tech = Prompt.ask("Technology")
                    entry["Technologies Used"].append(tech)
            
            elif section == "Education":
                entry = {
                    "Degree": Prompt.ask("Degree", default=""),
                    "Institution": Prompt.ask("Institution", default=""),
                    "Graduation Years": Prompt.ask("Graduation Years", default="")
                }
            
            elif section == "Certifications":
                entry = {
                    "Certification Name": Prompt.ask("Certification Name", default=""),
                    "Issuing Organization": Prompt.ask("Issuing Organization", default=""),
                    "Date": Prompt.ask("Date", default="")
                }
            
            elif section == "Publications & Open Source Contributions":
                entry = {
                    "Title": Prompt.ask("Title", default=""),
                    "Details": Prompt.ask("Details", default="")
                }
            
            elif section == "Awards & Recognitions":
                entry = {
                    "Award Name": Prompt.ask("Award Name", default=""),
                    "Description": Prompt.ask("Description", default=""),
                    "Date": Prompt.ask("Date", default="")
                }
            
            elif section == "Languages":
                entry = {
                    "Language": Prompt.ask("Language", default=""),
                    "Proficiency": Prompt.ask("Proficiency", default="")
                }
            
            entries.append(entry)
            
            if not Confirm.ask("Add another entry?"):
                break
        
        cv_data[section] = entries
    
    save_cv(cv_name, cv_data)
    console.print(f"[bold green]Updated section '{section}' in CV '{cv_name}'[/bold green]")

@click.command()
@click.argument("cv_name")
def show_cv(cv_name):
    """Display the contents of a CV."""
    # Check if CV already exists
    cv_path = get_cv_path(cv_name)
    if not os.path.exists(cv_path):
        console.print(f"[bold red]CV '{cv_name}' does not exist. Create it first with 'create-cv {cv_name}'[/bold red]")
        return
    
    cv_data = load_cv(cv_name)
    
    for section, content in cv_data.items():
        console.print(Panel.fit(
            json.dumps(content, indent=2, ensure_ascii=False),
            title=f"[bold blue]{section}[/bold blue]"
        )) 