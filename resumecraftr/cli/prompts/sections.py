RAW_PROMPTS = {
    "Contact Information": r"""
    Extract the contact information from the provided text. The output must be a valid JSON object with the following fields:
    {
        "Full Name": "string or null",
        "Email": "string or null",
        "Phone Number": "string or null",
        "LinkedIn": "string or null",
        "GitHub": "string or null",
        "Portfolio": "string or null"
    }
    If any field is missing in the input, set its value to null. Do NOT include any extra text, explanations, or markdown formatting. Return ONLY the JSON object.
    """,
    "Summary": r"""
    Extract the professional summary from the text. The output must be a valid JSON object:
    {
        "Summary": "string or null"
    }
    If no summary is found, set "Summary" to null. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON object.
    """,
    "Technical Skills": r"""
    Extract a structured list of programming languages, tools, and technologies. The output must be in the following JSON format:
    {
        "Programming Languages": ["string", ...] or [],
        "Tools and Technologies": ["string", ...] or []
    }
    If no skills are found, return empty lists. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON object.
    """,
    "Work Experience": r"""
    Extract the work experience section as a structured JSON array. Each entry must have:
    {
        "Job Title": "string",
        "Company": "string",
        "Dates of Employment": "string",
        "Responsibilities": ["string", ...] or []
    }
    If no work experience is found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Projects": r"""
    Extract all projects mentioned in the text. Each project must be structured as:
    {
        "Project Name": "string",
        "Description": "string",
        "Technologies Used": ["string", ...] or []
    }
    If no projects are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Education": r"""
    Extract all education details. Each entry must be structured as:
    {
        "Degree": "string",
        "Institution": "string",
        "Graduation Years": "string"
    }
    If no education details are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Certifications": r"""
    Extract certifications, courses, or professional training. Each entry must be structured as:
    {
        "Certification Name": "string",
        "Issuing Organization": "string",
        "Date": "string"
    }
    If no certifications are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Publications & Open Source Contributions": r"""
    Extract details about publications, articles, and open-source contributions. Each entry must be structured as:
    {
        "Title": "string",
        "Details": "string"
    }
    If no publications or contributions are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Awards & Recognitions": r"""
    Extract any awards or recognitions mentioned in the text. Each entry must be structured as:
    {
        "Award Name": "string",
        "Description": "string",
        "Date": "string"
    }
    If no awards are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Languages": r"""
    Extract spoken and written languages with proficiency levels. Each entry must be structured as:
    {
        "Language": "string",
        "Proficiency": "string"
    }
    If no languages are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
}
