# Testing Guide

This guide covers testing DT-Agent both locally (with uv) and in Docker containers.

## Prerequisites

### Option 1: Local Development with uv (Recommended for Development)

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Set up environment**:
   ```bash
   make setup-dev
   # or manually:
   uv venv
   uv pip install -e ".[dev]"
   ```

### Option 2: Docker (Recommended for Testing/Production)

1. **Install Docker and Docker Compose** (if not already installed)
2. **No additional setup needed** - everything runs in containers

## Quick Test

### Local Testing (with uv)

```bash
# Using the test script
./scripts/test-local.sh

# Or using make
make test-example

# Or manually
source .venv/bin/activate
python src/main.py example-data/"RE_ quote for server.msg" --config config/config.yaml
```

### Docker Testing

```bash
# Using the test script
./scripts/test-docker.sh

# Or using make
make docker-test

# Or using docker-compose directly
docker-compose run --rm dt-agent example-data/"RE_ quote for server.msg" --config config/config.yaml
```

## Testing Different Example Files

### Test with specific example file:

```bash
# Local
./scripts/test-local.sh example-data/"DDN for Dayotech - Prices.msg"

# Docker
./scripts/test-docker.sh example-data/"RE_ R350.msg"
```

## Available Make Commands

```bash
make help              # Show all available commands
make setup-dev         # Set up development environment with uv
make install           # Install dependencies with uv
make test              # Run pytest tests
make test-example      # Test with example data files (local)
make docker-build      # Build Docker image
make docker-run        # Build and run in Docker container
make docker-test       # Test with example data in Docker
make docker-shell      # Open interactive shell in Docker container
make clean             # Clean temporary files and caches
make setup-config      # Copy example config if it doesn't exist
make init              # Initialize project (config + dev environment)
```

## Directory Structure

```
dt-agent/
├── data/              # Local data storage (created automatically)
│   ├── quotes/       # Generated quotes
│   ├── logs/         # Application logs
│   └── incoming/     # Incoming email files
├── scripts/          # Test scripts
│   ├── test-local.sh # Local testing script
│   └── test-docker.sh # Docker testing script
├── .venv/            # uv virtual environment (created by setup-dev)
└── ...
```

## Configuration

Before running tests, ensure you have a config file:

```bash
make setup-config
# or manually:
cp config/config.yaml.example config/config.yaml
```

Edit `config/config.yaml` to customize:
- Base path for quotes (default: `/data/quotes`)
- Pricing rules and margins
- Email settings

## Expected Output

After running a test, you should see:

1. **Console output**:
   ```
   ✓ Quote Processing Complete!
     Quote ID: Customer_Project_20241215
     Customer: Customer
     Products: X
     Total Price: $XXXX.XX
     Quote saved to: /path/to/final_quote.xlsx
   ```

2. **Generated files** in `data/quotes/{customer}/quotes/{year}/{product}/costs/`:
   - `original_email_*.msg`
   - `vendor_quote_*.xlsx` (if Excel attachment)
   - `extracted_data_*.json`
   - `final_quote_*.xlsx`
   - `metadata_*.json`

## Troubleshooting

### uv Installation Issues

If uv installation fails:
```bash
# Alternative installation via pip
pip install uv
```

### Docker Issues

If Docker build fails:
```bash
# Clean and rebuild
docker-compose down
docker-compose build --no-cache dt-agent
```

### Missing Dependencies

If you get import errors:
```bash
# Local
source .venv/bin/activate
uv pip install -e ".[dev]"

# Docker - rebuild image
make docker-build
```

### Permission Issues

If you get permission errors on data directories:
```bash
chmod -R 755 data/
```

### Config File Not Found

```bash
make setup-config
```

## Testing Workflow

### Development Workflow

1. **Make changes** to source code
2. **Test locally** with uv:
   ```bash
   ./scripts/test-local.sh
   ```
3. **Test in Docker** to verify container compatibility:
   ```bash
   ./scripts/test-docker.sh
   ```
4. **Commit and push** when tests pass

### CI/CD Testing

The CI/CD pipeline (`.github/workflows/ci-cd.yml`) automatically:
- Runs tests on push/PR
- Builds Docker image
- Can deploy to Kubernetes (when configured)

## Advanced Testing

### Interactive Docker Shell

```bash
make docker-shell
# or
docker-compose run --rm dt-agent /bin/bash
```

### Run Specific Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_email_parser.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test with Custom Config

```bash
python src/main.py example-data/"file.msg" --config config/custom-config.yaml
```

## Next Steps

After successful testing:
1. Review generated quotes in `data/quotes/`
2. Adjust pricing rules in `config/config.yaml`
3. Test with your own email files
4. Set up MCP server for LLM integration
5. Deploy to Kubernetes cluster

