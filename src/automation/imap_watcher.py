"""
IMAP Email Watcher
Watches IMAP mailbox for new emails and processes them
"""

import imaplib
import email
from email.header import decode_header
import os
import tempfile
from typing import List, Dict, Optional
import logging
from datetime import datetime

from .watcher import EmailWatcher

logger = logging.getLogger(__name__)


class IMAPWatcher(EmailWatcher):
    """IMAP-based email watcher"""
    
    def __init__(self, config: Dict):
        """
        Initialize IMAP watcher
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.imap_config = self.email_config.get('imap', {})
        self.server = self.imap_config.get('server')
        self.port = self.imap_config.get('port', 993)
        self.username = self.imap_config.get('username')
        self.password = os.getenv('EMAIL_PASSWORD') or self.imap_config.get('password')
        self.folder = self.imap_config.get('folder', 'INBOX')
        self.processed_folder = self.imap_config.get('processed_folder', 'Processed')
        self.check_interval = self.imap_config.get('check_interval_seconds', 30)
        
        self.imap: Optional[imaplib.IMAP4_SSL] = None
        self.last_check_id = None  # Track last processed email ID
    
    def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            logger.info(f"Connecting to IMAP server {self.server}:{self.port}")
            self.imap = imaplib.IMAP4_SSL(self.server, self.port)
            self.imap.login(self.username, self.password)
            logger.info("Successfully connected to IMAP server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
                logger.info("Disconnected from IMAP server")
            except Exception as e:
                logger.warning(f"Error disconnecting from IMAP: {e}")
            finally:
                self.imap = None
    
    def _decode_mime_words(self, s: str) -> str:
        """Decode MIME encoded words in header"""
        decoded_words = decode_header(s)
        decoded_str = ""
        for word, encoding in decoded_words:
            if isinstance(word, bytes):
                decoded_str += word.decode(encoding if encoding else 'utf-8', errors='ignore')
            else:
                decoded_str += word
        return decoded_str
    
    def _fetch_email_message(self, email_id: str) -> Optional[Dict]:
        """
        Fetch email message data
        
        Args:
            email_id: Email UID
            
        Returns:
            Email metadata dictionary or None
        """
        try:
            # Fetch email by UID
            status, data = self.imap.uid('fetch', email_id, '(RFC822)')
            if status != 'OK' or not data[0]:
                return None
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract headers
            subject = self._decode_mime_words(msg['Subject'] or '')
            from_addr = self._decode_mime_words(msg['From'] or '')
            date_str = msg['Date'] or ''
            
            # Check for attachments
            has_attachments = False
            attachment_count = 0
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    has_attachments = True
                    attachment_count += 1
            
            # Save email to temporary file
            # Check if we need .msg or .eml format
            # For Outlook .msg files, we might need conversion
            # For now, save as .eml and let the processor handle it
            temp_dir = os.path.join(tempfile.gettempdir(), 'dt-agent-emails')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_file_path = os.path.join(temp_dir, f'email_{email_id}.eml')
            with open(temp_file_path, 'wb') as f:
                f.write(raw_email)
            
            email_data = {
                'id': email_id,
                'from': from_addr,
                'subject': subject,
                'date': date_str,
                'has_attachments': has_attachments,
                'attachment_count': attachment_count,
                'raw_data': temp_file_path,  # Path to saved email file
                'message_id': msg.get('Message-ID', ''),
            }
            
            logger.debug(f"Fetched email: {subject} from {from_addr}")
            return email_data
            
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {e}")
            return None
    
    def fetch_new_emails(self) -> List[Dict]:
        """
        Fetch new emails from IMAP mailbox
        
        Returns:
            List of email metadata dictionaries
        """
        if not self.imap:
            logger.error("Not connected to IMAP server")
            return []
        
        try:
            # Select mailbox folder
            status, _ = self.imap.select(self.folder)
            if status != 'OK':
                logger.error(f"Failed to select folder {self.folder}")
                return []
            
            # Search for unseen emails
            status, message_ids = self.imap.uid('search', None, 'UNSEEN')
            if status != 'OK':
                logger.warning("Failed to search for emails")
                return []
            
            if not message_ids[0]:
                logger.debug("No new emails found")
                return []
            
            email_ids = message_ids[0].split()
            logger.info(f"Found {len(email_ids)} new email(s)")
            
            emails = []
            for email_id in email_ids:
                email_id_str = email_id.decode('utf-8')
                email_data = self._fetch_email_message(email_id_str)
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def mark_as_processed(self, email_id: str, move_to_folder: Optional[str] = None):
        """
        Mark email as processed and optionally move to processed folder
        
        Args:
            email_id: Email UID
            move_to_folder: Folder to move to (defaults to processed_folder)
        """
        if not self.imap:
            return
        
        try:
            target_folder = move_to_folder or self.processed_folder
            
            # Try to create processed folder if it doesn't exist
            try:
                self.imap.create(target_folder)
            except:
                pass  # Folder might already exist
            
            # Copy email to processed folder
            status, _ = self.imap.uid('copy', email_id, target_folder)
            if status == 'OK':
                # Mark as deleted in original folder
                self.imap.uid('store', email_id, '+FLAGS', '\\Deleted')
                self.imap.expunge()
                logger.info(f"Moved email {email_id} to {target_folder}")
            else:
                logger.warning(f"Failed to move email {email_id} to {target_folder}")
            
            # Add to processed set
            self.add_to_processed(email_id)
            
        except Exception as e:
            logger.error(f"Error marking email {email_id} as processed: {e}")

