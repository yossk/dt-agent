"""
Email Automation Module
Handles automatic email watching and processing
"""

from .email_processor import EmailProcessor
from .imap_watcher import IMAPWatcher
from .watcher import EmailWatcher

__all__ = ['EmailProcessor', 'IMAPWatcher', 'EmailWatcher']

