"""
Base Email Watcher Class
Abstract base class for email watching implementations
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class EmailWatcher(ABC):
    """Abstract base class for email watchers"""
    
    def __init__(self, config: Dict):
        """
        Initialize email watcher
        
        Args:
            config: Configuration dictionary with email settings
        """
        self.config = config
        self.email_config = config.get('email_automation', {})
        self.filters = self.email_config.get('filters', {})
        self.processed_emails = set()  # Track processed email IDs
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to email server
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from email server"""
        pass
    
    @abstractmethod
    def fetch_new_emails(self) -> List[Dict]:
        """
        Fetch new emails from server
        
        Returns:
            List of email metadata dictionaries with:
            - id: Unique email identifier
            - from: Sender address
            - subject: Email subject
            - date: Email date
            - has_attachments: Whether email has attachments
            - raw_data: Email message data or file path
        """
        pass
    
    @abstractmethod
    def mark_as_processed(self, email_id: str, move_to_folder: Optional[str] = None):
        """
        Mark email as processed
        
        Args:
            email_id: Unique email identifier
            move_to_folder: Optional folder to move email to
        """
        pass
    
    def should_process_email(self, email: Dict) -> bool:
        """
        Check if email should be processed based on filters
        
        Args:
            email: Email metadata dictionary
            
        Returns:
            True if email matches filters
        """
        # Check from domain filter
        from_domains = self.filters.get('from_domains', [])
        if from_domains:
            email_from = email.get('from', '')
            if not any(domain in email_from for domain in from_domains):
                logger.debug(f"Email from {email_from} not in allowed domains")
                return False
        
        # Check subject keywords
        subject_keywords = self.filters.get('subject_keywords', [])
        if subject_keywords:
            subject = email.get('subject', '').lower()
            if not any(keyword.lower() in subject for keyword in subject_keywords):
                logger.debug(f"Email subject '{email.get('subject')}' doesn't match keywords")
                return False
        
        # Check for attachments requirement
        if self.filters.get('has_attachments', False):
            if not email.get('has_attachments', False):
                logger.debug(f"Email doesn't have attachments but filter requires them")
                return False
        
        # Check if already processed
        email_id = email.get('id')
        if email_id and email_id in self.processed_emails:
            logger.debug(f"Email {email_id} already processed")
            return False
        
        return True
    
    def add_to_processed(self, email_id: str):
        """Add email ID to processed set"""
        self.processed_emails.add(email_id)

