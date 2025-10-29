#!/bin/bash
# Complete setup script for local testing environment
# Handles uv installation, venv creation, and dependency installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_TESTING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$(cd "$LOCAL_TESTING_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DT-Agent Local Testing Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check/Install uv
echo -e "${GREEN}[1/6] Checking uv installation...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv not found. Installing uv...${NC}"
    
    # Check if cargo/bin is in PATH
    if [ ! -d "$HOME/.cargo/bin" ]; then
        echo -e "${YELLOW}Installing uv to ~/.cargo/bin...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    # Add to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Verify installation
    if command -v uv &> /dev/null; then
        echo -e "${GREEN}✓ uv installed successfully${NC}"
        uv --version
    else
        echo -e "${RED}✗ Failed to install uv. Please install manually from https://github.com/astral-sh/uv${NC}"
        echo -e "${YELLOW}Or add ~/.cargo/bin to your PATH:${NC}"
        echo -e "${YELLOW}  export PATH=\"\$HOME/.cargo/bin:\$PATH\"${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ uv already installed${NC}"
    uv --version
fi

echo ""

# Step 2: Check Python version
echo -e "${GREEN}[2/6] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${YELLOW}Warning: Python $PYTHON_VERSION detected. Recommended: Python 3.11+${NC}"
    echo -e "${YELLOW}Continuing anyway...${NC}"
else
    echo -e "${GREEN}✓ Python version OK: $(python3 --version)${NC}"
fi

echo ""

# Step 3: Create virtual environment
echo -e "${GREEN}[3/6] Setting up virtual environment...${NC}"
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    cd "$PROJECT_DIR"
    uv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

echo ""

# Step 4: Activate and install dependencies
echo -e "${GREEN}[4/6] Installing dependencies...${NC}"
cd "$PROJECT_DIR"

# Activate venv
source .venv/bin/activate

# Install project with dev dependencies
echo -e "${YELLOW}Installing project dependencies (this may take a few minutes)...${NC}"
uv pip install -e ".[dev]"

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 5: Setup configuration
echo -e "${GREEN}[5/6] Setting up configuration...${NC}"
if [ ! -f "$LOCAL_TESTING_DIR/config/config.local.yaml" ]; then
    echo -e "${RED}✗ Config file not found: $LOCAL_TESTING_DIR/config/config.local.yaml${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Configuration file found${NC}"
    
    # Create symlink to main config if needed
    if [ ! -f "$PROJECT_DIR/config/config.yaml" ]; then
        echo -e "${YELLOW}Creating symlink to local config for main config...${NC}"
        mkdir -p "$PROJECT_DIR/config"
        ln -sf "$LOCAL_TESTING_DIR/config/config.local.yaml" "$PROJECT_DIR/config/config.yaml" || \
        cp "$LOCAL_TESTING_DIR/config/config.local.yaml" "$PROJECT_DIR/config/config.yaml"
    fi
fi

echo ""

# Step 6: Create data directories
echo -e "${GREEN}[6/6] Creating data directories...${NC}"
mkdir -p "$LOCAL_TESTING_DIR/data/quotes"
mkdir -p "$LOCAL_TESTING_DIR/data/logs"
mkdir -p "$LOCAL_TESTING_DIR/data/incoming"

echo -e "${GREEN}✓ Data directories created${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo -e "   ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo "2. Run a test:"
echo -e "   ${YELLOW}cd local-testing${NC}"
echo -e "   ${YELLOW}make test${NC}"
echo ""
echo "   Or directly:"
echo -e "   ${YELLOW}./scripts/test-local.sh${NC}"
echo ""
echo "3. View results in:"
echo -e "   ${YELLOW}$LOCAL_TESTING_DIR/data/quotes/${NC}"
echo ""

