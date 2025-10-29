"""
Main Orchestrator
Coordinates all modules for quote processing workflow
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Optional
import yaml
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.email_intake.parser import EmailParser
from src.email_intake.content_extractor import EmailContentExtractor, EmailContext
from src.document_processor.excel_parser import ExcelParser
from src.document_processor.pdf_parser import PDFParser
from src.document_processor.unifier import DataUnifier
from src.business_logic.pricing import PricingEngine
from src.business_logic.quote_generator import QuoteGenerator
from src.file_manager.organizer import FileOrganizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuoteProcessor:
    """Main quote processing orchestrator"""
    
    def __init__(self, config_path: str):
        """
        Initialize quote processor with configuration
        
        Args:
            config_path: Path to configuration YAML file
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize modules
        self.email_parser = EmailParser()
        self.content_extractor = EmailContentExtractor()
        self.excel_parser = ExcelParser()
        self.pdf_parser = PDFParser(use_ocr=self.config.get('processing', {}).get('ocr_enabled', True))
        self.data_unifier = DataUnifier()
        self.pricing_engine = PricingEngine(self.config)
        self.quote_generator = QuoteGenerator(self.config)
        self.file_organizer = FileOrganizer(self.config)
    
    def process_email(self, email_path: str, 
                     customer_name: Optional[str] = None,
                     product_name: Optional[str] = None) -> Dict:
        """
        Process email and generate quote
        
        Args:
            email_path: Path to .msg email file
            customer_name: Customer name (auto-extract if None)
            product_name: Product/project name (auto-extract if None)
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing email: {email_path}")
        
        try:
            # Step 1: Parse email
            metadata = self.email_parser.parse_msg_file(email_path)
            logger.info(f"Parsed email from: {metadata.from_address}")
            
            # Step 1.5: Extract structured email context for agent understanding
            email_context = self.content_extractor.extract_context(metadata)
            logger.info(f"Extracted email context: {len(email_context.product_descriptions)} product descriptions, "
                       f"{len(email_context.special_notes)} notes, {len(email_context.customer_mentions)} customer mentions")
            
            # Log structured context for debugging/agent use
            context_string = self.content_extractor.to_structured_string(email_context)
            logger.debug(f"Email context:\n{context_string}")
            
            # Extract customer/product names if not provided
            if not customer_name:
                customer_name = self._extract_customer_name(metadata, email_context)
            if not product_name:
                product_name = self._extract_product_name(metadata, email_context)
            
            # Step 2: Extract attachments
            temp_dir = os.path.join(os.path.dirname(email_path), 'temp_attachments')
            os.makedirs(temp_dir, exist_ok=True)
            
            attachments = self.email_parser.extract_attachments(metadata, temp_dir)
            logger.info(f"Extracted {len(attachments)} attachments")
            
            # Step 3: Process documents
            all_products = []
            sources = {}
            
            # Process attachments
            excel_files = [a for a in attachments if a.filename.endswith(('.xlsx', '.xls'))]
            pdf_files = [a for a in attachments if a.filename.endswith('.pdf')]
            
            # Process Excel files
            for excel_file in excel_files:
                try:
                    if not os.path.exists(excel_file.filepath):
                        logger.warning(f"Excel file not found, skipping: {excel_file.filepath}")
                        continue
                    sheets_data = self.excel_parser.parse_excel(excel_file.filepath)
                    products = self.excel_parser.merge_sheets(sheets_data)
                    if products:
                        sources['excel'] = sources.get('excel', []) + products
                        all_products.extend(products)
                        logger.info(f"Extracted {len(products)} products from {excel_file.filename}")
                    else:
                        logger.warning(f"No products extracted from {excel_file.filename} - column detection may have failed")
                except FileNotFoundError:
                    logger.warning(f"Excel file not found, skipping: {excel_file.filepath}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing Excel {excel_file.filename}: {e}")
                    logger.debug(f"Full error: {e}", exc_info=True)
            
            # Process PDF files
            for pdf_file in pdf_files:
                try:
                    if not os.path.exists(pdf_file.filepath):
                        logger.warning(f"PDF file not found, skipping: {pdf_file.filepath}")
                        continue
                    products = self.pdf_parser.parse_pdf(pdf_file.filepath)
                    if products:
                        sources['pdf'] = sources.get('pdf', []) + products
                        all_products.extend(products)
                        logger.info(f"Extracted {len(products)} products from {pdf_file.filename}")
                    else:
                        logger.warning(f"No products extracted from {pdf_file.filename}")
                except FileNotFoundError:
                    logger.warning(f"PDF file not found, skipping: {pdf_file.filepath}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_file.filename}: {e}")
                    logger.debug(f"Full error: {e}", exc_info=True)
            
            # Process inline tables from email body
            inline_tables = self.email_parser.extract_inline_tables(metadata)
            if inline_tables:
                # Convert inline tables to product format (simplified)
                inline_products = self._parse_inline_tables(inline_tables)
                if inline_products:
                    sources['inline_table'] = inline_products
                    all_products.extend(inline_products)
                    logger.info(f"Extracted {len(inline_products)} products from inline tables")
            
            # Step 4: Unify and validate data
            unified = self.data_unifier.unify_products(sources)
            unified = self.data_unifier.deduplicate_products(unified)
            valid_products, validation_errors = self.data_unifier.validate_products(unified)
            
            if validation_errors:
                logger.warning(f"Validation errors: {len(validation_errors)} products have issues")
                for error in validation_errors[:5]:  # Log first 5
                    logger.warning(f"  {error['product']}: {error['errors']}")
            
            # Save email context even if no products found (for debugging/agent use)
            if not valid_products:
                logger.warning("No valid products extracted from email, but saving email context")
                # Still save the email context for review
                dest_folder = self.file_organizer.build_path(
                    customer_name if customer_name else "Unknown", 
                    product_name if product_name else "Unknown"
                )
                self.file_organizer.save_email(email_path, dest_folder)
                extracted_data_no_products = {
                    "email_metadata": {
                        "from": metadata.from_address,
                        "subject": metadata.subject,
                        "date": metadata.date.isoformat(),
                        "language": email_context.language
                    },
                    "email_context": {
                        "customer_mentions": email_context.customer_mentions,
                        "product_descriptions": email_context.product_descriptions,
                        "special_notes": email_context.special_notes,
                        "specifications": email_context.specifications,
                        "quantities_mentioned": email_context.quantities_mentioned,
                        "structured_context": context_string
                    },
                    "products": [],
                    "validation_errors": validation_errors,
                    "error": "No valid products extracted from email or attachments"
                }
                self.file_organizer.save_extracted_data(extracted_data_no_products, dest_folder)
                raise ValueError("No valid products extracted from email")
            
            logger.info(f"Valid products: {len(valid_products)}")
            
            # Step 5: Calculate pricing
            priced_products = self.pricing_engine.calculate_prices(valid_products)
            summary = self.pricing_engine.generate_summary(priced_products)
            
            logger.info(f"Pricing calculated - Total: {summary.total_selling_price:.2f}")
            
            # Step 6: Generate quote
            quote_id = f"{customer_name}_{product_name}_{metadata.date.strftime('%Y%m%d')}"
            temp_quote_path = os.path.join(temp_dir, f"quote_{quote_id}.xlsx")
            
            self.quote_generator.generate_quote(
                priced_products=priced_products,
                summary=summary,
                output_path=temp_quote_path,
                customer_name=customer_name,
                quote_number=quote_id
            )
            
            # Step 7: Organize files
            dest_folder = self.file_organizer.build_path(customer_name, product_name)
            
            saved_email = self.file_organizer.save_email(email_path, dest_folder)
            
            # Save vendor quotes
            for excel_file in excel_files:
                self.file_organizer.save_vendor_quote(excel_file.filepath, dest_folder, "excel")
            for pdf_file in pdf_files:
                self.file_organizer.save_vendor_quote(pdf_file.filepath, dest_folder, "pdf")
            
            # Save extracted data including email context
            extracted_data = {
                "email_metadata": {
                    "from": metadata.from_address,
                    "subject": metadata.subject,
                    "date": metadata.date.isoformat(),
                    "language": email_context.language
                },
                "email_context": {
                    "customer_mentions": email_context.customer_mentions,
                    "product_descriptions": email_context.product_descriptions,
                    "special_notes": email_context.special_notes,
                    "specifications": email_context.specifications,
                    "quantities_mentioned": email_context.quantities_mentioned,
                    "structured_context": context_string
                },
                "products": [
                    {
                        "sku": p.sku,
                        "description": p.description,
                        "quantity": p.quantity,
                        "unit_price": p.unit_price,
                        "source": p.source
                    }
                    for p in valid_products
                ],
                "validation_errors": validation_errors
            }
            self.file_organizer.save_extracted_data(extracted_data, dest_folder)
            
            # Save final quote
            final_quote_path = self.file_organizer.save_final_quote(temp_quote_path, dest_folder, quote_id)
            
            # Save processing metadata
            metadata_dict = {
                "quote_id": quote_id,
                "customer": customer_name,
                "product": product_name,
                "processed_at": metadata.date.isoformat(),
                "products_count": len(valid_products),
                "total_selling_price": summary.total_selling_price,
                "total_margin": summary.total_margin,
                "margin_percent": summary.margin_percent_avg
            }
            self.file_organizer.save_metadata(metadata_dict, dest_folder)
            
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {
                "success": True,
                "quote_id": quote_id,
                "customer": customer_name,
                "product": product_name,
                "quote_path": final_quote_path,
                "products_count": len(valid_products),
                "total_price": summary.total_selling_price,
                "validation_errors": len(validation_errors)
            }
        
        except Exception as e:
            logger.error(f"Error processing email: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_customer_name(self, metadata, email_context: Optional[EmailContext] = None) -> str:
        """Extract customer name from email"""
        # First try email context customer mentions
        if email_context and email_context.customer_mentions:
            # Prefer longer, more specific mentions
            mentions = sorted(email_context.customer_mentions, key=len, reverse=True)
            for mention in mentions[:3]:
                # Filter out email addresses, keep names
                if '@' not in mention and len(mention.split()) <= 3:
                    return mention.title()
        
        # Try to extract from subject or body
        subject = metadata.subject.lower()
        
        # Common patterns: "RE: Quote for [Customer]", "DDN for [Customer]"
        if "for" in subject:
            parts = subject.split("for")
            if len(parts) > 1:
                name = parts[-1].strip().split()[0]
                return name.capitalize()
        
        # Try from sender domain
        if '@' in metadata.from_address:
            domain = metadata.from_address.split('@')[1].split('.')[0]
            return domain.capitalize()
        
        # Default
        return "Customer"
    
    def _extract_product_name(self, metadata, email_context: Optional[EmailContext] = None) -> str:
        """Extract product/project name from email"""
        # Try from email context product descriptions
        if email_context and email_context.product_descriptions:
            # Look for server/product type mentions
            for desc in email_context.product_descriptions[:3]:
                if 'server' in desc.lower():
                    # Extract server type
                    server_match = re.search(r'(\d+U?\s+server)', desc, re.IGNORECASE)
                    if server_match:
                        return server_match.group(1)
        
        subject = metadata.subject
        
        # Remove common prefixes
        for prefix in ["RE:", "Fwd:", "FW:", "RE:"]:
            if subject.lower().startswith(prefix.lower()):
                subject = subject[len(prefix):].strip()
        
        # Use subject as product name (or part of it)
        return subject[:50] or "Project"
    
    def _parse_inline_tables(self, tables) -> list:
        """Parse inline tables into product format"""
        products = []
        # This is simplified - can be enhanced
        for table in tables:
            # Skip if table has headers but no data
            if len(table.get('data', [])) < 2:
                continue
            
            # Try to extract products from table data
            # This would require more sophisticated parsing
            # For now, return empty list and rely on LLM module later
            pass
        
        return products


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='DT-Agent: Automated Quote Processing')
    parser.add_argument('email_path', help='Path to email .msg file')
    parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    parser.add_argument('--customer', help='Customer name (auto-detect if not provided)')
    parser.add_argument('--product', help='Product/project name (auto-detect if not provided)')
    
    args = parser.parse_args()
    
    # Check if config exists, create from example if not
    config_path = args.config
    if not os.path.exists(config_path):
        example_config = config_path + '.example'
        if os.path.exists(example_config):
            import shutil
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            shutil.copy(example_config, config_path)
            logger.info(f"Created config file from example: {config_path}")
        else:
            logger.error(f"Config file not found: {config_path}")
            return 1
    
    # Initialize processor
    processor = QuoteProcessor(args.config)
    
    # Process email
    result = processor.process_email(
        args.email_path,
        customer_name=args.customer,
        product_name=args.product
    )
    
    if result['success']:
        logger.info(f"Quote generated successfully: {result['quote_path']}")
        print(f"\n✓ Quote Processing Complete!")
        print(f"  Quote ID: {result['quote_id']}")
        print(f"  Customer: {result['customer']}")
        print(f"  Products: {result['products_count']}")
        print(f"  Total Price: ${result['total_price']:.2f}")
        print(f"  Quote saved to: {result['quote_path']}")
        return 0
    else:
        logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
        print(f"\n✗ Processing Failed: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

