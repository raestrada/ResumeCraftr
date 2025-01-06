RAW_PROMPTS = {
    "optimize_resume": r"""
    You will be given a specific **CV section** in JSON format and a **Job Description**. Your task is to rewrite the content of the CV section so that it aligns with the Job Description while keeping the original JSON structure intact.

    **Rules:**
    1. **Do not modify the JSON structure.** Maintain the same keys, lists, and data formats.
    2. **Do not invent experience.** Rewrite using stronger language but do not add unrealistic or fake details.
    3. **Optimize for ATS (Applicant Tracking Systems)** by incorporating relevant **keywords** from the job description.
    4. **Enhance clarity and professionalism** while ensuring the section remains structured, concise, and impactful.
    5. **Do not include any extra text, explanations, or formatting**—return only the updated JSON.

    **Input Format:**
    ```json
    {
        "section_name": "string",
        "section_content": { ... } // The JSON object to be rewritten
    }
    ```
    
    **Job Description Format:**
    ```
    Job Title: <string>
    Job Responsibilities: <string>
    Required Skills: <string>
    Preferred Qualifications: <string>
    ```

    **Output Format (same JSON structure as input, but with rewritten content):**
    ```json
    {
        "section_name": "string",
        "section_content": { ... } // Rewritten but structurally identical JSON object
    }
    ```
    """
}
