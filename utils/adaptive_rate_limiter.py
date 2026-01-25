"""Rate limiter adaptativo que ajusta delays según respuestas del servidor."""

from typing import Dict
from datetime import datetime
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.delay_manager import DelayManager
from config.settings import MIN_DELAY, MAX_DELAY

logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """Rate limiter que se adapta a respuestas del servidor."""
    
    def __init__(self, base_min_delay: float = None, base_max_delay: float = None):
        """
        Inicializa el rate limiter adaptativo.
        
        Args:
            base_min_delay: Delay mínimo base (usa MIN_DELAY de settings si es None)
            base_max_delay: Delay máximo base (usa MAX_DELAY de settings si es None)
        """
        min_delay = base_min_delay if base_min_delay is not None else MIN_DELAY
        max_delay = base_max_delay if base_max_delay is not None else MAX_DELAY
        
        self.base_min_delay = min_delay
        self.base_max_delay = max_delay
        self.delay_manager = DelayManager(min_delay, max_delay)
        self.domain_stats: Dict[str, Dict] = {}  # domain -> stats
    
    def record_response(self, domain: str, status_code: int, response_time: float = 0.0):
        """
        Registra respuesta y ajusta delays según el resultado.
        
        Args:
            domain: Dominio que respondió
            status_code: Código de estado HTTP
            response_time: Tiempo de respuesta en segundos
        """
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {
                'success_count': 0,
                'error_count': 0,
                'last_403': None,
                'avg_response_time': response_time if response_time > 0 else 1.0,
                'consecutive_errors': 0
            }
        
        stats = self.domain_stats[domain]
        
        if status_code == 200:
            stats['success_count'] += 1
            stats['consecutive_errors'] = 0
            # Reducir contador de errores gradualmente
            stats['error_count'] = max(0, stats['error_count'] - 1)
            
            # Si hay muchos éxitos, reducir delays gradualmente
            if stats['success_count'] % 10 == 0 and stats['error_count'] == 0:
                if self.delay_manager.min_delay > self.base_min_delay:
                    self.delay_manager.min_delay = max(
                        self.base_min_delay,
                        self.delay_manager.min_delay * 0.9
                    )
                if self.delay_manager.max_delay > self.base_max_delay:
                    self.delay_manager.max_delay = max(
                        self.base_max_delay,
                        self.delay_manager.max_delay * 0.9
                    )
                logger.debug(f"Delays reducidos para {domain} después de éxitos")
                
        elif status_code in [403, 429]:
            stats['error_count'] += 1
            stats['consecutive_errors'] += 1
            stats['last_403'] = datetime.now()
            
            # Aumentar delays si hay errores
            if stats['consecutive_errors'] > 2:
                multiplier = 1.0 + (stats['consecutive_errors'] * 0.3)
                self.delay_manager.min_delay = min(10.0, self.delay_manager.min_delay * multiplier)
                self.delay_manager.max_delay = min(20.0, self.delay_manager.max_delay * multiplier)
                logger.warning(
                    f"Delays aumentados para {domain} después de {stats['consecutive_errors']} errores consecutivos"
                )
        
        # Calcular promedio de tiempo de respuesta
        if response_time > 0:
            stats['avg_response_time'] = (stats['avg_response_time'] + response_time) / 2
    
    def get_delay(self, domain: str) -> float:
        """
        Retorna delay apropiado para el dominio.
        
        Args:
            domain: Dominio para el cual obtener delay
        
        Returns:
            Delay en segundos
        """
        if domain in self.domain_stats:
            stats = self.domain_stats[domain]
            
            # Delay extra largo si hay muchos errores
            if stats.get('consecutive_errors', 0) > 5:
                base_delay = self.delay_manager.get_random_delay()
                return base_delay * 2.5
            
            # Delay moderado si hay algunos errores
            if stats.get('error_count', 0) > 3:
                base_delay = self.delay_manager.get_random_delay()
                return base_delay * 1.5
        
        return self.delay_manager.get_random_delay()
    
    def get_stats(self, domain: str) -> Dict:
        """
        Retorna estadísticas para un dominio.
        
        Args:
            domain: Dominio a consultar
        
        Returns:
            Dict con estadísticas
        """
        return self.domain_stats.get(domain, {})
    
    def reset_domain(self, domain: str):
        """Resetea estadísticas para un dominio."""
        if domain in self.domain_stats:
            del self.domain_stats[domain]
            logger.debug(f"Estadísticas reseteadas para {domain}")
