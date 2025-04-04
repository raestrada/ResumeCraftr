# <img src="https://res.cloudinary.com/dyknhuvxt/image/upload/f_auto,q_auto/v1736189459/resumecraftr_eb7drc.png" alt="ResumeCraftr Logo" width="100" height="100"> ResumeCraftr - AI-powered ATS Resume Optimization 📄🤖

Welcome to [**ResumeCraftr**](https://resumecraftr.app), the open-source tool designed to optimize resumes for ATS (Applicant Tracking Systems) using AI and LaTeX formatting. ResumeCraftr extracts, restructures, and formats CVs to ensure they meet ATS requirements while maintaining readability and professionalism.

---

## 🚀 What's New?

### 🌟 Now with Windows Support! 🖥️

ResumeCraftr now fully supports Windows, making it easier for more users to optimize their resumes across different platforms.

### 🌟 New Interactive CV Creation! 📝

ResumeCraftr now allows you to create and manage CV sections interactively without needing to parse an existing CV. This makes it easier to build your resume from scratch or update specific sections.

---

## What's New? Discover AI Craftr 🌐

**[AI Craftr](https://aicraftr.app)** is now available as a powerful suite for AI-assisted writing, featuring specialized tools like **ResumeCraftr** for resume optimization and **[PaperCraftr](https://papercraftr.app)** for academic writing. Each tool simplifies different types of content creation. Explore **PaperCraftr** for structuring research papers or stay tuned as we add more tools like **LegalCraftr** for legal documents.

---

## Release Notes v0.3.0

You can find the release notes for version `v0.3.0` [here](https://github.com/raestrada/ResumeCraftr/releases/tag/v0.3.0).

## Step 1: Install ResumeCraftr

First, install **ResumeCraftr** using [pipx](https://pypa.github.io/pipx/), a tool that helps you install and run Python applications in isolated environments. It works on macOS, Linux, and Windows. Using `pipx` ensures that **ResumeCraftr** runs in its own virtual environment, keeping your system's Python installation clean.

To install **ResumeCraftr**, run:

```bash
pipx install git+https://github.com/raestrada/ResumeCraftr.git@v0.3.0
```

## Quick Examples

Here are a few ways to get started with **ResumeCraftr**:

### Initialize a workspace:

```bash
poetry run resumecraftr init --language EN
```

### Create a new CV from scratch:

```bash
poetry run resumecraftr create-cv my_cv
```

### Add or update a section in your CV:

```bash
poetry run resumecraftr add-section my_cv "Work Experience"
```

### View your CV:

```bash
poetry run resumecraftr show-cv my_cv
```

### Extract text from a resume:

```bash
poetry run resumecraftr extract /Users/username/Documents/Personal/Resume.pdf
```

### Extract structured sections:

```bash
poetry run resumecraftr extract-sections
```

### Generate a PDF directly from extracted sections:

```bash
poetry run resumecraftr extract-pdf
```

### Generate a PDF directly from a text file without using OpenAI:

```bash
poetry run resumecraftr text-to-pdf [path/to/text_file.txt]
```

### Generate a PDF directly from a LaTeX file (useful for manual corrections):

```bash
poetry run resumecraftr tex-to-pdf [path/to/file.tex]
```

### Add a job description for optimization:

```