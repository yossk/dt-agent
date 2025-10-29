# Quote Processing Flow Diagram

## Detailed Process Flow

### Step 1: Email Reception & Parsing
```
Email Arrives (Outlook .msg)
    ↓
Extract Metadata:
    - From/To/Date
    - Subject
    - Body (HTML/Text)
    - Attachments (list)
    ↓
Identify Content Type:
    - Inline table in body?
    - Excel attachment?
    - PDF attachment?
    - Plain text with prices?
```

### Step 2: Document Extraction
```
FOR EACH Document (Attachment/Inline):
    ↓
IF Excel:
    └─→ Parse with openpyxl
        └─→ Extract: SKU, Description, Qty, Price
    ↓
IF PDF:
    └─→ Extract text + tables
        └─→ OCR if needed (scanned PDF)
        └─→ Extract: SKU, Description, Qty, Price
    ↓
IF Inline Table (Email Body):
    └─→ Parse HTML/text table
        └─→ Extract: SKU, Description, Qty, Price
    ↓
Normalize Data Format:
    {
        "sku": str,
        "description": str,
        "quantity": int,
        "unit_price": float,
        "source": str,  # "excel", "pdf", "inline"
        "raw_text": str  # Hebrew/English
    }
```

### Step 3: Product Intelligence (LLM/MCP)
```
Extracted Product Data
    ↓
FOR EACH Product:
    ↓
LLM Analysis (via MCP):
    - Recognize product category
    - Extract standardized features
    - Match to product catalog (Elasticsearch)
    - Validate SKU format
    ↓
Enrichment:
    - Add missing fields
    - Standardize description (Hebrew→English if needed)
    - Map vendor SKU → Internal SKU
    ↓
Validation:
    - Required fields present?
    - Price format valid?
    - Quantity > 0?
```

### Step 4: Business Logic Processing
```
Validated Product Data
    ↓
Apply Pricing Rules:
    - Lookup category margin %
    - Apply tier pricing if applicable
    - Calculate unit cost from vendor price
    ↓
Calculate Selling Prices:
    unit_price = vendor_price
    margin_amount = unit_price * (margin_percent / 100)
    selling_price = unit_price + margin_amount
    total_line = selling_price * quantity
    ↓
Aggregate Totals:
    - Subtotal
    - Tax (if applicable)
    - Grand Total
```

### Step 5: Quote Generation
```
Processed Product Data + Prices
    ↓
Generate Excel Quote:
    - Format header (customer, date, quote #)
    - Product table with columns:
        * SKU
        * Description (Hebrew + English)
        * Quantity
        * Unit Price (Vendor)
        * Margin %
        * Unit Price (Selling)
        * Total Line
    - Summary section (totals)
    - Footer (terms, contact)
    ↓
Apply Formatting:
    - Bold headers
    - Number formatting
    - Currency symbols
    - Conditional formatting
```

### Step 6: File Organization & Storage
```
Generated Quote + Original Email
    ↓
Extract Context:
    - Customer name (from email or config)
    - Project/product name (from subject/body)
    - Year (current year)
    ↓
Build Path:
    base_path = config.paths.base
    structure = config.paths.structure
    path = f"{base_path}/{customer}/{quotes}/{year}/{product}/{costs}/"
    ↓
Save Files:
    - Original email (.msg) → {path}/original_email.msg
    - Vendor quote (Excel/PDF) → {path}/vendor_quote.{ext}
    - Extracted data (JSON) → {path}/extracted_data.json
    - Final quote (Excel) → {path}/final_quote_{timestamp}.xlsx
    ↓
Create Index:
    - Update metadata database
    - Link to customer/project
```

### Step 7: Response & Notification
```
Storage Complete
    ↓
Generate Response Email:
    - Template: templates/email_response.html
    - Include: Status, Quote link, Summary
    - Language: Match original email (Hebrew/English)
    ↓
Send Email:
    - To: Original sender or configured recipient
    - Subject: "Quote Processed: {quote_id}"
    - Attach: Final quote (optional)
    ↓
Log Activity:
    - Success/failure
    - Processing time
    - Product count
    - Errors/warnings
```

## Error Handling Flow

```
Error Detected
    ↓
Categorize:
    - Parsing Error (document)
    - Validation Error (data)
    - LLM Error (intelligence)
    - Storage Error (file system)
    ↓
Handle Based on Category:
    - Retry (for transient errors)
    - Flag for manual review
    - Partial processing (what succeeded)
    - Alert notification
    ↓
Log & Continue:
    - Record error details
    - Continue with next item
    - Generate error report
```

## Integration Points

1. **Email System**: IMAP/POP3 or file watch folder
2. **MCP Server**: LLM services, tool calling
3. **Elasticsearch**: Product catalog, search
4. **File System**: Organized storage structure
5. **Email Sender**: SMTP for responses
6. **Monitoring**: Logging, metrics, alerts

