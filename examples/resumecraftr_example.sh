#!/bin/bash
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parámetros del ejemplo
RESUME_NAME="John Doe Principal Engineer Resume"
RESUME_FILE="dummy_${RESUME_NAME}"
JOB_ROLE="Principal Engineer, Applied AI Experiences"
JOB_DESCRIPTION="Northstar Studio is hiring a Principal Engineer to guide our applied AI experience teams. You will architect marketing analytics copilots, coach ten senior engineers, and own the reliability of multi-region LangChain/LangGraph services. Bring 15+ years across platform engineering, growth experimentation, and data storytelling."

# Verificar si se pasó --use-poetry como argumento
if [[ "$*" == *"--use-poetry"* ]]; then
    COMMAND="poetry run resumecraftr"
else
    COMMAND="resumecraftr"
fi

# Archivo de checkpoint
CHECKPOINT_FILE=".resumecraftr_checkpoint"

# Crear archivo de checkpoint si no existe
if [ ! -f "$CHECKPOINT_FILE" ]; then
    touch "$CHECKPOINT_FILE"
fi

# Función para verificar si un comando ya fue ejecutado
check_command() {
    grep -Fxq "$1" "$CHECKPOINT_FILE"
}

# Función para marcar un comando como ejecutado
mark_command() {
    echo "$1" >> "$CHECKPOINT_FILE"
}

# Función para ejecutar comando con checkpoint
run_command() {
    local cmd="$COMMAND $*"
    if check_command "$cmd"; then
        echo -e "${YELLOW}Skipping already executed command: $cmd${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Executing: $cmd${NC}"
    eval "$cmd"
    if [ $? -eq 0 ]; then
        mark_command "$cmd"
        echo -e "${GREEN}Command completed successfully${NC}"
        return 0
    else
        echo -e "${RED}Command failed${NC}"
        return 1
    fi
}

# Función para generar custom.md si no existe
generate_custom() {
    if [ -f "cv-workspace/custom.md" ] && check_command "generate_custom"; then
        echo -e "${YELLOW}custom.md already exists, skipping generation${NC}"
        return 0
    fi

    # Crear directorio cv-workspace si no existe
    mkdir -p cv-workspace

    cat > cv-workspace/custom.md << 'EOL'
# Custom Instructions for ResumeCraftr

## Resume Style Guidelines
- Use action verbs to begin bullet points
- Quantify achievements with specific numbers and percentages
- Keep bullet points concise (1-2 lines maximum)
- Use consistent formatting throughout
- Highlight most relevant skills for each job application

## Content Focus
- Emphasize technical skills relevant to the target position
- Include specific project outcomes and business impact
- Highlight leadership and collaboration experiences
- Demonstrate problem-solving abilities with concrete examples

## Language Preferences
- Use professional, industry-standard terminology
- Avoid jargon unless specifically relevant to the field
- Maintain a confident but not arrogant tone
- Use present tense for current roles, past tense for previous positions

## Formatting Instructions
- Use bold for section headings
- Use italics for company names and job titles
- Use bullet points for achievements and responsibilities
- Maintain consistent spacing between sections
EOL

    mark_command "generate_custom"
    echo -e "${GREEN}custom.md generated successfully${NC}"
}

# Verificar si se debe continuar desde un checkpoint
if [ -f "$CHECKPOINT_FILE" ]; then
    echo -e "${YELLOW}Resuming from checkpoint...${NC}"
else
    echo -e "${YELLOW}Starting new execution...${NC}"
fi

# Generar custom.md
generate_custom

cleanup_seed_files() {
    rm -f "cv-workspace/${RESUME_FILE}.extracted_sections.json"
    rm -f "cv-workspace/${RESUME_FILE}.txt"
    rm -f "cv-workspace/${RESUME_FILE}.optimized_sections.json"
    rm -f "cv-workspace/${RESUME_FILE}.tailored_sections.json"
}

