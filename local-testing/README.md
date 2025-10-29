# Local Testing Setup

This folder contains everything you need for local testing of DT-Agent.

## Quick Start

### Complete Setup (Recommended)

```bash
# From local-testing directory
./scripts/setup.sh
```

This will:
- Install uv if needed
- Create virtual environment
- Install all dependencies
- Set up configuration
- Create data directories

### Run Tests

After setup, run tests:

```bash
# Local test with uv
make test
# or
./scripts/test-local.sh

# Docker test
make test-docker
# or
./scripts/test-docker.sh
```

## Folder Structure

```
local-testing/
├── README.md              # This file
├── scripts/              # Test scripts
│   ├── setup-and-test.sh      # Complete setup + test
│   ├── setup-uv-env.sh        # Setup uv environment
│   ├── setup-docker-env.sh    # Setup Docker environment
│   ├── run-test.sh            # Run test with example data
│   ├── test-all-files.sh      # Test all example files
│   └── cleanup.sh             # Clean test data
├── config/                # Local test configurations
│   └── config.local.yaml # Local testing config
├── data/                  # Test data directory
│   ├── quotes/           # Generated quotes (auto-created)
│   ├── logs/             # Application logs (auto-created)
│   └── incoming/         # Incoming emails (auto-created)
└── logs/                 # Test run logs
```

## Test Files Available

Test files are located in `../example-data/`:
- `RE_ quote for server.msg`
- `DDN for Dayotech - Prices.msg`
- `RE_ R350.msg`
- `project example.xlsx`

## Configuration

The local test configuration (`config/config.local.yaml`) is pre-configured with:
- Local paths (`./data/quotes`)
- Development-friendly settings
- Verbose logging

## Scripts

### `setup.sh`
Complete automated setup (run this first):
- Installs uv if needed
- Sets up virtual environment
- Installs all dependencies
- Configures environment
- Creates data directories

### `setup-docker-env.sh`
Sets up Docker environment:
- Builds Docker image
- Creates data directories
- Validates setup

### `run-test.sh`
Runs test with specified file:
```bash
./scripts/run-test.sh "RE_ quote for server.msg"
```

### `test-all-files.sh`
Tests all example files sequentially:
```bash
./scripts/test-all-files.sh
```

### `cleanup.sh`
Cleans test data and temporary files:
```bash
./scripts/cleanup.sh
```

## Usage Examples

### Test Single File
```bash
cd local-testing
./scripts/run-test.sh "../example-data/RE_ quote for server.msg"
```

### Test All Example Files
```bash
cd local-testing
./scripts/test-all-files.sh
```

### Full Automated Test
```bash
cd local-testing
./scripts/setup-and-test.sh
```

### Docker Test
```bash
cd local-testing
./scripts/test-docker.sh
```

## Expected Output

After running tests, check:
- `data/quotes/` - Generated quotes organized by customer/product
- `logs/` - Application and test logs
- Console output with quote summary

## Troubleshooting

### uv not found
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
```

### Permission denied
```bash
chmod +x scripts/*.sh
```

### Docker issues
```bash
docker-compose down
docker-compose build --no-cache
```

### Missing dependencies
```bash
./scripts/setup-uv-env.sh
```

## Next Steps

After successful local testing:
1. Review generated quotes in `data/quotes/`
2. Adjust config for your needs
3. Test with your own email files
4. Integrate into CI/CD pipeline

