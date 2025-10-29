"""
Email Automation Service
Main service that runs continuously to watch and process emails
"""

import time
import logging
import signal
import sys
from typing import Dict, Optional
from pathlib import Path

from src.automation.watcher import EmailWatcher
from src.automation.imap_watcher import IMAPWatcher
from src.automation.email_processor import EmailProcessor

logger = logging.getLogger(__name__)


class EmailAutomationService:
    """
    Main service for automated email watching and processing
    """
    
    def __init__(self, config: Dict):
        """
        Initialize automation service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.running = False
        self.watcher: Optional[EmailWatcher] = None
        self.processor = EmailProcessor(config)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def _initialize_watcher(self) -> bool:
        """
        Initialize appropriate email watcher based on configuration
        
        Returns:
            True if watcher initialized successfully
        """
        email_config = self.config.get('email_automation', {})
        method = email_config.get('method', 'imap')
        
        if method == 'imap':
            self.watcher = IMAPWatcher(self.config)
        elif method == 'graph':
            # TODO: Implement Graph API watcher
            logger.error("Microsoft Graph API watcher not yet implemented")
            return False
        else:
            logger.error(f"Unknown email watching method: {method}")
            return False
        
        return self.watcher.connect()
    
    def _process_new_emails(self):
        """Fetch and process new emails"""
        if not self.watcher:
            return
        
        try:
            # Fetch new emails
            emails = self.watcher.fetch_new_emails()
            
            for email_data in emails:
                # Check if email should be processed
                if not self.watcher.should_process_email(email_data):
                    logger.debug(f"Skipping email: {email_data.get('subject')}")
                    continue
                
                logger.info(f"Processing email: {email_data.get('subject')}")
                
                # Process email
                result = self.processor.process_email(email_data)
                
                if result.get('success'):
                    logger.info(
                        f"Successfully processed email: {email_data.get('subject')}\n"
                        f"  Products: {result.get('products_count', 0)}\n"
                        f"  Quote: {result.get('quote_path')}"
                    )
                    
                    # Mark as processed
                    self.watcher.mark_as_processed(email_data.get('id'))
                else:
                    logger.error(
                        f"Failed to process email: {email_data.get('subject')}\n"
                        f"  Error: {result.get('error')}"
                    )
                    
                    # Optionally move failed emails to a different folder
                    # For now, we'll leave them for manual review
                    
        except Exception as e:
            logger.error(f"Error processing emails: {e}", exc_info=True)
    
    def start(self):
        """Start the email automation service"""
        email_config = self.config.get('email_automation', {})
        
        if not email_config.get('enabled', False):
            logger.warning("Email automation is disabled in configuration")
            return
        
        logger.info("Starting Email Automation Service")
        
        # Initialize watcher
        if not self._initialize_watcher():
            logger.error("Failed to initialize email watcher")
            return
        
        self.running = True
        check_interval = email_config.get('imap', {}).get('check_interval_seconds', 30)
        
        logger.info(f"Email automation service running (checking every {check_interval} seconds)")
        
        try:
            while self.running:
                self._process_new_emails()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("Service interrupted")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the email automation service"""
        logger.info("Stopping Email Automation Service")
        self.running = False
        
        if self.watcher:
            self.watcher.disconnect()
        
        logger.info("Email Automation Service stopped")

