# Getting Started with ResumeCraftr

ResumeCraftr is an ATS-focused minimalist CV generator that leverages OpenAI and LaTeX to parse, optimize, and format resumes. This guide will walk you through the setup and usage of ResumeCraftr, along with tips for customizing your experience.

---

## 🚀 What's New?

### 🌟 Now with Windows Support! 🖥️

ResumeCraftr now fully supports Windows, making it easier for more users to optimize their resumes across different platforms.

### 🌟 New Interactive CV Creation! 📝

ResumeCraftr now allows you to create and manage CV sections interactively without needing to parse an existing CV. This makes it easier to build your resume from scratch or update specific sections.

---

## Installation

Ensure you have `pipx` installed, then install ResumeCraftr with:

```bash
pipx install git+https://github.com/raestrada/ResumeCraftr.git@v0.3.0
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

Here's an example of a `resumecraftr.json` configuration file:

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

## Creating a CV from Scratch

ResumeCraftr now allows you to create a CV from scratch without needing to parse an existing document. This is useful for building a new resume or updating specific sections.

### Creating a New CV

To create a new CV, run:

```bash
resumecraftr create-cv my_cv
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
resumecraftr add-section my_cv "Work Experience"
```

This command will guide you through the process of adding or updating the specified section. You can add multiple entries for sections like Work Experience, Projects, Education, etc.

### Viewing Your CV

To view the contents of your CV, run:

```bash
resumecraftr show-cv my_cv
```

This command displays all sections of your CV in a structured format.

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

This command creates an `.extracted_sections.json` file, which contains a structured version of your CV, making it easier to optimize.

### Generating a PDF from Extracted Sections

If you want to generate a PDF directly from the extracted sections without going through the optimization process, use:

```bash
resumecraftr extract-pdf
```

This command will:
1. Find all `.extracted_sections.json` files in your workspace
2. Let you choose which one to use if multiple files exist
3. Generate a LaTeX file and compile it to PDF
4. Save the resulting PDF in your workspace

This is useful when you want to see how your CV looks after extraction but before optimization, or when you're satisfied with the extracted content and don't need to optimize it for a specific job.

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

### Language Optimization

One of the key benefits of the optimize command is that it rewrites all content in the language you configured during initialization. This means:

- **Grammar and Spelling**: The AI automatically corrects grammatical errors and spelling mistakes
- **Language Consistency**: Ensures all content follows the same language style and conventions
- **Professional Tone**: Adjusts the writing to maintain a professional tone appropriate for resumes
- **Cultural Adaptation**: Adapts content to match the cultural expectations of the target language

For example, if you configured ResumeCraftr with `--language ES` (Spanish), the optimize command will rewrite your resume in proper Spanish, correcting any language errors and ensuring it follows Spanish resume conventions.

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

With these steps, you can create, extract, optimize, and generate a professionally formatted ATS-friendly resume with ResumeCraftr. 🚀
