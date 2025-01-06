RAW_PROMPT = r"""
You are an expert at generating LaTeX documents for ATS-friendly resumes. Your task is to generate a well-formatted LaTeX file based on the provided CV text, optimized CV sections, and the job description.

### Instructions:
1. Use the provided **LaTeX template** structure to generate the final document.
2. Populate all sections using:
   - **Original CV text**: Use it to recover missing details that may have been lost in optimization.
   - **Optimized CV sections**: These are rewritten for ATS but may lack important details.
   - **Job Description**: Ensure the resume aligns well with the job posting.
3. **Prioritize and expand on relevant experience**:
   - Highlight and **fully elaborate** on work experience that is directly related to the job description.
   - Ensure that all key achievements, technologies used, and detailed responsibilities are included.
   - Do not summarize key experiences; keep descriptions **as detailed as possible**.
   - For non-relevant jobs, provide a shorter summary but still retain key points.
4. Ensure the LaTeX output is **properly structured**, with:
   - Bullet points where appropriate (using `\begin{{itemize}}` and `\item`).
   - Bold section headers (using `\section*{{}}`).
   - Proper text formatting to keep it **clean and professional**.
5. Do **not** introduce information that does not exist in the original CV or optimized sections, but you may infer relevant details when appropriate.
6. Maintain an **ATS-friendly format**, avoiding excessive styling while keeping it readable.
7. Ensure the output is **pure LaTeX code**, without markdown wrappers (e.g., no triple backticks ` ``` `).
8. Do not include explanations or metadata, only return the final LaTeX document.

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
Provide **only** the final LaTeX file content in {language}, properly formatted and ready for direct compilation with `xelatex`. Do not include any markdown or explanations.
"""

LATEX_CORRECTION = r"""
You are an expert in LaTeX document formatting and troubleshooting. The following LaTeX document has errors that prevent it from compiling successfully.

Here is the LaTeX source code that caused the issue:
```
{latex_code}
```

Here is the error message from the LaTeX compiler:
```
{error_message}
```

Your task is to:
1. **Identify the source of the errors** based on the error message and the provided LaTeX code.
2. **Correct only the problematic parts** while preserving the document's structure and formatting.
3. Ensure all hyperlinks (`\href{}`), bold text (`\textbf{}`), lists, and special characters are properly escaped or formatted.
4. Prevent overfull boxes and missing `$` symbols by adjusting long text and equations.
5. Return only the fixed LaTeX code. Do NOT include any explanations, comments, or markdown formatting.

Ensure that the output is a valid, compilable LaTeX document.
"""
