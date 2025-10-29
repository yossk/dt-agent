#!/bin/bash
# Test script for Docker/container testing

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

echo -e "${GREEN}DT-Agent Docker Testing${NC}"
echo "======================"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

# Setup config if needed
if [ ! -f config/config.yaml ]; then
    echo -e "${YELLOW}Creating config from example...${NC}"
    cp config/config.yaml.example config/config.yaml
fi

# Create data directories in local-testing
mkdir -p "$LOCAL_TESTING_DIR/data/quotes" "$LOCAL_TESTING_DIR/data/logs" "$LOCAL_TESTING_DIR/data/incoming"

# Build image
echo -e "${GREEN}Building Docker image...${NC}"
docker-compose build dt-agent

# Determine which example file to use
EXAMPLE_FILE="${1:-example-data/RE_ quote for server.msg}"

if [ ! -f "$EXAMPLE_FILE" ]; then
    echo -e "${RED}Error: Example file not found: $EXAMPLE_FILE${NC}"
    echo "Available example files:"
    ls -1 example-data/*.msg 2>/dev/null || echo "No .msg files found"
    exit 1
fi

echo ""
echo -e "${GREEN}Running test in Docker container...${NC}"
echo ""

# Run test in container
docker-compose run --rm dt-agent "$EXAMPLE_FILE" --config "$LOCAL_TESTING_DIR/config/config.local.yaml"

echo ""
echo -e "${GREEN}Test completed!${NC}"
echo "Check output in: $LOCAL_TESTING_DIR/data/quotes/"

