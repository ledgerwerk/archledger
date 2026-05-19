#!/bin/bash

# Build script for archledger documentation

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building archledger documentation...${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists, create if not
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install requirements
echo -e "${YELLOW}Installing documentation requirements...${NC}"
python -m pip install -r "$SCRIPT_DIR/requirements.txt"

# Install the package in development mode
echo -e "${YELLOW}Installing archledger in development mode...${NC}"
python -m pip install -e "$PROJECT_ROOT"

# Clean previous build
echo -e "${YELLOW}Cleaning previous build...${NC}"
rm -rf "$SCRIPT_DIR/_build/"

# Build documentation
echo -e "${YELLOW}Building HTML documentation...${NC}"
sphinx-build -b html "$SCRIPT_DIR" "$SCRIPT_DIR/_build/html"

# Build PDF documentation (if latex is available)
if command -v pdflatex &>/dev/null; then
    echo -e "${YELLOW}Building PDF documentation...${NC}"
    sphinx-build -b latex "$SCRIPT_DIR" "$SCRIPT_DIR/_build/latex"
    cd "$SCRIPT_DIR/_build/latex"
    make
else
    echo -e "${YELLOW}pdflatex not found, skipping PDF build${NC}"
fi

echo -e "${GREEN}Documentation build complete!${NC}"
echo -e "${GREEN}HTML documentation: $SCRIPT_DIR/_build/html/index.html${NC}"
if [ -f "$SCRIPT_DIR/_build/latex/archledger.pdf" ]; then
    echo -e "${GREEN}PDF documentation: $SCRIPT_DIR/_build/latex/archledger.pdf${NC}"
fi
