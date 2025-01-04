RAW_PROMPTS = {
    "optimize_resume": r"""
    Given a set of extracted CV sections and a job description, rewrite the CV sections so that they align as closely as possible with the job description.
    
    Rules:
    1. Do not invent experience that does not exist in the original CV.
    2. Optimize for Applicant Tracking Systems (ATS) by incorporating relevant keywords from the job description where applicable.
    3. Infer reasonable skills and technologies based on existing experience but do not add anything unrealistic.
    4. Ensure the rewritten sections are professional, concise, and follow a structured format.
    5. Retain the core experiences while making the language stronger and more tailored to the job description.
    
    Input:
    - CV Sections (structured JSON format)
    - Job Description (structured text)
    
    Output:
    - Optimized CV Sections (structured JSON format, ready for ATS)
    """
}
