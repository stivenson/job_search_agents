"""Interfaz y estrategias para HTTP clients (SOLID: Interface Segregation)."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import requests
import logging

logger = logging.getLogger(__name__)


class HTTPClientStrategy(ABC):
    """
    Interfaz para estrategias de HTTP client (Dependency Inversion).
    
    Permite intercambiar implementaciones sin modificar código que las usa.
    """
    
    @abstractmethod
    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Ejecuta GET request.
        
        Args:
            url: URL objetivo
            params: Parámetros de query string
            headers: Headers HTTP
            timeout: Timeout en segundos
            **kwargs: Argumentos adicionales específicos de la implementación
        
        Returns:
            Objeto response (tipo depende de la implementación)
        """
        pass


class RequestsClientStrategy(HTTPClientStrategy):
    """Estrategia usando requests estándar."""
    
    def __init__(self, session: requests.Session):
        """
        Inicializa estrategia con sesión de requests.
        
        Args:
            session: Sesión de requests configurada
        """
        self.session = session
    
    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> requests.Response:
        """
        Ejecuta GET request usando requests.
        
        Returns:
            requests.Response
        """
        return self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout or 30,
            **kwargs
        )


class TLSClientStrategy(HTTPClientStrategy):
    """
    Estrategia usando curl_cffi para bypass TLS fingerprinting.
    
    Requiere: pip install curl-cffi
    Single Responsibility: Solo maneja requests con TLS fingerprinting bypass
    """
    
    def __init__(self):
        """Inicializa TLSClientStrategy con curl_cffi si está disponible."""
        self.use_curl = False
        try:
            from curl_cffi import requests as curl_requests
            self.session = curl_requests.Session()
            self.use_curl = True
            logger.info("TLSClientStrategy inicializado con curl_cffi")
        except ImportError:
            logger.warning("curl_cffi no instalado, usando requests estándar como fallback")
            import requests
            self.session = requests.Session()
            self.use_curl = False
    
    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
        **kwargs
    ):
        """
        Ejecuta GET request usando curl_cffi con fingerprint de Chrome.
        
        Args:
            url: URL objetivo
            params: Parámetros de query string
            headers: Headers HTTP
            timeout: Timeout en segundos
            **kwargs: Argumentos adicionales
        
        Returns:
            Response object (curl_cffi o requests según disponibilidad)
        """
        if self.use_curl:
            # Usar curl_cffi con fingerprint de Chrome 120 (más reciente)
            return self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout or 30,
                impersonate="chrome120",  # Emular Chrome 120
                **kwargs
            )
        else:
            # Fallback a requests estándar
            return self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout or 30,
                **kwargs
            )
