"""Utilidades HTTP compartidas para reducir duplicación en scrapers y API clients."""

import time
import logging
from typing import Optional
from requests import Session

logger = logging.getLogger(__name__)


def setup_session_headers(session: Session, ua_rotator: Optional['UserAgentRotator'] = None, 
                          user_agent: Optional[str] = None) -> None:
    """Configura headers de sesión con User-Agent apropiado.
    
    Args:
        session: Sesión de requests a configurar
        ua_rotator: UserAgentRotator opcional para obtener headers realistas
        user_agent: User-Agent específico a usar si no hay rotator
    """
    if ua_rotator:
        headers = ua_rotator.get_realistic_headers()
        session.headers.update(headers)
    elif user_agent:
        session.headers.update({'User-Agent': user_agent})
    else:
        # Fallback a User-Agent por defecto
        default_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        session.headers.update({'User-Agent': default_ua})


def handle_rate_limit_error(ua_rotator: Optional['UserAgentRotator'], 
                            session: Optional[Session],
                            url: str) -> None:
    """Maneja errores de rate limiting (403/429) rotando User-Agent.
    
    Args:
        ua_rotator: UserAgentRotator opcional para rotar User-Agent
        session: Sesión de requests opcional para actualizar headers
        url: URL que causó el error (para logging)
    """
    if ua_rotator:
        ua_rotator.rotate()
        logger.warning(f"Rate limit detectado para {url}, rotando User-Agent...")
        
        if session:
            headers = ua_rotator.get_realistic_headers()
            session.headers.update(headers)
    else:
        logger.warning(f"Rate limit detectado para {url}, pero no hay rotator disponible")


def wait_with_delay(delay_manager: Optional['DelayManager'] = None, 
                   default_delay: float = 2.0,
                   use_async: bool = False) -> None:
    """Aplica delay con o sin manager, soportando sync y async.
    
    Args:
        delay_manager: DelayManager opcional para delays aleatorios
        default_delay: Delay por defecto si no hay manager
        use_async: Si True, retorna coroutine para await
    """
    if use_async:
        import asyncio
        if delay_manager:
            return delay_manager.wait()
        return asyncio.sleep(default_delay)
    else:
        if delay_manager:
            delay_manager.wait_sync()
        else:
            time.sleep(default_delay)


def get_default_headers(user_agent: Optional[str] = None) -> dict:
    """Obtiene headers HTTP por defecto realistas.
    
    Args:
        user_agent: User-Agent específico, o usa uno por defecto
    
    Returns:
        Diccionario de headers HTTP
    """
    default_ua = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    return {
        'User-Agent': default_ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
