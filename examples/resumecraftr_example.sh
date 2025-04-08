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

# Inicializar el proyecto
run_command 'setup --language "EN" --gpt-model "gpt-4o"' || exit 1

# 1. Crear un nuevo CV
run_command 'new-cv "Software Engineer Resume"' || exit 1

# 2. Añadir secciones al CV
run_command 'add-section "Professional Summary" "Experienced software engineer with expertise in full-stack development, cloud architecture, and agile methodologies. Proven track record of delivering scalable solutions and leading development teams."' || exit 1
run_command 'add-section "Experience" "Senior Software Engineer at TechCorp (2020-Present)\n- Led development of microservices architecture reducing system latency by 40%\n- Managed a team of 5 developers implementing CI/CD pipeline\n- Implemented automated testing increasing code coverage to 95%"' || exit 1
run_command 'add-section "Education" "Master of Science in Computer Science, Stanford University (2018)\nBachelor of Science in Software Engineering, MIT (2016)"' || exit 1
run_command 'add-section "Skills" "Programming: Python, JavaScript, Java, C#\nFrameworks: React, Node.js, Django, Spring Boot\nCloud: AWS, Azure, GCP\nDevOps: Docker, Kubernetes, Jenkins\nDatabases: PostgreSQL, MongoDB, Redis"' || exit 1
run_command 'add-section "Projects" "E-commerce Platform (2021)\n- Developed full-stack application using React and Node.js\n- Implemented payment processing with Stripe API\n- Deployed on AWS with auto-scaling configuration\n\nMobile App (2020)\n- Created cross-platform app using React Native\n- Integrated with RESTful APIs for real-time data\n- Published on both App Store and Google Play"' || exit 1

# 3. Importar CV desde archivo
run_command 'import-cv cv-workspace/software_engineer_resume.pdf' || exit 1

# 4. Parsear CV importado
run_command 'parse-cv cv-workspace/software_engineer_resume.txt' || exit 1

# 5. Añadir descripción de trabajo
run_command 'add-job "Senior Full-Stack Developer Position at TechInnovate" "We are looking for a Senior Full-Stack Developer to join our growing team. The ideal candidate will have 5+ years of experience in web development, strong knowledge of JavaScript frameworks, and experience with cloud platforms. Responsibilities include developing and maintaining web applications, collaborating with cross-functional teams, and mentoring junior developers."' || exit 1

# 6. Adaptar CV a la descripción del trabajo
run_command 'tailor-cv cv-workspace/software_engineer_resume.optimized_sections.json' || exit 1

# 7. Exportar CV a PDF
run_command 'export-pdf' || exit 1

# 8. Exportar CV a PDF en español
run_command 'export-pdf --translate ES' || exit 1

echo -e "${GREEN}Example usage for ResumeCraftr completed successfully${NC}" 
