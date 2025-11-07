#!/bin/bash
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
    rm -f "cv-workspace/dummy_Software Engineer Resume.extracted_sections.json"
    rm -f "cv-workspace/dummy_Software Engineer Resume.txt"
    rm -f "cv-workspace/dummy_Software Engineer Resume.optimized_sections.json"
    rm -f "cv-workspace/dummy_Software Engineer Resume.tailored_sections.json"
}

populate_cv_sections() {
    local marker="populate_cv_sections"
    if check_command "$marker"; then
        echo -e "${YELLOW}Skipping CV population, already done.${NC}"
        return 0
    fi

    python - <<'PY'
import json
from pathlib import Path

cv_path = Path("cv-workspace") / "dummy_Software Engineer Resume.extracted_sections.json"
data = {
    "Contact Information": {
        "Full Name": "Ariana Delgado",
        "Email": "ariana.delgado@example.com",
        "Phone Number": "+1-415-555-2109",
        "LinkedIn": "linkedin.com/in/arianadelgado",
        "GitHub": "github.com/adelgado",
        "Portfolio": "arianadelgado.dev"
    },
    "Summary": {
        "Summary": "Principal engineer with 12+ years building AI productivity platforms, large-scale data fabrics, and developer tooling that ship tangible revenue results."
    },
    "Technical Skills": {
        "Programming Languages": ["Python", "TypeScript", "Go", "Rust"],
        "Tools and Technologies": ["LangChain", "LangGraph", "FastAPI", "Kafka", "Airflow", "Snowflake", "Kubernetes", "Terraform"]
    },
    "Work Experience": [
        {
            "Job Title": "Principal Software Engineer",
            "Company": "AtlasPay",
            "Dates of Employment": "2021-Present",
            "Responsibilities": [
                "Migrated payment core to event-driven architecture processing 80M tx/month with <200ms latency",
                "Launched ML anomaly detection reducing chargeback losses by 34%",
                "Mentored 9 engineers and formalized technical ladder + reliability guild"
            ]
        },
        {
            "Job Title": "Senior Staff Engineer",
            "Company": "Lumina Analytics",
            "Dates of Employment": "2017-2021",
            "Responsibilities": [
                "Designed multi-cloud data lake (>5PB) and governance program",
                "Led rollout of LangChain copilots cutting research cycles 45%",
                "Drove incident command practice sustaining 99.97% SLO"
            ]
        },
        {
            "Job Title": "Lead Full-Stack Engineer",
            "Company": "Northwind Labs",
            "Dates of Employment": "2014-2017",
            "Responsibilities": [
                "Delivered React/GraphQL workflow suite adopted by 300 enterprise customers",
                "Implemented GitOps + contract testing reducing regressions 60%"
            ]
        }
    ],
    "Education": [
        {
            "Institution": "Georgia Institute of Technology",
            "Degree": "M.S. Computer Science",
            "Year": "2013"
        },
        {
            "Institution": "Universidad de Los Andes",
            "Degree": "B.Eng. Computer Engineering",
            "Year": "2011"
        }
    ],
    "Projects": [
        {
            "Project Name": "Autonomous Candidate Screener",
            "Description": "LangGraph + Chroma hiring copilot with DeepSeek + policy guardrails",
            "Technologies Used": ["LangChain", "ChromaDB", "FastAPI", "DeepSeek"]
        },
        {
            "Project Name": "Observability Mesh",
            "Description": "OpenTelemetry enrichment service powering 10B spans/day",
            "Technologies Used": ["OpenTelemetry", "ClickHouse", "Rust", "Kubernetes"]
        }
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
run_command 'new-cv "Software Engineer Resume"' || exit 1
populate_cv_sections

# 2. CV seed data already populated via JSON helper

# 5. Añadir descripción de trabajo
run_command 'add-job "Director of AI Platforms at Strataverse" --content "Strataverse is seeking a Director-level engineer to lead our AI Productivity Platform. You will guide a team of 12 building LangChain/LangGraph powered RAG services, integrate DeepSeek + OpenRouter providers, and evolve our multi-region Kubernetes footprint. Required: 10+ years in backend/ML systems, proven leadership of staff-level engineers, fluency with Python, Go, and modern data tooling, hands-on experience productionizing LLM workflows, and obsession with measurable business impact."' || exit 1

# 6. Adaptar CV a la descripción del trabajo
run_command 'tailor-cv' || exit 1

# 7. Exportar CV a PDF
run_command 'export-pdf' || exit 1

echo -e "${GREEN}Example usage for ResumeCraftr completed successfully${NC}" 
