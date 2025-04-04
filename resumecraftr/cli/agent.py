import os
import glob
import time
import json
from dotenv import load_dotenv
from openai import OpenAI
from openai import OpenAIError
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt

load_dotenv()

console = Console()
CV_WORKSPACE = "cv-workspace"
SUPPORTED_EXTENSIONS = (".md", ".txt", ".doc", ".docx", ".pdf")
CONFIG_FILE = "cv-workspace/resumecraftr.json"

class OpenAIClientSingleton:
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_client(self):
        if self._client is None:
            try:
                self._client = OpenAI()
                # Test the client with a simple API call
                self._client.models.list()
            except OpenAIError as e:
                if "api_key" in str(e).lower():
                    console.print("[bold red]Error: OpenAI API key not found or invalid.[/bold red]")
                    api_key = Prompt.ask("[bold yellow]Please enter your OpenAI API key[/bold yellow]")
                    os.environ["OPENAI_API_KEY"] = api_key
                    # Try again with the new key
                    try:
                        self._client = OpenAI()
                        self._client.models.list()
                        console.print("[bold green]Successfully connected to OpenAI with the new API key![/bold green]")
                    except OpenAIError as retry_error:
                        console.print(f"[bold red]Error: Still unable to connect to OpenAI: {str(retry_error)}[/bold red]")
                        raise
                else:
                    console.print(f"[bold red]Error connecting to OpenAI: {str(e)}[/bold red]")
                    raise
        return self._client

def get_openai_client():
    """Get an initialized OpenAI client using the Singleton pattern."""
    return OpenAIClientSingleton.get_instance().get_client()

def delete_all_resumecraftr_agents():
    """
    Deletes all OpenAI agents whose names start with 'ResumeCraftr'.

    Returns:
        None
    """
    try:
        client = get_openai_client()
        console.print("[bold cyan]Fetching agents to delete those starting with 'ResumeCraftr'...[/bold cyan]")
        agents = client.beta.assistants.list()
        matching_agents = [agent for agent in agents.data if agent.name.startswith("ResumeCraftr")]

        if not matching_agents:
            console.print("[bold yellow]No agents found starting with 'ResumeCraftr'.[/bold yellow]")
            return

        for agent in matching_agents:
            console.print(f"[bold yellow]Deleting agent '{agent.name}'...[/bold yellow]")
            client.beta.assistants.delete(assistant_id=agent.id)
            console.print(f"[bold green]Agent '{agent.name}' successfully deleted![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error deleting agents: {e}[/bold red]")

def get_vector_store_id_by_name(agent_name: str) -> str:
    """
    Retrieve the vector store ID by the agent's name.

    Args:
        agent_name (str): The name of the agent.

    Returns:
        str: The ID of the vector store.
    """
    client = get_openai_client()
    vector_stores = client.beta.vector_stores.list()
    expected_name = f"{agent_name} Docs"

    for vector_store in vector_stores.data:
        if vector_store.name == expected_name:
            return vector_store.id

    console.print(
        f"[bold red]No vector store found with name '{expected_name}'.[/bold red]"
    )
    return None

def load_supported_files(directory: str) -> list:
    """
    Load all supported document files from the given directory and subdirectories.

    Args:
        directory (str): The directory to search for files.

    Returns:
        list: A list of file paths.
    """
    console.print(f"[bold blue]Loading documents from '{directory}'...[/bold blue]")
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(glob.glob(f"{directory}/**/*{ext}", recursive=True))
    return files

def upload_files_to_vector_store(
    vector_store_id: str, progress: Progress = None, task=None
):
    """
    Upload all supported files to the specified vector store.

    Args:
        vector_store_id (str): The ID of the vector store.
        progress (Progress, optional): The progress object for displaying progress.
        task (optional): The task object for updating progress.

    Returns:
        None
    """
    client = get_openai_client()
    files = load_supported_files(CV_WORKSPACE)

    if not files:
        console.print("[bold yellow]No supported files found to upload.[/bold yellow]")
        return

    file_streams = [open(file, "rb") for file in files]
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store_id, files=file_streams
    )

    while file_batch.status in ["queued", "in_progress"]:
        status_message = f"{file_batch.status}..."
        if progress and task:
            progress.update(task, description=status_message)
        else:
            console.print(f"[bold yellow]{status_message}[/bold yellow]")
        time.sleep(1)

    console.print(
        f"[bold green]Files uploaded successfully to vector store '{vector_store_id}'.[/bold green]"
    )

def create_or_get_agent(name=None):
    """
    Create or retrieve an assistant for document processing.

    Args:
        name (str, optional): The name of the agent. Defaults to None.

    Returns:
        assistant: The created or retrieved assistant.
    """
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]"
        )
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    agent_name = "ResumeCraftr Agent" if name is None else name
    
    # Only initialize OpenAI client when needed
    client = get_openai_client()

    assistants = client.beta.assistants.list()
    for assistant in assistants.data:
        if assistant.name == agent_name:
            return assistant

    console.print(
        f"[bold yellow]Agent '{agent_name}' not exists, creating.[/bold yellow]"
    )

    vector_store = client.beta.vector_stores.create(name=f"{agent_name} Docs")
    if agent_name == "ResumeCraftr Agent":
        upload_files_to_vector_store(vector_store.id)

    assistant = client.beta.assistants.create(
        instructions="Process resumes with ATS optimization techniques.",
        name=agent_name,
        tools=[{"type": "file_search"}],
        model=config["chat_gpt"]["model"],
        temperature=config["chat_gpt"]["temperature"],
        top_p=config["chat_gpt"]["top_p"],
    )

    if agent_name == "ResumeCraftr Agent":
        client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )

    console.print(
        f"[bold green]Agent '{agent_name}' created successfully.[/bold green]"
    )
    return assistant

def execute_prompt(prompt: str, name=None) -> str:
    """
    Execute a given prompt using the AI agent, ensuring the vector database is refreshed.
    Provides real-time feedback to the user using Rich.

    Args:
        prompt (str): The prompt to send to the AI agent.
        name (str, optional): The name of the agent. Defaults to None.

    Returns:
        str: The response from the AI agent.
    """
    # Only initialize OpenAI client when needed
    client = get_openai_client()
    assistant = create_or_get_agent(name)
    thread = client.beta.threads.create()

    console.print("[bold cyan]🔄 Sending prompt to OpenAI...[/bold cyan]")

    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=prompt
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant.id
    )

    console.print("[yellow]⏳ Waiting for OpenAI response...[/yellow]")

    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(1)

    console.print("[bold green]✅ Response received![/bold green]")

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    response = messages.data[0].content[0].text.value

    if response.strip() == prompt.strip():
        console.print(
            "[bold red]⚠️ Error: OpenAI credits may have run out, as the response is identical to the prompt.[/bold red]"
        )
        raise RuntimeError(
            "OpenAI response is identical to the prompt. Possible credit exhaustion."
        )

    console.print("[bold green]✅ Processing completed successfully![/bold green]")

    return response
