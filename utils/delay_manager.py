"""Gestor de delays aleatorios para simular comportamiento humano."""

import random
import time
import asyncio
from typing import Optional


class DelayManager:
    """Gestiona delays aleatorios con distribución normal para simular comportamiento humano."""
    
    def __init__(self, min_delay: float = 1.5, max_delay: float = 4.0):
        """
        Inicializa el gestor de delays.
        
        Args:
            min_delay: Delay mínimo en segundos
            max_delay: Delay máximo en segundos
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
    
    def get_random_delay(self) -> float:
        """
        Retorna un delay aleatorio usando distribución normal.
        
        La distribución normal está centrada en el medio del rango,
        lo que simula mejor el comportamiento humano (la mayoría de
        las acciones ocurren en tiempos intermedios, no extremos).
        
        Returns:
            Delay en segundos dentro del rango [min_delay, max_delay]
        """
        # Calcular media y desviación estándar
        mean = (self.min_delay + self.max_delay) / 2
        std_dev = (self.max_delay - self.min_delay) / 4
        
        # Generar delay con distribución normal
        delay = random.gauss(mean, std_dev)
        
        # Asegurar que está dentro del rango
        delay = max(self.min_delay, min(self.max_delay, delay))
        
        return round(delay, 2)
    
    async def wait(self):
        """Espera un delay aleatorio (versión asíncrona)."""
        await asyncio.sleep(self.get_random_delay())
    
    def wait_sync(self):
        """Espera un delay aleatorio (versión síncrona)."""
        time.sleep(self.get_random_delay())
    
    def get_uniform_delay(self) -> float:
        """
        Retorna un delay aleatorio usando distribución uniforme.
        
        Útil cuando se quiere variabilidad completa sin sesgo hacia el centro.
        
        Returns:
            Delay en segundos dentro del rango [min_delay, max_delay]
        """
        return round(random.uniform(self.min_delay, self.max_delay), 2)
