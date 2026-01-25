"""Gestor de sesiones HTTP persistentes con cookies."""

from typing import Dict, Optional
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)


class SessionManager:
    """Gestiona sesiones HTTP con cookies persistentes por dominio."""
    
    def __init__(self, cookies_dir: Optional[Path] = None):
        """
        Inicializa el gestor de sesiones.
        
        Args:
            cookies_dir: Directorio donde guardar cookies. Si es None, usa DATA_DIR/cookies
        """
        self.cookies_dir = cookies_dir or (DATA_DIR / "cookies")
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, Dict] = {}  # domain -> session_data
    
    def get_cookies_file(self, domain: str) -> Path:
        """
        Retorna path al archivo de cookies para un dominio.
        
        Args:
            domain: Dominio (ej: 'indeed.com')
        
        Returns:
            Path al archivo de cookies
        """
        safe_domain = domain.replace('.', '_').replace('/', '_').replace(':', '_')
        return self.cookies_dir / f"{safe_domain}_cookies.json"
    
    def load_cookies(self, domain: str) -> Dict:
        """
        Carga cookies guardadas para un dominio.
        
        Args:
            domain: Dominio para el cual cargar cookies
        
        Returns:
            Dict con cookies (formato requests.cookies)
        """
        cookies_file = self.get_cookies_file(domain)
        if cookies_file.exists():
            try:
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Verificar expiración
                    expires_str = data.get('expires', '2000-01-01T00:00:00')
                    try:
                        expires = datetime.fromisoformat(expires_str)
                        if expires > datetime.now():
                            return data.get('cookies', {})
                        else:
                            logger.debug(f"Cookies expiradas para {domain}")
                    except ValueError:
                        # Si no se puede parsear fecha, usar cookies de todas formas
                        return data.get('cookies', {})
            except Exception as e:
                logger.warning(f"Error cargando cookies para {domain}: {e}")
        return {}
    
    def save_cookies(self, domain: str, cookies: Dict, expires_hours: int = 24):
        """
        Guarda cookies para un dominio.
        
        Args:
            domain: Dominio para el cual guardar cookies
            cookies: Dict con cookies (puede ser de requests.cookies o dict simple)
            expires_hours: Horas hasta que expiren las cookies
        """
        cookies_file = self.get_cookies_file(domain)
        try:
            # Convertir cookies a dict si es necesario
            if hasattr(cookies, 'get_dict'):
                cookies_dict = cookies.get_dict()
            elif isinstance(cookies, dict):
                cookies_dict = cookies
            else:
                cookies_dict = {}
            
            expires = datetime.now() + timedelta(hours=expires_hours)
            data = {
                'cookies': cookies_dict,
                'expires': expires.isoformat(),
                'domain': domain,
                'saved_at': datetime.now().isoformat()
            }
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cookies guardadas para {domain}")
        except Exception as e:
            logger.warning(f"Error guardando cookies para {domain}: {e}")
    
    def update_cookies_from_response(self, domain: str, response_cookies, expires_hours: int = 24):
        """
        Actualiza cookies desde una respuesta HTTP.
        
        Args:
            domain: Dominio
            response_cookies: Cookies de una respuesta (requests.cookies)
            expires_hours: Horas hasta que expiren
        """
        if response_cookies:
            self.save_cookies(domain, response_cookies, expires_hours)
    
    def clear_cookies(self, domain: str):
        """Elimina cookies guardadas para un dominio."""
        cookies_file = self.get_cookies_file(domain)
        if cookies_file.exists():
            try:
                cookies_file.unlink()
                logger.info(f"Cookies eliminadas para {domain}")
            except Exception as e:
                logger.warning(f"Error eliminando cookies para {domain}: {e}")
