"""Gestor de fingerprint consistente para evitar detección."""

from typing import Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.user_agent_rotator import UserAgentRotator


class FingerprintManager:
    """Gestiona fingerprint consistente (UA, viewport, screen, etc.)."""
    
    def __init__(self):
        """Inicializa el gestor de fingerprint."""
        self.ua_rotator = UserAgentRotator()
        self.current_fingerprint: Optional[Dict] = None
    
    def generate_fingerprint(self) -> Dict:
        """
        Genera un fingerprint completo y consistente.
        
        El fingerprint incluye User-Agent, viewport, screen, platform, etc.
        que deben ser consistentes entre sí para evitar detección.
        
        Returns:
            Dict con fingerprint completo
        """
        ua = self.ua_rotator.get_random_user_agent()
        
        # Determinar viewport y screen basado en User-Agent y plataforma
        if 'Windows' in ua:
            # Resoluciones comunes en Windows
            resolutions = [
                {'width': 1920, 'height': 1080},
                {'width': 1366, 'height': 768},
                {'width': 1536, 'height': 864},
                {'width': 1440, 'height': 900},
            ]
            viewport = resolutions[0]  # Usar la más común
            screen = viewport.copy()
            platform = 'Win32'
        elif 'Macintosh' in ua:
            # Resoluciones comunes en macOS
            resolutions = [
                {'width': 1440, 'height': 900},
                {'width': 1920, 'height': 1080},
                {'width': 2560, 'height': 1440},
            ]
            viewport = resolutions[0]
            screen = viewport.copy()
            platform = 'MacIntel'
        elif 'Linux' in ua:
            # Resoluciones comunes en Linux
            resolutions = [
                {'width': 1920, 'height': 1080},
                {'width': 1366, 'height': 768},
            ]
            viewport = resolutions[0]
            screen = viewport.copy()
            platform = 'Linux x86_64'
        else:
            # Default
            viewport = {'width': 1920, 'height': 1080}
            screen = viewport.copy()
            platform = 'Win32'
        
        # Determinar idioma basado en User-Agent
        if 'Safari' in ua and 'Chrome' not in ua:
            language = 'en-US,en;q=0.9'
        else:
            language = 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7'
        
        self.current_fingerprint = {
            'user_agent': ua,
            'viewport': viewport,
            'screen': screen,
            'platform': platform,
            'language': language,
            'timezone': 'America/Bogota',  # Timezone por defecto
            'timezone_offset': -300,  # UTC-5
        }
        
        return self.current_fingerprint
    
    def get_current_fingerprint(self) -> Dict:
        """
        Retorna el fingerprint actual o genera uno nuevo.
        
        Returns:
            Dict con fingerprint actual
        """
        if not self.current_fingerprint:
            return self.generate_fingerprint()
        return self.current_fingerprint
    
    def reset_fingerprint(self):
        """Resetea el fingerprint actual, forzando generación de uno nuevo."""
        self.current_fingerprint = None
    
    def _extract_platform(self, ua: str) -> str:
        """
        Extrae plataforma del User-Agent.
        
        Args:
            ua: User-Agent string
        
        Returns:
            Plataforma (Win32, MacIntel, Linux x86_64, etc.)
        """
        if 'Windows' in ua:
            return 'Win32'
        elif 'Macintosh' in ua:
            return 'MacIntel'
        elif 'Linux' in ua:
            return 'Linux x86_64'
        return 'Win32'
    
    def get_viewport_size(self) -> Dict[str, int]:
        """
        Retorna tamaño de viewport del fingerprint actual.
        
        Returns:
            Dict con 'width' y 'height'
        """
        fingerprint = self.get_current_fingerprint()
        return fingerprint['viewport']
    
    def get_screen_size(self) -> Dict[str, int]:
        """
        Retorna tamaño de pantalla del fingerprint actual.
        
        Returns:
            Dict con 'width' y 'height'
        """
        fingerprint = self.get_current_fingerprint()
        return fingerprint['screen']
