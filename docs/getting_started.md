# Getting Started with ResumeCraftr

ResumeCraftr is an ATS-focused minimalist CV generator that leverages OpenAI and LaTeX to parse, optimize, and format resumes. This guide will walk you through the setup and usage of ResumeCraftr, along with tips for customizing your experience.

---

## Installation

Ensure you have `pipx` installed, then install ResumeCraftr with:

```bash
pipx install git+https://github.com/raestrada/ResumeCraftr.git@v0.1.0
```

Additionally, make sure you have a LaTeX distribution installed, specifically one that includes `xelatex`.

---

## Initializing Your Workspace

ResumeCraftr operates within a dedicated workspace directory called `cv-workspace`. To set up this workspace, run:

```bash
resumecraftr init --language EN --gpt-model gpt-4o-mini
```

### Key Options:
- `--language`: Sets the primary language of your CV (e.g., `EN` for English or `ES` for Spanish).
- `--gpt-model`: Specifies the GPT model to use. For testing, we recommend using `gpt-4o-mini`.

This will create the `cv-workspace` directory with the following files:
- **`cv-workspace/resume_template.tex`**: The LaTeX template used for PDF generation. You can modify this file to customize the CV layout and style.
- **`cv-workspace/resumecraftr.json`**: The main configuration file.
- **`cv-workspace/custom.md`**: A file for adding supplementary information and custom instructions for ChatGPT.

---

### Understanding `resumecraftr.json`

Here’s an example of a `resumecraftr.json` configuration file:

```json
{
    "primary_language": "ES",
    "output_format": "pdf",
    "template_name": "resume_template.tex",
    "chat_gpt": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "top_p": 1.0
    },
    "extracted_files": [
        "Rodrigo Estrada CV ES.txt"
    ],
    "job_descriptions": [
        "Principal Engineer Verne.txt"
    ]
}
```

- **`primary_language`**: The language of the CV and job descriptions (e.g., `EN`, `ES`).
- **`output_format`**: Output format, typically `pdf`.
- **`template_name`**: Name of the LaTeX template used for PDF generation.
- **`chat_gpt`**: OpenAI settings such as the model, temperature, and top_p.
- **`extracted_files`**: List of extracted text files from your CVs.
- **`job_descriptions`**: List of job description files used for optimization.

---

### `custom.md`

The `custom.md` file is a powerful tool where you can add:
- **Supplementary information** that may not be in your CV (e.g., achievements, side projects).
- **Additional instructions** for ChatGPT to tailor the CV optimization further.

Make sure to keep this file updated with relevant details to enhance your CV optimization process.

---

## Extracting Resume Text

ResumeCraftr can extract text from supported document formats (`.pdf`, `.docx`, `.txt`, `.md`). Place your CV inside `cv-workspace` and run:

```bash
resumecraftr extract /path/to/Resume.pdf
```

This will generate a `.txt` file containing the extracted raw text.

---

## Extracting Structured Sections

To classify the extracted resume text into structured sections such as contact details, experience, skills, and education, use:

```bash
resumecraftr extract-sections
```

This command creates an `.optimized_sections.json` file, which contains a structured version of your CV, making it easier to optimize.

---

## Adding a Job Description and Optimizing Your Resume

### Adding a Job Description
To tailor your resume for a specific job description, run:

```bash
resumecraftr add-job-description "Principal Engineer XYZ" --content "About the job... (job description text here)"
```

### Optimizing the Resume
After adding the job description, optimize the resume with:

```bash
resumecraftr optimize
```

This step ensures that your resume highlights relevant skills and experience based on the job description. ResumeCraftr uses OpenAI to rewrite and structure the content to be ATS-friendly.

---

## Generating a PDF Resume

Once your resume is optimized, generate a PDF using:

```bash
resumecraftr toPdf
```

ResumeCraftr uses OpenAI to:
1. Generate the LaTeX file based on the provided template and structured sections.
2. Automatically correct any LaTeX errors to ensure a seamless PDF generation.

The resulting PDF will be saved in `cv-workspace/`.

---

## Changing Models or Recreating Agents

To change the GPT model:

1. Change de model on ```resumecraftr.json```
2. Delete the existing agents using the following command:

```bash
resumecraftr delete-agents
```

This ensures that any new model preferences are applied to subsequent optimizations.

---

With these steps, you can extract, optimize, and generate a professionally formatted ATS-friendly resume with ResumeCraftr. 🚀
