import os
import glob
import time
import openai
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress

console = Console()
client = OpenAI()

CV_WORKSPACE = "cv-workspace"
SUPPORTED_EXTENSIONS = (".md", ".txt", ".doc", ".docx", ".pdf")


def get_vector_store_id_by_name(agent_name: str) -> str:
    """Retrieve the vector store ID by the agent's name."""
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
    """Load all supported document files from the given directory and subdirectories."""
    console.print(f"[bold blue]Loading documents from '{directory}'...[/bold blue]")
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(glob.glob(f"{directory}/**/*{ext}", recursive=True))
    return files


def upload_files_to_vector_store(
    vector_store_id: str, progress: Progress = None, task=None
):
    """Upload all supported files to the specified vector store."""
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


def create_or_get_agent():
    """Create or retrieve an assistant for document processing."""
    agent_name = "ResumeCraftr Agent"

    assistants = client.beta.assistants.list()
    for assistant in assistants.data:
        if assistant.name == agent_name:
            return assistant

    console.print(
        f"[bold yellow]Agent '{agent_name}' not exists, creating.[/bold yellow]"
    )

    vector_store = client.beta.vector_stores.create(name=f"{agent_name} Docs")
    upload_files_to_vector_store(vector_store.id)

    assistant = client.beta.assistants.create(
        instructions="Process resumes with ATS optimization techniques.",
        name=agent_name,
        tools=[{"type": "file_search"}],
        model="gpt-4o",
        temperature=0.7,
        top_p=1.0,
    )

    client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    console.print(
        f"[bold green]Agent '{agent_name}' created successfully.[/bold green]"
    )
    return assistant


def execute_prompt(prompt: str) -> str:
    """Execute a given prompt using the AI agent, ensuring the vector database is refreshed."""
    assistant = create_or_get_agent()

    """Execute a given prompt using the AI agent."""
    assistant = create_or_get_agent()
    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=prompt
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant.id
    )
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value
