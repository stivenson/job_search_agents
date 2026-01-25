"""Circuit Breaker para detectar y manejar bloqueos persistentes."""

from typing import Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del Circuit Breaker."""
    CLOSED = "closed"  # Funcionando normalmente
    OPEN = "open"      # Bloqueado, no intentar
    HALF_OPEN = "half_open"  # Probando si se recuperó


class CircuitBreaker:
    """Circuit Breaker para detectar bloqueos persistentes por dominio."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 300):
        """
        Inicializa el Circuit Breaker.
        
        Args:
            failure_threshold: Número de fallos consecutivos antes de abrir el circuito
            timeout_seconds: Segundos antes de intentar recuperación (HALF_OPEN)
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.circuits: Dict[str, Dict] = {}  # domain -> circuit_state
    
    def record_success(self, domain: str):
        """
        Registra éxito, resetea contador de fallos.
        
        Args:
            domain: Dominio que tuvo éxito
        """
        if domain not in self.circuits:
            self.circuits[domain] = {
                'state': CircuitState.CLOSED,
                'failures': 0,
                'last_failure': None,
                'success_count': 0
            }
        
        circuit = self.circuits[domain]
        circuit['failures'] = 0
        circuit['success_count'] = circuit.get('success_count', 0) + 1
        
        # Si estaba en HALF_OPEN y tuvo éxito, cerrar el circuito
        if circuit['state'] == CircuitState.HALF_OPEN:
            circuit['state'] = CircuitState.CLOSED
            logger.info(f"Circuit breaker CLOSED para {domain} después de recuperación exitosa")
        else:
            circuit['state'] = CircuitState.CLOSED
    
    def record_failure(self, domain: str):
        """
        Registra fallo, puede abrir circuito.
        
        Args:
            domain: Dominio que falló
        """
        if domain not in self.circuits:
            self.circuits[domain] = {
                'state': CircuitState.CLOSED,
                'failures': 0,
                'last_failure': None,
                'success_count': 0
            }
        
        circuit = self.circuits[domain]
        circuit['failures'] += 1
        circuit['last_failure'] = datetime.now()
        
        # Si estaba en HALF_OPEN y falló, volver a abrir
        if circuit['state'] == CircuitState.HALF_OPEN:
            circuit['state'] = CircuitState.OPEN
            logger.warning(f"Circuit breaker re-abierto para {domain} después de fallo en HALF_OPEN")
        
        # Abrir circuito si se alcanza el umbral
        if circuit['failures'] >= self.failure_threshold and circuit['state'] != CircuitState.OPEN:
            circuit['state'] = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPEN para {domain} después de {self.failure_threshold} fallos")
    
    def is_open(self, domain: str) -> bool:
        """
        Verifica si el circuito está abierto.
        
        Args:
            domain: Dominio a verificar
        
        Returns:
            True si el circuito está abierto y no ha pasado el timeout
        """
        if domain not in self.circuits:
            return False
        
        circuit = self.circuits[domain]
        
        # Si está abierto, verificar timeout
        if circuit['state'] == CircuitState.OPEN:
            if circuit['last_failure']:
                elapsed = (datetime.now() - circuit['last_failure']).total_seconds()
                if elapsed >= self.timeout_seconds:
                    circuit['state'] = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker HALF_OPEN para {domain}, probando recuperación")
                    return False
            return True
        
        return False
    
    def get_state(self, domain: str) -> CircuitState:
        """
        Retorna el estado actual del circuito para un dominio.
        
        Args:
            domain: Dominio a consultar
        
        Returns:
            Estado del circuito
        """
        if domain not in self.circuits:
            return CircuitState.CLOSED
        return self.circuits[domain]['state']
    
    def reset(self, domain: str):
        """Resetea el circuito para un dominio."""
        if domain in self.circuits:
            self.circuits[domain] = {
                'state': CircuitState.CLOSED,
                'failures': 0,
                'last_failure': None,
                'success_count': 0
            }
            logger.info(f"Circuit breaker reseteado para {domain}")