populate_cv_sections() {
    local marker="populate_cv_sections"
    if check_command "$marker"; then
        echo -e "${YELLOW}Skipping CV population, already done.${NC}"
        return 0
    fi

    CV_FILE_STEM="$RESUME_FILE" python - <<'PY'
import json
from pathlib import Path
import os

label = os.environ["CV_FILE_STEM"]
cv_path = Path("cv-workspace") / f"{label}.extracted_sections.json"
data = {
    "Contact Information": {
        "Full Name": "John Doe",
        "Email": "john.doe@example.com",
        "Phone Number": "+1-415-555-8899",
        "LinkedIn": "linkedin.com/in/johndoe",
        "GitHub": "github.com/john-doe",
        "Portfolio": "johndoe.dev"
    },
    "Summary": {
        "Summary": "Principal Engineer with 15 years orchestrating marketing analytics platforms, intelligent assistants, and growth experimentation pipelines that turn customer insights into measurable revenue."
    },
    "Technical Skills": {
        "Programming Languages": ["Python", "TypeScript", "Go", "SQL", "Scala"],
        "Tools and Technologies": [
            "LangChain",
            "LangGraph",
            "ChromaDB",
            "Vertex AI",
            "OpenRouter",
            "Snowflake",
            "dbt",
            "Kafka",
            "Airflow",
            "Looker",
            "Tableau",
            "Fivetran",
            "Kubernetes",
            "Terraform",
            "Segment",
            "Amplitude"
        ]
    },
    "Work Experience": [
        {
            "Job Title": "Principal Engineer, Marketing Intelligence",
            "Company": "Northstar Studio",
            "Dates of Employment": "2022-Present",
            "Responsibilities": [
                "Architected a LangGraph-powered experimentation copilot that forecasts campaign lift within minutes, increasing incremental ARR attribution confidence by 38%.",
                "Led 10 senior engineers and analytics partners delivering a unified marketing insights backbone spanning CRM, product telemetry, and paid channels.",
                "Shifted 90% of marketing models to a feature-store driven workflow with CI guardrails, reducing failed launches by 42%."
            ]
        },
        {
            "Job Title": "Lead Growth Platform Engineer",
            "Company": "Pulse Commerce",
            "Dates of Employment": "2020-2022",
            "Responsibilities": [
                "Built a multi-touch attribution engine on Snowflake + dbt that reconciled $650M in pipeline, unlocking budget reallocation within one quarter.",
                "Integrated LangChain assistants into marketing ops tooling, cutting creative QA turnaround from 4 days to same day.",
                "Established experimentation guardrails (pre/post power calculators, anomaly alerts) adopted by 25 growth squads."
            ]
        },
        {
            "Job Title": "Senior Staff Engineer, Lifecycle Marketing",
            "Company": "Flowly",
            "Dates of Employment": "2018-2020",
            "Responsibilities": [
                "Shipped a personalization service combining behavioral embeddings and rules, increasing LTV of the top cohort by 19%.",
                "Mentored staff engineers on measurement design, incident command, and storytelling for executive reviews.",
                "Partnered with marketing leadership to define the north-star KPI stack and telemetry investments."
            ]
        },
        {
            "Job Title": "Staff Software Engineer, Revenue Platforms",
            "Company": "Brightline Media",
            "Dates of Employment": "2016-2018",
            "Responsibilities": [
                "Modernized the ad intelligence stack onto Kubernetes + Kafka, shrinking report latency from 4 hours to 8 minutes.",
                "Rolled out contract testing and probabilistic scoring models that caught 70% of tracking regressions before launch.",
                "Built a self-serve experimentation UI for marketers, later used in 700+ tests annually."
            ]
        },
        {
            "Job Title": "Senior Engineer, Martech & CRM",
            "Company": "Acorn Retail",
            "Dates of Employment": "2014-2016",
            "Responsibilities": [
                "Implemented customer identity resolution and Segment pipelines that fed email, push, and paid media channels.",
                "Launched cross-channel journey orchestration with real-time suppression rules, cutting unsubscribes by 22%.",
                "Own incident response for revenue-impacting journeys with weekly readiness drills."
            ]
        },
        {
            "Job Title": "Platform Engineer, Marketing Systems",
            "Company": "BluePeak Travel",
            "Dates of Employment": "2012-2014",
            "Responsibilities": [
                "Built offer ranking services mixing rule-based logic with ML scoring for seasonal bundles, adding $18M upsell revenue.",
                "Established data contracts across product, finance, and marketing teams aligned to GAAP revenue reporting.",
                "Introduced release train rituals and postmortem templates adopted by the marketing engineering guild."
            ]
        },
        {
            "Job Title": "Senior Software Engineer",
            "Company": "TerraAd",
            "Dates of Employment": "2011-2012",
            "Responsibilities": [
                "Developed multi-region APIs that optimized ad pacing in near real-time, increasing ROAS by 14%.",
                "Partnered with customer success to embed experimentation narratives into quarterly business reviews.",
                "Piloted on-call rotations covering 150+ campaign integrations."
            ]
        },
        {
            "Job Title": "Software Engineer",
            "Company": "Verve Analytics",
            "Dates of Employment": "2010-2011",
            "Responsibilities": [
                "Created dashboards translating complex lift models into executive-friendly storytelling.",
                "Automated ingestion of survey and panel data into a unified warehouse, reducing manual analyst work by 30%.",
                "Collaborated with marketing ops to codify data-quality SLAs."
            ]
        },
        {
            "Job Title": "Junior Engineer, Campaign Insights",
            "Company": "Harbor Labs",
            "Dates of Employment": "2009-2010",
            "Responsibilities": [
                "Built ETL jobs combining CRM and sales data for quarterly pipeline reviews.",
                "Launched first KPI catalog and glossary shared by sales, marketing, and finance.",
                "Co-created onboarding workshops demystifying experimentation basics for marketers."
            ]
        },
        {
            "Job Title": "Engineering Intern",
            "Company": "SignalPath",
            "Dates of Employment": "2008-2009",
            "Responsibilities": [
                "Prototyped anomaly detectors on campaign data sets and presented findings to leadership.",
                "Maintained content syndication pipelines powering 60+ partner sites.",
                "Documented best practices that evolved into SignalPath’s first marketing engineering wiki."
            ]
        }
    ],
    "Education": [
        {
            "Institution": "Stanford University",
            "Degree": "M.S. Management Science & Engineering",
            "Graduation Years": "2012"
        },
        {
            "Institution": "University of Washington",
            "Degree": "B.S. Computer Science",
            "Graduation Years": "2010"
        }
    ],
    "Projects": [
        {
            "Project Name": "Growth Narrative Copilot",
            "Description": "LangGraph agent that drafts board-ready narratives combining experimentation, attribution, and finance guardrails.",
            "Technologies Used": ["LangGraph", "OpenRouter", "dbt", "Looker"]
        },
        {
            "Project Name": "Audience Intelligence Fabric",
            "Description": "Unified profile store blending first-party, paid media, and product telemetry signals with privacy-safe contracts.",
            "Technologies Used": ["Kafka", "Snowflake", "Amplitude", "Kubernetes", "Privacy APIs"]
        }
    ],
    "Publications & Open Source Contributions": [
        {
            "Title": "Designing Marketing Copilots with LangChain and Guardrails",
            "Details": "2024 talk on measurable experimentation assistants at GrowthConf."
        },
        {
            "Title": "Open-sourcing the Attribution Contract Playbook",
            "Details": "Maintainer of a contract-testing toolkit for marketing event schemas."
        }
    ],
    "Languages": [
        {"Language": "English", "Proficiency": "Native"},
        {"Language": "Spanish", "Proficiency": "Professional"}
    ]
}

cv_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
PY

    if [ $? -eq 0 ]; then
        mark_command "$marker"
        echo -e "${GREEN}Seed CV data written successfully${NC}"
    else
        echo -e "${RED}Failed to populate CV data${NC}"
        exit 1
    fi
}

# Inicializar el proyecto
run_command 'setup --language "EN" --provider "openrouter" --model "deepseek/deepseek-chat"' || exit 1

# 1. Crear un nuevo CV
cleanup_seed_files
run_command "new-cv \"${RESUME_NAME}\"" || exit 1
populate_cv_sections

# 2. CV seed data already populated via JSON helper

# 5. Añadir descripción de trabajo
JOB_TEXT="Northstar Studio needs a Principal Engineer to partner with Marketing and Revenue Operations leaders. Responsibilities include scaling LangChain/LangGraph copilots for analytics storytelling, coaching senior engineers, managing experimentation reliability, and translating signal quality into executive-ready narratives. Must demonstrate 15 years driving growth platforms, cloud infrastructure mastery, and persuasive data storytelling."
run_command "add-job \"${JOB_ROLE}\" --content \"${JOB_TEXT}\"" || exit 1

# 6. Adaptar CV a la descripción del trabajo
run_command 'tailor-cv' || exit 1

# 7. Exportar CV a PDF
run_command 'export-pdf --template modern' || exit 1

echo -e "${GREEN}Example usage for ResumeCraftr completed successfully${NC}"
