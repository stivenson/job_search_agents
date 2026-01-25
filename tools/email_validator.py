"""Validador y normalizador de emails."""

import re
from typing import List, Optional, Dict
from urllib.parse import urlparse


class EmailValidator:
    """Valida y normaliza direcciones de email."""
    
    # Patrón regex para emails
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )
    
    # Dominios comunes de no-reply que debemos ignorar
    NO_REPLY_DOMAINS = {
        'noreply', 'no-reply', 'donotreply', 'do-not-reply',
        'mailer', 'automated', 'notification'
    }
    
    def extract_emails(self, text: str) -> List[str]:
        """Extrae todos los emails de un texto."""
        emails = self.EMAIL_PATTERN.findall(text)
        return [email.lower().strip() for email in emails]
    
    def is_valid_email(self, email: str) -> bool:
        """Valida si un email es válido y no es un no-reply."""
        if not email or not self.EMAIL_PATTERN.match(email):
            return False
        
        # Extraer dominio
        domain = email.split('@')[1].lower()
        
        # Ignorar no-reply
        for no_reply in self.NO_REPLY_DOMAINS:
            if no_reply in domain:
                return False
        
        return True
    
    def normalize_email(self, email: str) -> Optional[str]:
        """Normaliza un email (lowercase, strip)."""
        if not email:
            return None
        
        email = email.lower().strip()
        
        if self.is_valid_email(email):
            return email
        
        return None
    
    def filter_valid_emails(self, emails: List[str]) -> List[str]:
        """Filtra y normaliza una lista de emails."""
        valid_emails = []
        seen = set()
        
        for email in emails:
            normalized = self.normalize_email(email)
            if normalized and normalized not in seen:
                valid_emails.append(normalized)
                seen.add(normalized)
        
        return valid_emails
    
    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """Extrae información de contacto de un texto."""
        emails = self.extract_emails(text)
        valid_emails = self.filter_valid_emails(emails)
        
        # Buscar patrones comunes de contacto
        contact_info = {
            'emails': valid_emails,
            'phone_numbers': self._extract_phones(text),
            'urls': self._extract_urls(text)
        }
        
        return contact_info
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extrae números de teléfono."""
        # Patrones comunes de teléfono
        phone_patterns = [
            r'\+?\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}',
            r'\(\d{3}\)\s?\d{3}[\s\-]?\d{4}',
            r'\d{3}[\s\-]?\d{3}[\s\-]?\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        return list(set(phones))
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extrae URLs."""
        url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )
        
        urls = url_pattern.findall(text)
        return list(set(urls))
