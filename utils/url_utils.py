"""Utilidades para manejo de URLs."""

from urllib.parse import urlparse
from typing import Optional


def get_domain(url: str) -> str:
    """Extrae el dominio de una URL.
    
    Args:
        url: URL completa de la que extraer el dominio
    
    Returns:
        Dominio normalizado (sin 'www.' y en minúsculas), o 'unknown' si no se puede parsear
    
    Examples:
        >>> get_domain("https://www.example.com/path")
        'example.com'
        >>> get_domain("http://jobs.github.com")
        'jobs.github.com'
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '').lower()
        return domain if domain else 'unknown'
    except Exception:
        return 'unknown'


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """Normaliza una URL, opcionalmente combinándola con una URL base.
    
    Args:
        url: URL a normalizar
        base_url: URL base opcional para URLs relativas
    
    Returns:
        URL normalizada
    """
    if not url:
        return ""
    
    # Si es una URL completa, retornarla tal cual
    if url.startswith(('http://', 'https://')):
        return url
    
    # Si hay base_url y la URL es relativa, combinarlas
    if base_url:
        from urllib.parse import urljoin
        return urljoin(base_url, url)
    
    return url


def is_valid_url(url: str) -> bool:
    """Valida si una string es una URL válida.
    
    Args:
        url: String a validar
    
    Returns:
        True si es una URL válida, False en caso contrario
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False
