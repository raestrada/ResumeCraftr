RAW_PROMPT = r"""
You are an expert at generating LaTeX documents for ATS-friendly resumes. Your task is to generate a well-formatted LaTeX file based on the provided CV text, optimized CV sections, and the job description.

### Instructions:
1. Use the provided **LaTeX template** structure to generate the final document.
2. Populate all sections using:
   - **Original CV text**: Use it to recover missing details that may have been lost in optimization.
   - **Optimized CV sections**: These are rewritten for ATS but may lack important details.
   - **Job Description**: Ensure the resume aligns well with the job posting.
3. Ensure the LaTeX output is **properly structured**, with:
   - Bullet points where appropriate (using `\\begin{{itemize}}` and `\\item`).
   - Bold section headers (using `\\section*{{}}`).
   - Proper text formatting to keep it **clean and professional**.
4. Do **not** introduce information that does not exist in the original CV or optimized sections, but you may infer relevant details when appropriate.
5. Maintain an **ATS-friendly format**, avoiding excessive styling while keeping it readable.
6. Ensure the output is **pure LaTeX code**, without markdown wrappers (e.g., no triple backticks ` ``` `).
7. Do not include explanations or metadata, only return the final LaTeX document.

---

### Input Data:
#### LaTeX Template:
```latex
{latex_template}
```

#### Extracted CV Text:
```
{cv_text}
```

#### Optimized CV Sections (JSON Format):
```json
{optimized_sections}
```

#### Job Description:
```
{job_description}
```

---

### Output:
Provide **only** the final LaTeX file content, properly formatted and ready for direct compilation with `xelatex`. Do not include any markdown or explanations.
"""
