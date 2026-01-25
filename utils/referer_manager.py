"""Gestor de referers realistas para simular navegación."""

import random
from typing import Optional
from urllib.parse import urlparse


class RefererManager:
    """Gestiona referers realistas basados en el dominio objetivo."""
    
    # Referers comunes por dominio
    COMMON_REFERERS = {
        'indeed.com': [
            'https://www.google.com/search?q=jobs',
            'https://www.google.com/search?q=indeed+jobs',
            'https://www.google.com/',
            'https://www.bing.com/search?q=indeed',
            'https://www.bing.com/search?q=jobs',
            'https://www.linkedin.com/jobs/',
            'https://www.indeed.com/',
        ],
        'linkedin.com': [
            'https://www.google.com/search?q=linkedin+jobs',
            'https://www.google.com/search?q=jobs',
            'https://www.linkedin.com/feed/',
            'https://www.linkedin.com/jobs/',
            'https://www.linkedin.com/',
            'https://www.bing.com/search?q=linkedin',
        ],
        'stackoverflow.com': [
            'https://www.google.com/search?q=stack+overflow+jobs',
            'https://www.google.com/search?q=developer+jobs',
            'https://stackoverflow.com/',
            'https://stackoverflow.com/jobs',
        ],
        'github.com': [
            'https://www.google.com/search?q=github+jobs',
            'https://www.google.com/search?q=developer+jobs',
            'https://github.com/',
            'https://github.com/jobs',
        ],
        'remoteok.com': [
            'https://www.google.com/search?q=remote+jobs',
            'https://www.google.com/search?q=remoteok',
            'https://remoteok.com/',
        ],
        'weworkremotely.com': [
            'https://www.google.com/search?q=we+work+remotely',
            'https://www.google.com/search?q=remote+jobs',
            'https://weworkremotely.com/',
        ],
    }
    
    # Referers genéricos para dominios no configurados
    DEFAULT_REFERERS = [
        'https://www.google.com/',
        'https://www.google.com/search?q=jobs',
        'https://www.bing.com/',
        'https://www.bing.com/search?q=jobs',
        'https://duckduckgo.com/',
    ]
    
    def get_referer(self, target_url: str) -> Optional[str]:
        """
        Retorna un referer realista para la URL objetivo.
        
        Args:
            target_url: URL objetivo para la cual generar referer
        
        Returns:
            URL referer o None si no se puede determinar
        """
        try:
            parsed = urlparse(target_url)
            domain = parsed.netloc.replace('www.', '').lower()
            
            # Buscar referers específicos para el dominio
            referers = self.COMMON_REFERERS.get(domain, self.DEFAULT_REFERERS)
            
            return random.choice(referers) if referers else None
        except Exception:
            return random.choice(self.DEFAULT_REFERERS)
    
    def get_referer_for_domain(self, domain: str) -> Optional[str]:
        """
        Retorna un referer para un dominio específico.
        
        Args:
            domain: Dominio (ej: 'indeed.com')
        
        Returns:
            URL referer o None
        """
        domain_clean = domain.replace('www.', '').lower()
        referers = self.COMMON_REFERERS.get(domain_clean, self.DEFAULT_REFERERS)
        return random.choice(referers) if referers else None
