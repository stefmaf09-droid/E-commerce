"""
Attachment Extractor - Saving and Organizing Email Attachments
Handles file extraction, sanitization, and storage organization.
"""
import os
import email
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class AttachmentExtractor:
    """Extracts and saves attachments from email messages."""
    
    def __init__(self, base_storage_path: str):
        self.base_storage_path = base_storage_path
        if not os.path.exists(base_storage_path):
            os.makedirs(base_storage_path)
            logger.info(f"Created base storage directory: {base_storage_path}")

    def extract_attachments(self, msg: email.message.Message, client_email: str) -> List[Dict]:
        """
        Extract and save attachments from an email message.
        
        Args:
            msg: The email message object.
            client_email: Email of the client to organize storage.
            
        Returns:
            List of dictionaries containing saved file metadata.
        """
        saved_files = []
        client_dir = os.path.join(self.base_storage_path, client_email)
        
        # Create month-based subfolder
        month_dir = datetime.now().strftime("%Y-%m")
        target_dir = os.path.join(client_dir, month_dir)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
                
            filename = part.get_filename()
            if filename:
                filename = self._sanitize_filename(self._decode_header(filename))
                
                # Intelligent renaming: add timestamp to avoid collisions
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_name = f"{name}_{timestamp}{ext}"
                filepath = os.path.join(target_dir, save_name)
                
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        with open(filepath, 'wb') as f:
                            f.write(payload)
                            
                        file_info = {
                            'original_filename': filename,
                            'saved_path': filepath,
                            'file_size': len(payload),
                            'mime_type': part.get_content_type(),
                            'client_email': client_email,
                            'timestamp': datetime.now().isoformat()
                        }
                        saved_files.append(file_info)
                        logger.info(f"Saved attachment: {save_name} for {client_email}")
                except Exception as e:
                    logger.error(f"Failed to save attachment {filename}: {e}")
                    
        return saved_files

    def _sanitize_filename(self, filename: str) -> str:
        """Remove dangerous characters from filename."""
        # Replace non-alphanumeric (except . - _) with _
        return re.sub(r'[^\w\.\-]', '_', filename)

    def _decode_header(self, header: str) -> str:
        """Decode filename if it's encoded in header format."""
        from email.header import decode_header
        if not header:
            return "unnamed_attachment"
            
        decoded = decode_header(header)
        decoded_str = ""
        for content, encoding in decoded:
            if isinstance(content, bytes):
                decoded_str += content.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_str += str(content)
        return decoded_str
