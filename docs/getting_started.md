# Getting Started with ResumeCraftr

ResumeCraftr is an ATS-focused minimalist CV generator that leverages OpenAI and LaTeX to parse, optimize, and format resumes. This guide will walk you through the setup and usage of ResumeCraftr.

## Installation

Ensure you have `pipx` installed, then install ResumeCraftr with:

```sh
pipx install git+https://github.com/raestrada/ResumeCraftr.git@v0.1.0
```

Additionally, make sure you have a LaTeX distribution installed, specifically one that includes `xelatex`.

## Initializing Your Workspace

ResumeCraftr operates within a dedicated workspace directory called `cv-workspace`. To set up this workspace, run:

```sh
poetry run resumecraftr init --language EN
```

This will create the `cv-workspace` directory with the necessary configuration files, including:

- `cv-workspace/resume_template.tex`: The LaTeX template used for PDF generation. You can modify this template to customize the CV layout and style.
- `cv-workspace/resumecraftr.json`: Configuration file storing extracted files and job descriptions.

## Extracting Resume Text

ResumeCraftr can extract text from supported document formats (`.pdf`, `.docx`, `.txt`, `.md`). To extract text from your CV, place the file inside `cv-workspace` and run:

```sh
poetry run resumecraftr extract /Users/username/Documents/Personal/Resume.pdf
```

This will generate a `.txt` file containing the extracted raw text.

## Extracting Structured Sections

To classify the extracted resume text into structured sections such as contact details, experience, skills, and education, use:

```sh
poetry run resumecraftr extract-sections
```

This command will create an `.optimized_sections.json` file, which contains a structured version of your CV.

## Adding a Job Description and Optimizing Your Resume

To optimize your resume for a specific job description, run:

```sh
poetry run resumecraftr add-job-description "Principal Engineer XYZ" --content "About the job... (job description text here)"
```

Once the job description is added, optimize the resume with:

```sh
poetry run resumecraftr optimize
```

This step refines your resume to highlight relevant experience and skills based on the job description.

## Generating a PDF Resume

Once your resume is optimized, generate a PDF using:

```sh
poetry run resumecraftr toPdf
```

This will use LaTeX to format the resume and output a PDF in `cv-workspace/`.

---

With these steps, you can extract, optimize, and generate a professionally formatted ATS-friendly resume with ResumeCraftr. 🚀
