import os

job_desc_file = "cv-workspace/job_descriptions/Principal Engineer Verne.txt"
job_desc_path = os.path.abspath(job_desc_file)

print(f"Checking: {job_desc_path}")
print(f"File exists? {os.path.exists(job_desc_path)}")

