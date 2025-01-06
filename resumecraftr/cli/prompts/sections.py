RAW_PROMPTS = {
    "Contact Information": r"""
    Extract the contact information from the provided text in {language}. The output must be a valid JSON object with the following fields:
    {{
        "Full Name": "string or null",
        "Email": "string or null",
        "Phone Number": "string or null",
        "LinkedIn": "string or null",
        "GitHub": "string or null",
        "Portfolio": "string or null"
    }}
    If any field is missing in the input, set its value to null. Do NOT include any extra text, explanations, or markdown formatting. Return ONLY the JSON object.
    """,
    "Summary": r"""
    Extract the professional summary from the text in {language}. The output must be a valid JSON object:
    {{
        "Summary": "string or null"
    }}
    If no summary is found, set "Summary" to null. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON object.
    """,
    "Technical Skills": r"""
    Extract a structured list of programming languages, tools, and technologies in {language}. The output must be in the following JSON format:
    {{
        "Programming Languages": ["string", ...] or [],
        "Tools and Technologies": ["string", ...] or []
    }}
    If no skills are found, return empty lists. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON object.
    """,
    "Work Experience": r"""
    Extract the work experience section as a structured JSON array in {language}. Each entry must have:
    {{
        "Job Title": "string",
        "Company": "string",
        "Dates of Employment": "string",
        "Responsibilities": ["string", ...] or []
    }}
    Ensure all details, including company name, employment dates, and full responsibilities, are captured without summarization. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Projects": r"""
    Extract all projects mentioned in the text in {language}. Each project must be structured as:
    {{
        "Project Name": "string",
        "Description": "string",
        "Technologies Used": ["string", ...] or []
    }}
    Ensure the project descriptions retain all details without summarization. If no projects are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Education": r"""
    Extract all education details in {language}. Each entry must be structured as:
    {{
        "Degree": "string",
        "Institution": "string",
        "Graduation Years": "string"
    }}
    Ensure no information is lost, and all details are retained. If no education details are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Certifications": r"""
    Extract certifications, courses, or professional training in {language}. Each entry must be structured as:
    {{
        "Certification Name": "string",
        "Issuing Organization": "string",
        "Date": "string"
    }}
    Ensure all details, including issuing organizations and dates, are retained without summarization. If no certifications are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Publications & Open Source Contributions": r"""
    Extract details about publications, articles, and open-source contributions in {language}. Each entry must be structured as:
    {{
        "Title": "string",
        "Details": "string"
    }}
    Ensure all details are preserved. If no publications or contributions are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Awards & Recognitions": r"""
    Extract any awards or recognitions mentioned in the text in {language}. Each entry must be structured as:
    {{
        "Award Name": "string",
        "Description": "string",
        "Date": "string"
    }}
    Ensure all award details, including names, descriptions, and dates, are captured fully. If no awards are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
    "Languages": r"""
    Extract spoken and written languages with proficiency levels in {language}. Each entry must be structured as:
    {{
        "Language": "string",
        "Proficiency": "string"
    }}
    Ensure all languages and proficiency levels are retained. If no languages are found, return an empty list []. Do NOT include any additional text, explanations, or markdown formatting. Return ONLY the JSON array.
    """,
}
