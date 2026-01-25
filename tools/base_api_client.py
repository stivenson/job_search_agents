"""Clase base para API clients de job boards."""

import logging
import time
import requests
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """Clase base abstracta para clientes de APIs de job boards.
    
    Proporciona funcionalidad común para:
    - Inicialización de sesión HTTP
    - Configuración de User-Agent y headers
    - Manejo de delays y rate limiting
    - Manejo de errores comunes (403/429)
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Inicializa el cliente base.
        
        Args:
            base_url: URL base de la API
            api_key: API key opcional para autenticación
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.ua_rotator = None
        self.delay_manager = None
        
        # Inicializar componentes
        self._setup_session()
        self._setup_anti_bot()
    
    def _setup_session(self) -> None:
        """Configura la sesión HTTP con headers apropiados."""
        from config.settings import USE_USER_AGENT_ROTATION
        from utils.user_agent_rotator import UserAgentRotator
        from utils.http_helpers import setup_session_headers
        
        if USE_USER_AGENT_ROTATION:
            self.ua_rotator = UserAgentRotator()
        
        setup_session_headers(self.session, self.ua_rotator)
    
    def _setup_anti_bot(self) -> None:
        """Configura características anti-bot."""
        from config.settings import RANDOM_DELAY_ENABLED, MIN_DELAY, MAX_DELAY
        from utils.delay_manager import DelayManager
        
        if RANDOM_DELAY_ENABLED:
            self.delay_manager = DelayManager(MIN_DELAY, MAX_DELAY)
    
    def _apply_delay(self) -> None:
        """Aplica delay configurado después de un request."""
        from config.settings import SCRAPING_DELAY
        from utils.http_helpers import wait_with_delay
        
        wait_with_delay(self.delay_manager, SCRAPING_DELAY, use_async=False)
    
    def _handle_rate_limit_error(self, url: str) -> None:
        """Maneja errores de rate limiting (403/429).
        
        Args:
            url: URL que causó el error
        """
        from utils.http_helpers import handle_rate_limit_error
        
        handle_rate_limit_error(self.ua_rotator, self.session, url)
    
    def _make_request(self, url: str, params: Optional[Dict] = None, 
                     timeout: int = 30) -> requests.Response:
        """Hace un request HTTP con manejo de errores estándar.
        
        Args:
            url: URL del request
            params: Parámetros de query opcionales
            timeout: Timeout en segundos
        
        Returns:
            Response object
        
        Raises:
            requests.exceptions.HTTPError: Si hay un error HTTP
            requests.exceptions.Timeout: Si hay timeout
        """
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            # Aplicar delay después de request exitoso
            self._apply_delay()
            
            return response
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code in [403, 429]:
                self._handle_rate_limit_error(url)
            raise
    
    @abstractmethod
    def search_jobs(self, keywords: List[str], **kwargs) -> List[Dict]:
        """Busca trabajos usando los keywords proporcionados.
        
        Debe ser implementado por cada subclase.
        
        Args:
            keywords: Lista de keywords de búsqueda
            **kwargs: Argumentos adicionales específicos del cliente
        
        Returns:
            Lista de trabajos encontrados
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cerrar sesión."""
        self.session.close()
