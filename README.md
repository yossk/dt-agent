# DT-Agent: Automated Quote Processing System

Automated quote processing system for technology resellers. Processes vendor quotes from emails, extracts product data, calculates margins, and generates final formatted quotes.

## Features

- 📧 **Email Processing**: Parse Outlook .msg files with attachment extraction
- 📊 **Multi-format Support**: Extract data from Excel, PDF, and inline email tables
- 🤖 **Intelligent Extraction**: Product recognition and SKU mapping (with LLM integration)
- 💰 **Automated Pricing**: Calculate margins and generate selling prices
- 📁 **Organized Storage**: Automatic file organization by customer/quotes/year/product
- 🌐 **Bilingual Support**: Hebrew and English language support
- 🐳 **Containerized**: Docker and Kubernetes ready
- 🔄 **CI/CD Ready**: Automated deployment pipeline

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation and [FLOW_DIAGRAM.md](FLOW_DIAGRAM.md) for process flow diagrams.

### Key Components

1. **Email Intake Module**: Parse .msg files, extract attachments
2. **Document Processor**: Excel/PDF parsing, table extraction
3. **Intelligence Module**: LLM-based product recognition (MCP integration)
4. **Business Logic**: Pricing engine, margin calculator, quote generator
5. **File Manager**: Organized storage with structured paths
6. **Communication Module**: Email responses and notifications

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Kubernetes cluster (optional, for production deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yossk/dt-agent.git
   cd dt-agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the system**:
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config/config.yaml with your settings
   ```

4. **Run a test**:
   ```bash
   python src/main.py example-data/"RE_ quote for server.msg" --config config/config.yaml
   ```

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t dt-agent:latest .
   ```

2. **Run container**:
   ```bash
   docker run -v /path/to/quotes:/data/quotes \
              -v /path/to/config:/app/config \
              dt-agent:latest \
              python src/main.py /path/to/email.msg
   ```

## Configuration

The main configuration file is `config/config.yaml`. Key settings:

### Paths
```yaml
paths:
  base: "/data/quotes"
  structure: "{customer}/{quotes}/{year}/{product}/{costs}"
```

### Pricing Rules
```yaml
pricing:
  default_margin_percent: 15.0
  margin_rules:
    - category: "servers"
      margin: 12.0
    - category: "software"
      margin: 25.0
```

### Email Settings
```yaml
email:
  imap_server: "outlook.office365.com"
  watch_folder: "/data/incoming"
```

See `config/config.yaml.example` for complete configuration options.

## Usage

### Basic Usage

Process a single email file:
```bash
python src/main.py /path/to/email.msg
```

Process with explicit customer/product names:
```bash
python src/main.py /path/to/email.msg \
    --customer "Customer Name" \
    --product "Project Name"
```

### Processing Workflow

1. **Email Arrives** → System receives .msg file
2. **Parse Email** → Extract body, attachments, metadata
3. **Process Documents** → Extract products from Excel/PDF/Inline tables
4. **Intelligence** → LLM recognizes products, maps SKUs
5. **Calculate Pricing** → Apply margin rules, calculate selling prices
6. **Generate Quote** → Create formatted Excel quote
7. **Organize Files** → Save to structured path
8. **Send Response** → Email confirmation (if configured)

### File Organization

Files are automatically organized as:
```
/data/quotes/
  {customer}/
    quotes/
      {year}/
        {product}/
          costs/
            original_email_*.msg
            vendor_quote_*.xlsx
            extracted_data_*.json
            final_quote_*.xlsx
            metadata_*.json
```

## Development

### Project Structure

```
dt-agent/
├── src/
│   ├── email_intake/      # Email parsing
│   ├── document_processor/ # Excel/PDF parsing
│   ├── intelligence/      # LLM/MCP integration (to be added)
│   ├── business_logic/   # Pricing, quote generation
│   ├── file_manager/      # File organization
│   └── communication/     # Email responses (to be added)
├── config/                # Configuration files
├── templates/             # Email templates (to be added)
├── tests/                 # Test suite (to be added)
├── kubernetes/            # K8s manifests (to be added)
└── docker/                # Docker configs
```

### Running Tests

```bash
pytest tests/
```

### Code Style

The project follows PEP 8 style guidelines.

## Kubernetes Deployment

Kubernetes manifests are located in `kubernetes/` (to be added):

- `deployment.yaml`: Main application deployment
- `service.yaml`: Service definition
- `configmap.yaml`: Configuration
- `persistentvolumeclaim.yaml`: Storage for quotes

Deploy to Kubernetes:
```bash
kubectl apply -f kubernetes/
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/`) provides:
- Automated testing
- Docker image building
- Kubernetes deployment

## Roadmap

- [x] Core email and document parsing
- [x] Pricing engine and quote generation
- [x] File organization
- [ ] LLM/MCP integration for product recognition
- [ ] Elasticsearch product catalog
- [ ] Email response automation
- [ ] Web UI dashboard
- [ ] Advanced SKU mapping
- [ ] Multi-language translation (Hebrew ↔ English)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.

## Authors

Dayo Tech Team
