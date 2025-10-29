"""
Email Processor
Wrapper around main workflow for automated email processing
"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path

# Import main processor
import sys
from pathlib import Path as PathLib
project_root = PathLib(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import QuoteProcessor

logger = logging.getLogger(__name__)


class EmailProcessor:
    """
    Process emails automatically using the main quote processing workflow
    """
    
    def __init__(self, config: Dict):
        """
        Initialize email processor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.processor = QuoteProcessor(config)
    
    def process_email(self, email_data: Dict) -> Dict:
        """
        Process an email through the quote workflow
        
        Args:
            email_data: Dictionary with email metadata:
                - raw_data: Path to email file (.msg, .eml)
                - from: Sender address
                - subject: Email subject
                - date: Email date
                
        Returns:
            Dictionary with processing results:
                - success: bool
                - quote_path: str (if successful)
                - error: str (if failed)
                - products_count: int
        """
        email_file = email_data.get('raw_data')
        if not email_file or not os.path.exists(email_file):
            return {
                'success': False,
                'error': f'Email file not found: {email_file}'
            }
        
        # Check if file is .msg or .eml
        file_ext = Path(email_file).suffix.lower()
        
        # The email parser can handle both .msg and .eml files
        # For .eml files, we might need to convert to .msg if extract-msg doesn't support it
        # For now, pass it through and let the parser handle it
        if file_ext not in ['.msg', '.eml']:
            return {
                'success': False,
                'error': f'Unsupported email format: {file_ext}. Expected .msg or .eml'
            }
        
        try:
            logger.info(f"Processing email: {email_data.get('subject')} from {email_data.get('from')}")
            
            # Process using main workflow
            result = self.processor.process_email(email_file)
            
            # Clean up temporary file if it was created
            if file_ext == '.eml' and os.path.exists(email_file):
                try:
                    os.unlink(email_file)
                except:
                    pass
            
            return {
                'success': True,
                'quote_path': result.get('quote_path'),
                'products_count': result.get('product_count', 0),
                'customer_name': result.get('customer_name'),
                'product_name': result.get('product_name'),
                'total_price': result.get('total_price', 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing email: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

