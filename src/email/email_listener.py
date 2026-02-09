"""
Email Listener - IMAP Connection for Email Monitoring
Fetches emails from configured IMAP server and filters by sender.
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailListener:
    """Connects to IMAP server and retrieves emails."""
    
    def __init__(self, imap_server: str, imap_port: int, username: str, password: str):
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.username = username
        self.password = password
        self.mail = None
    
    def connect(self) -> bool:
        """Establish IMAP connection."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.username, self.password)
            logger.info(f"Connected to IMAP server: {self.username}")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close IMAP connection."""
        if self.mail:
            try:
                self.mail.logout()
                logger.info("Disconnected from IMAP server")
            except:
                pass
    
    def fetch_unread_emails(self, sender_filter: Optional[str] = None) -> List[Dict]:
        """
        Fetch unread emails, optionally filtered by sender.
        
        Args:
            sender_filter: Email address to filter by (e.g., "chronopost.fr")
        
        Returns:
            List of email dictionaries with metadata
        """
        emails = []
        
        try:
            # Select mailbox
            self.mail.select("INBOX")
            
            # Build search criteria
            if sender_filter:
                search_criteria = f'(UNSEEN FROM "{sender_filter}")'
            else:
                search_criteria = 'UNSEEN'
            
            # Search for emails
            status, messages = self.mail.search(None, search_criteria)
            
            if status != "OK":
                logger.warning("No emails found")
                return emails
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    
                    if status != "OK":
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract metadata
                    email_dict = {
                        'id': email_id.decode(),
                        'subject': self._decode_header(msg.get("Subject", "")),
                        'from': self._decode_header(msg.get("From", "")),
                        'to': self._decode_header(msg.get("To", "")),
                        'date': msg.get("Date", ""),
                        'message': msg,
                        'has_attachments': self._has_attachments(msg)
                    }
                    
                    emails.append(email_dict)
                    
                except Exception as e:
                    logger.error(f"Error parsing email {email_id}: {e}")
                    continue
            
            logger.info(f"Fetched {len(emails)} unread emails")
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
        
        return emails
    
    def mark_as_read(self, email_id: str):
        """Mark email as read."""
        try:
            self.mail.store(email_id.encode(), '+FLAGS', '\\Seen')
            logger.info(f"Marked email {email_id} as read")
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
    
    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ""
        
        decoded = decode_header(header)
        decoded_str = ""
        
        for content, encoding in decoded:
            if isinstance(content, bytes):
                decoded_str += content.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_str += str(content)
        
        return decoded_str
    
    def _has_attachments(self, msg) -> bool:
        """Check if email has attachments."""
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            return True
        return False
