# <img src="https://res.cloudinary.com/dyknhuvxt/image/upload/f_auto,q_auto/v1736189459/resumecraftr_eb7drc.png" alt="ResumeCraftr Logo" width="100" height="100"> ResumeCraftr - AI-powered ATS Resume Optimization 📄🤖

Welcome to [**ResumeCraftr**](https://resumecraftr.app), the open-source tool designed to optimize resumes for ATS (Applicant Tracking Systems) using AI and Markdown formatting. ResumeCraftr extracts, restructures, and formats CVs to ensure they meet ATS requirements while maintaining readability and professionalism.

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

## Release Notes v0.4.0

You can find the release notes for version `v0.4.0` [here](https://github.com/raestrada/ResumeCraftr/releases/tag/v0.4.0).

## Step 1: Install ResumeCraftr

First, install **ResumeCraftr** using [pipx](https://pypa.github.io/pipx/), a tool that helps you install and run Python applications in isolated environments. It works on macOS, Linux, and Windows. Using `pipx` ensures that **ResumeCraftr** runs in its own virtual environment, keeping your system's Python installation clean.

To install **ResumeCraftr**, run:

```bash
pipx install git+https://github.com/raestrada/ResumeCraftr.git@v0.4.0
```

## Quick Examples

Here are a few ways to get started with **ResumeCraftr**:

### Initialize a workspace:

```bash
poetry run resumecraftr setup --language EN
```

### Create a new CV from scratch:

```bash
poetry run resumecraftr new-cv my_cv
```

### Add or update a section in your CV:

```bash
poetry run resumecraftr edit-section my_cv "Work Experience"
```

### View your CV:

```bash
poetry run resumecraftr view-cv my_cv
```

### Import a CV from PDF:

```bash
poetry run resumecraftr import-cv /Users/username/Documents/Personal/Resume.pdf
```

### Parse a CV into sections:

```bash
poetry run resumecraftr parse-cv
```

### Add a job description for optimization:

```bash
poetry run resumecraftr add-job
```

### Tailor your CV to a job description:

```bash
poetry run resumecraftr tailor-cv
```

### Export your CV to PDF:

```bash
poetry run resumecraftr export-pdf
```

## Full Guide

For a complete guide, including more examples and instructions on how to fully leverage ResumeCraftr, visit our **Getting Started** page:

👉 [**Getting Started with ResumeCraftr**](https://resumecraftr.app/getting_started.html) 👈

## Why ResumeCraftr?

Applying for jobs requires a well-structured and ATS-optimized resume. **ResumeCraftr** helps you:

- **Create resumes from scratch** with interactive section management.
- **Import resume content** from various document formats.
- **Parse resumes** into structured sections.
- **Tailor resumes** to match job descriptions effectively.
- **Generate professional PDFs** with structured sections.
- **Ensure ATS compatibility** while maintaining readability.

With ResumeCraftr, your resume gets the best chance of passing ATS filters and standing out to recruiters.

## Contributing

We welcome contributions of all kinds! Whether you're a developer, resume expert, or simply interested in improving the tool, you can help. Here's how you can contribute:

1. **Fork the repository** and create your branch:

```bash
git checkout -b feature/YourFeature
```

2. **Make your changes**, ensuring all tests pass.

3. **Submit a pull request** detailing your changes.

Join us in making ResumeCraftr the best AI-powered resume tool! 🚀

## Powered by AI Craftr

**ResumeCraftr** is part of the **AI Craftr** suite, an open-source set of tools designed to assist with creative and professional writing. AI Craftr enhances the productivity of job seekers, researchers, and writers, providing advanced tools for content optimization.

![AI Craftr Logo](https://res.cloudinary.com/dyknhuvxt/image/upload/v1730059761/aicraftr_qzknf4.png)

Learn more about **AI Craftr** and discover other tools like **StoryCraftr** for novel writing at [https://aicraftr.app](https://aicraftr.app).


