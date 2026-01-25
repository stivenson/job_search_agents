"""Gestor de sesión warm-up para establecer sesiones legítimas antes de scraping."""

from typing import Optional
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.http_client_strategy import HTTPClientStrategy
from config.settings import USE_SESSION_WARMUP

logger = logging.getLogger(__name__)


class SessionWarmup:
    """
    Gestiona warm-up de sesiones visitando páginas principales primero.
    
    Single Responsibility: Solo maneja warm-up de sesiones
    """
    
    # Dominios que requieren warm-up
    WARMUP_DOMAINS = {
        'indeed.com': 'https://www.indeed.com',
        'www.indeed.com': 'https://www.indeed.com',
    }
    
    def __init__(self, http_client: HTTPClientStrategy):
        """
        Inicializa SessionWarmup.
        
        Args:
            http_client: Estrategia HTTP client para hacer requests (Dependency Inversion)
        """
        self.http_client = http_client
        self.warmed_up_domains = set()  # Track de dominios ya calentados
    
    def needs_warmup(self, domain: str) -> bool:
        """
        Verifica si un dominio necesita warm-up.
        
        Args:
            domain: Dominio a verificar
        
        Returns:
            True si necesita warm-up
        """
        return domain in self.WARMUP_DOMAINS
    
    def warm_up(self, domain: str) -> bool:
        """
        Realiza warm-up visitando página principal del dominio.
        
        Args:
            domain: Dominio para warm-up
        
        Returns:
            True si warm-up exitoso, False en caso contrario
        """
        if not USE_SESSION_WARMUP:
            return True
        
        if not self.needs_warmup(domain):
            return True
        
        if domain in self.warmed_up_domains:
            logger.debug(f"Dominio {domain} ya calentado en esta sesión")
            return True
        
        warmup_url = self.WARMUP_DOMAINS.get(domain)
        if not warmup_url:
            return True
        
        try:
            logger.info(f"Realizando warm-up para {domain}...")
            response = self.http_client.get(warmup_url, timeout=30)
            
            if response.status_code == 200:
                self.warmed_up_domains.add(domain)
                logger.info(f"Warm-up exitoso para {domain}")
                return True
            else:
                logger.warning(f"Warm-up falló para {domain}: status {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Error en warm-up para {domain}: {e}")
            return False
    
    def reset(self):
        """Resetea el estado de warm-up (útil para testing)."""
        self.warmed_up_domains.clear()
