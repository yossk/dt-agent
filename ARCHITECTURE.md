# DT-Agent Architecture

## Overview
Automated quote processing system for a technology reseller company. Processes vendor quotes from emails, extracts product data, calculates margins, and generates final quotes.

## System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      EMAIL INTAKE LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Email Parser │→ │ Attachment   │→ │ Content     │        │
│  │ (.msg files) │  │ Extractor    │  │ Normalizer   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DOCUMENT PROCESSING LAYER                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Excel Parser │  │ PDF Parser   │  │ Table        │        │
│  │              │  │              │  │ Extractor    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                  │                  │                │
│         └──────────────────┴──────────────────┘                │
│                            │                                    │
│                            ▼                                    │
│                   ┌──────────────┐                             │
│                   │ Data         │                             │
│                   │ Unification  │                             │
│                   └──────────────┘                             │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INTELLIGENCE LAYER (LLM/MCP)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Product      │→ │ SKU Mapping  │→ │ Data         │        │
│  │ Recognition  │  │ & Validation │  │ Enrichment   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                  │                  │                │
│         └──────────────────┴──────────────────┘                │
│                            │                                    │
│                            ▼                                    │
│                   ┌──────────────┐                             │
│                   │ Structured   │                             │
│                   │ Product Data │                             │
│                   └──────────────┘                             │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Price        │→ │ Margin       │→ │ Quote        │        │
│  │ Calculation  │  │ Calculator   │  │ Generator    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐      │
│  │ Configuration: Profit %, Margin Rules, Pricing Tiers│      │
│  └─────────────────────────────────────────────────────┘      │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   OUTPUT & STORAGE LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ File         │  │ Quote Excel  │  │ Email        │        │
│  │ Organizer    │  │ Generator    │  │ Responder    │        │
│  │              │  │              │  │              │        │
│  │ path/to/     │  │ Final Quote  │  │ Status/Send │        │
│  │ customer/    │  │ with Margins │  │              │        │
│  │ quotes/      │  │              │  │              │        │
│  │ year/        │  │              │  │              │        │
│  │ product/     │  │              │  │              │        │
│  │ costs/       │  │              │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Email Intake Module (`email_intake/`)
- **Email Parser**: Parse Outlook .msg files, extract metadata
- **Attachment Handler**: Extract and categorize attachments (Excel, PDF)
- **Content Normalizer**: Extract inline tables from email body
- **Multi-language Support**: Hebrew/English text extraction

### 2. Document Processing Module (`document_processor/`)
- **Excel Parser**: Extract tables, handle multiple sheets, format detection
- **PDF Parser**: OCR + table extraction (for scanned PDFs)
- **Table Extractor**: Extract inline tables from email body (HTML/text)
- **Data Unifier**: Normalize data from different sources into common format

### 3. Intelligence Module (`intelligence/`)
- **MCP Server Integration**: Connect to LLM tools via MCP
- **Product Recognizer**: Use LLM to identify products from descriptions
- **SKU Mapper**: Map vendor SKUs to internal SKU system
- **Data Enrichment**: Add missing product information
- **Elasticsearch Integration**: Product catalog search/indexing

### 4. Business Logic Module (`business_logic/`)
- **Pricing Engine**: Apply pricing rules, tiers
- **Margin Calculator**: Calculate profit margins based on config
- **Quote Generator**: Create final Excel quote document
- **Validation**: Ensure data quality, completeness

### 5. File Management Module (`file_manager/`)
- **Path Builder**: Construct organized file paths
- **Version Control**: Track quote versions
- **Archive Management**: Store historical quotes

### 6. Communication Module (`communication/`)
- **Email Responder**: Send status updates, confirmations
- **Notification System**: Alert on errors, completion

## Data Flow

1. **Email Arrives** → Parse .msg file
2. **Extract Content** → Body text, attachments (Excel/PDF)
3. **Process Documents** → Extract product tables, SKUs, prices
4. **LLM Processing** → Product recognition, SKU mapping, validation
5. **Business Logic** → Apply margins, calculate final prices
6. **Generate Quote** → Create formatted Excel document
7. **Organize Files** → Save to structured path
8. **Send Response** → Email confirmation/status

## Technology Stack

- **Language**: Python 3.11+
- **Email Parsing**: `extract-msg`, `mailparser`
- **Document Processing**: `openpyxl`, `pandas`, `PyPDF2`, `pdfplumber`
- **LLM Integration**: MCP Server (Model Context Protocol)
- **Search**: Elasticsearch (for product catalog)
- **Containerization**: Docker + Kubernetes
- **CI/CD**: GitHub Actions / GitLab CI
- **Configuration**: YAML-based config files
- **Multi-language**: `googletrans` or similar for Hebrew/English

## Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Email       │  │ Processing  │  │ Intelligence│   │
│  │ Intake      │  │ Workers     │  │ Service     │   │
│  │ Service     │  │ (Pods)      │  │ (LLM/MCP)   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│         │                 │                 │         │
│         └─────────────────┴─────────────────┘         │
│                      │                                │
│                      ▼                                │
│              ┌─────────────┐                         │
│              │ Shared      │                         │
│              │ Storage     │                         │
│              │ (PVC)       │                         │
│              └─────────────┘                         │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐                   │
│  │ Elasticsearch│ │ PostgreSQL  │                   │
│  │ (Product DB) │ │ (Metadata)  │                   │
│  └─────────────┘  └─────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## Configuration Structure

```yaml
# config/config.yaml
paths:
  base: "/data/quotes"
  structure: "{customer}/{quotes}/{year}/{product}/{costs}"

pricing:
  default_margin_percent: 15
  margin_rules:
    - category: "servers"
      margin: 12
    - category: "software"
      margin: 25
    - category: "networking"
      margin: 18

email:
  imap_server: "outlook.office365.com"
  watch_folder: "/data/incoming"
  response_template: "templates/email_response.html"

llm:
  mcp_server_url: "http://mcp-service:8080"
  model: "gpt-4"
  max_retries: 3

languages:
  supported: ["he", "en"]
  default: "en"
```

## Project Structure

```
dt-agent/
├── src/
│   ├── email_intake/
│   ├── document_processor/
│   ├── intelligence/
│   ├── business_logic/
│   ├── file_manager/
│   └── communication/
├── config/
├── templates/
├── tests/
├── kubernetes/
├── docker/
├── .github/workflows/
├── requirements.txt
├── Dockerfile
└── README.md
```

