# Getting Started with ResumeCraftr

ResumeCraftr is an ATS-focused minimalist CV generator that now leverages LangChain graph pipelines, an embedded ChromaDB store, and PyMuPDF to parse, optimize, and format resumes using only Python-native tooling. This guide walks you through the modernized setup and usage of ResumeCraftr, along with tips for customizing your experience.

---

## 🚀 What's New?

### 🌟 Now with Windows Support! 🖥️

ResumeCraftr now fully supports Windows, making it easier for more users to optimize their resumes across different platforms.

### 🌟 New Interactive CV Creation! 📝

ResumeCraftr now allows you to create and manage CV sections interactively without needing to parse an existing CV. This makes it easier to build your resume from scratch or update specific sections.

### 🌟 Embedded RAG & PyMuPDF! 📄

ResumeCraftr now routes every LLM call through LangChain/ LangGraph, persists knowledge in an on-disk ChromaDB (SQLite) store, and renders PDFs directly through PyMuPDF for precise styling.

---

## Installation

Ensure you have `pipx` installed, then install ResumeCraftr with:

```bash
pipx install git+https://github.com/raestrada/ResumeCraftr.git@v0.8.1-beta4
```

PyMuPDF ships with the project, so there is no longer a dependency on Pandoc or LaTeX. You only need:

- Python 3.10+ (3.11 recommended)
- The appropriate API keys in your environment (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, or local Ollama)
- Basic shell access to export your provider credentials before running the CLI

### Configuring provider API keys

All providers are resolved via LangChain, so credentials live in standard environment variables:

```bash
# OpenRouter (recommended for multi-model routing)
export OPENROUTER_API_KEY="sk-or-v1..."

# OpenAI (only if you selected --provider openai)
export OPENAI_API_KEY="sk-proj-..."

# Optional: override LangChain's base URL for OpenRouter (only needed if you use custom routing)
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
```

Prefer not to export environment variables? Create `~/.resumecraftr/openrouter_api_key.txt` and paste your OpenRouter key inside—ResumeCraftr will load it from that file first and fall back to the env vars. On Windows PowerShell, use `$env:OPENROUTER_API_KEY = "sk-or-v1..."`. Storing secrets in a `.env` file also works because the CLI loads dotenv automatically at startup.

---

## Initializing Your Workspace

ResumeCraftr operates within a dedicated workspace directory called `cv-workspace`. To set up this workspace, run:

```bash
resumecraftr setup --language EN --provider openrouter --model deepseek/deepseek-chat
```

### Key Options:
- `--language`: Sets the primary language of your CV (e.g., `EN` for English or `ES` for Spanish).
- `--provider`: Selects the LangChain provider (`openai`, `openrouter`, or `ollama`).
- `--model`: Specifies the model string compatible with the chosen provider (defaults to `deepseek/deepseek-chat`).
- `--temperature`: Controls the creativity of generations (default `0.4`).

This will create the `cv-workspace` directory with:
- **`cv-workspace/resumecraftr.json`**: The main configuration file (see below).
- **`cv-workspace/custom.md`**: A file for supplementary information and custom instructions.
- **`cv-workspace/job_descriptions/`** and **`cv-workspace/output/`** directories.

---

### Understanding `resumecraftr.json`

Here's an example of a `resumecraftr.json` configuration file:

```json
{
    "primary_language": "EN",
    "llm": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-chat",
        "temperature": 0.4,
        "max_tokens": 1200
    },
    "retrieval": {
        "persist_directory": ".chroma",
        "embedding_provider": "huggingface",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "chunk_size": 900,
        "chunk_overlap": 200
    },
    "pdf": {
        "font": "helv",
        "heading_font_size": 14,
        "body_font_size": 11,
        "margin": 54
    },
    "extracted_files": [
        "Rodrigo Estrada CV EN.txt"
    ],
    "job_descriptions": [
        "Principal Engineer Verne.txt"
    ]
}
```

- **`llm`**: LangChain provider/model/temperature/max tokens used for all generations.
- **`retrieval`**: Embedded ChromaDB settings plus embedding model/provider.
- **`pdf`**: Styling knobs consumed by the PyMuPDF renderer.
- **`extracted_files`** & **`job_descriptions`**: Workspace bookkeeping for imported resumes and stored jobs.

---

### `custom.md`

The `custom.md` file is a powerful tool where you can add:
- **Supplementary information** that may not be in your CV (e.g., achievements, side projects).
- **Additional instructions** for ChatGPT to tailor the CV optimization further.

Make sure to keep this file updated with relevant details to enhance your CV optimization process.

---

## Creating a CV from Scratch

ResumeCraftr now allows you to create a CV from scratch without needing to parse an existing document. This is useful for building a new resume or updating specific sections.

### Creating a New CV

To create a new CV, run:

```bash
resumecraftr new-cv my_cv
```

