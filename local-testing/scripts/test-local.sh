#!/bin/bash
# Test script for local development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_TESTING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$(cd "$LOCAL_TESTING_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}DT-Agent Local Testing${NC}"
echo "===================="
echo ""

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv not found.${NC}"
    echo -e "${YELLOW}Please run setup first:${NC}"
    echo -e "${YELLOW}  ./scripts/setup.sh${NC}"
    echo ""
    echo "Or install uv manually:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if config exists
if [ ! -f config/config.yaml ]; then
    echo -e "${YELLOW}Creating config from example...${NC}"
    cp config/config.yaml.example config/config.yaml
fi

# Create data directories in local-testing
mkdir -p "$LOCAL_TESTING_DIR/data/quotes" "$LOCAL_TESTING_DIR/data/logs" "$LOCAL_TESTING_DIR/data/incoming"

# Setup virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment with uv...${NC}"
    uv venv
fi

# Activate venv and install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run test
echo ""
echo -e "${GREEN}Testing with example email file...${NC}"
echo ""

# Check which example file to use
EXAMPLE_FILE="${1:-example-data/RE_ quote for server.msg}"

if [ ! -f "$EXAMPLE_FILE" ]; then
    echo -e "${RED}Error: Example file not found: $EXAMPLE_FILE${NC}"
    echo "Available example files:"
    ls -1 example-data/*.msg 2>/dev/null || echo "No .msg files found"
    exit 1
fi

python src/main.py "$EXAMPLE_FILE" --config "$LOCAL_TESTING_DIR/config/config.local.yaml"

echo ""
echo -e "${GREEN}Test completed!${NC}"
echo "Check output in: $LOCAL_TESTING_DIR/data/quotes/"

