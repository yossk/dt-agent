# Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation (5 minutes)

### Step 1: Install Python Dependencies

```bash
cd /home/dayosupp/dt-agent
pip install -r requirements.txt
```

**Note**: If you want OCR support for scanned PDFs, also install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-heb poppler-utils libpoppler-cpp-dev
```

### Step 2: Configure the System

```bash
cp config/config.yaml.example config/config.yaml
```

Edit `config/config.yaml` and set:
- **paths.base**: Where to store processed quotes (e.g., `/home/dayosupp/quotes`)
- **pricing.margin_rules**: Adjust margins for your product categories

### Step 3: Test with Example Data

```bash
python src/main.py example-data/"RE_ quote for server.msg" --config config/config.yaml
```

Or process any of the example files:
```bash
# Test with Excel attachment
python src/main.py example-data/"DDN for Dayotech - Prices.msg"

# Test with another email
python src/main.py example-data/"RE_ R350.msg"
```

## What Happens?

1. **Email Parsing**: Extracts email content and attachments
2. **Document Processing**: Parses Excel/PDF files for product data
3. **Data Extraction**: Identifies SKUs, descriptions, quantities, prices
4. **Pricing Calculation**: Applies margin rules and calculates selling prices
5. **Quote Generation**: Creates formatted Excel quote
6. **File Organization**: Saves everything to organized folder structure

## Output Structure

After processing, you'll find files organized like this:

```
/data/quotes/  (or your configured base path)
  Customer_Name/
    quotes/
      2024/
        Project_Name/
          costs/
            original_email_20241215_143022.msg
            vendor_quote_20241215_143022.xlsx
            extracted_data_20241215_143022.json
            final_quote_Customer_Name_Project_Name_20241215.xlsx
            metadata_20241215_143022.json
```

## Understanding the Output

### `final_quote_*.xlsx`
The main output - a formatted Excel quote with:
- Product SKUs and descriptions
- Vendor prices
- Calculated margins
- Final selling prices
- Summary totals

### `extracted_data_*.json`
Raw extracted product data for debugging/verification

### `metadata_*.json`
Processing metadata including:
- Quote ID
- Customer/Product names
- Product counts
- Total pricing information

## Customization

### Adjusting Margins

Edit `config/config.yaml`:
```yaml
pricing:
  margin_rules:
    - category: "servers"
      margin: 12.0  # Change this value
```

### Changing File Structure

Edit the path template:
```yaml
paths:
  structure: "{customer}/{quotes}/{year}/{product}/{costs}"
```

## Troubleshooting

### Import Errors
If you get import errors:
```bash
pip install --upgrade -r requirements.txt
```

### OCR Not Working
Make sure Tesseract is installed:
```bash
tesseract --version
```

### Permission Errors
Ensure write permissions on the quotes base directory:
```bash
chmod -R 755 /data/quotes  # or your configured path
```

### Empty Results
- Check that attachments are valid Excel/PDF files
- Verify email file is not corrupted
- Check logs for parsing errors

## Next Steps

1. **Process Real Emails**: Point the system to your actual vendor emails
2. **Configure Pricing**: Adjust margins in config.yaml
3. **Set Up Automation**: Configure email watching (coming soon)
4. **Enable LLM**: Set up MCP server for intelligent product recognition (coming soon)

## Getting Help

- Check `IMPLEMENTATION_STATUS.md` for feature completion status
- Review `ARCHITECTURE.md` for system design
- See `FLOW_DIAGRAM.md` for process flow details