This command creates a new CV with the name `my_cv` and initializes all sections with empty values.

### Available Sections

ResumeCraftr supports the following sections that you can add to your CV:

1. **Contact Information** - Personal details like name, email, phone, location, and website
2. **Professional Summary** - A brief overview of your professional background and career objectives
3. **Work Experience** - Detailed information about your employment history
4. **Education** - Academic background, degrees, and certifications
5. **Skills** - Technical and soft skills relevant to your field
6. **Projects** - Notable projects you've worked on
7. **Publications** - Any articles, papers, or books you've authored
8. **Awards & Achievements** - Recognition and accomplishments
9. **Languages** - Language proficiencies
10. **Volunteer Experience** - Community service and volunteer work
11. **References** - Professional references (optional)
12. **Custom Section** - Any additional section you'd like to include

### Adding or Updating Sections

To add or update a specific section in your CV, run:

```bash
resumecraftr edit-section my_cv "Work Experience"
```

This command will guide you through the process of adding or updating the specified section. You can add multiple entries for sections like Work Experience, Projects, Education, etc.

### Viewing Your CV

To view the contents of your CV, run:

```bash
resumecraftr view-cv my_cv
```

This command displays all sections of your CV in a structured format.

---

## Importing and Parsing Resumes

ResumeCraftr can import text from supported document formats (`.pdf`, `.docx`, `.txt`, `.md`). Place your CV inside `cv-workspace` and run:

```bash
resumecraftr import-cv /path/to/Resume.pdf
```

This will generate a `.txt` file containing the extracted raw text.

### Parsing into Structured Sections

To classify the imported resume text into structured sections such as contact details, experience, skills, and education, use:

```bash
resumecraftr parse-cv
```

This command creates an `.extracted_sections.json` file, which contains a structured version of your CV, making it easier to optimize.

---

## Adding a Job Description and Tailoring Your Resume

### Adding a Job Description
To tailor your resume for a specific job description, run:

```bash
resumecraftr add-job
```

This will prompt you to either paste the job description directly or provide a file containing the job description.

### Tailoring the Resume
After adding the job description, tailor the resume with:

```bash
resumecraftr tailor-cv
```

This step ensures that your resume highlights relevant skills and experience based on the job description. ResumeCraftr now routes the optimization through a LangChain + LangGraph pipeline backed by ChromaDB retrieval, so every section is grounded in your workspace knowledge base.

### Language Optimization

One of the key benefits of the tailor command is that it rewrites all content in the language you configured during initialization. This means:

- **Grammar and Spelling**: The AI automatically corrects grammatical errors and spelling mistakes
- **Language Consistency**: Ensures all content follows the same language style and conventions
- **Professional Tone**: Adjusts the writing to maintain a professional tone appropriate for resumes
- **Cultural Adaptation**: Adapts content to match the cultural expectations of the target language

For example, if you configured ResumeCraftr with `--language ES` (Spanish), the tailor command will rewrite your resume in proper Spanish, correcting any language errors and ensuring it follows Spanish resume conventions.

---

## Exporting Your Resume to PDF

Once you're satisfied with your resume, you can export it to PDF using PyMuPDF:

```bash
# Use the default (latest) tailored sections and bundled template
resumecraftr export-pdf

# Specify sections file, template, and destination
resumecraftr export-pdf \
  --sections senior-role.tailored_sections.json \
  --template modern \
  --output output/senior-role.pdf

# Translate first, then render (example: French)
resumecraftr export-pdf --template minimal --translate FR
```

The command will:
1. Find tailored/optimized section files inside `cv-workspace`
2. Prompt you to pick one if multiple exist
3. Ask for a template if you haven't specified one (workspace templates take priority)
4. Render the sections into a styled HTML resume and convert it to PDF under `cv-workspace/output`

Exports are saved using deterministic filenames derived from the candidate name, template, language, and job slug, e.g. `jdoe_modern_es_principal-engineer.pdf`. Re-running the same template simply overwrites the previous file. When `--translate` is provided, the translated JSON is cached next to the tailored sections (`my_cv.tailored_sections.es.translated.json`) to speed up subsequent renders.

### 5. Exportar a PDF
```bash
# Exportar usando la última versión y el template por defecto
resumecraftr export-pdf

# Exportar eligiendo secciones y template personalizados
resumecraftr export-pdf --sections mi_cv.tailored_sections.json --template modern --output cv-final.pdf

# Traducir a otro idioma antes de exportar
resumecraftr export-pdf --template executive --translate ES
```

### Custom templates

You can override the packaged HTML templates by creating `cv-workspace/templates/pdf/` and dropping your own `.html` files there.

1. Copy the bundled `modern.html` into that directory (the CLI copies it automatically during setup).
2. Tweak the CSS/HTML to match your desired layout.
3. Export with `resumecraftr export-pdf --template my_template`.

The CLI searches the workspace directory first, then falls back to the bundled templates.
