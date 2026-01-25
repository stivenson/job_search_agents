"""Generador de variaciones de queries usando LLM para parecer más humanas."""

from typing import List, Optional
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from config.settings import (
    LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY,
    USE_QUERY_VARIATIONS
)

logger = logging.getLogger(__name__)


class QueryVariator:
    """
    Genera variaciones naturales de queries usando LLM.
    
    Single Responsibility: Solo genera variaciones de queries
    Open/Closed: Extensible mediante diferentes estrategias de variación
    """
    
    def __init__(self, enabled: Optional[bool] = None):
        """
        Inicializa QueryVariator.
        
        Args:
            enabled: Si está habilitado. Si None, usa USE_QUERY_VARIATIONS de settings
        """
        self.enabled = enabled if enabled is not None else USE_QUERY_VARIATIONS
        self.llm = None
        
        if self.enabled:
            if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
                try:
                    self.llm = ChatAnthropic(
                        model=LLM_MODEL if "claude" in LLM_MODEL.lower() else "claude-3-5-sonnet-20241022",
                        temperature=0.7  # Más creatividad para variaciones
                    )
                    logger.debug("QueryVariator inicializado con Anthropic")
                except Exception as e:
                    logger.warning(f"Error inicializando Anthropic para QueryVariator: {e}")
            elif OPENAI_API_KEY:
                try:
                    self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0.7)
                    logger.debug("QueryVariator inicializado con OpenAI")
                except Exception as e:
                    logger.warning(f"Error inicializando OpenAI para QueryVariator: {e}")
            
            if not self.llm:
                logger.warning("QueryVariator habilitado pero sin LLM disponible, usando fallback")
    
    def generate_variations(self, keyword: str, num_variations: int = 3) -> List[str]:
        """
        Genera variaciones naturales de un keyword.
        
        Args:
            keyword: Keyword original
            num_variations: Número de variaciones a generar
        
        Returns:
            Lista de variaciones (incluye el original si falla)
        """
        if not self.enabled:
            return [keyword]
        
        # Fallback simple si no hay LLM
        if not self.llm:
            return self._simple_variations(keyword, num_variations)
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un asistente que genera variaciones naturales de búsquedas de trabajo. 
Genera variaciones que un humano usaría al buscar trabajo en un buscador de empleos, 
no keywords técnicos directos. Las variaciones deben ser frases completas y naturales."""),
                ("human", """Genera {num} variaciones naturales de búsqueda para: '{keyword}'.

Las variaciones deben:
- Sonar como búsquedas humanas reales
- Ser frases completas, no solo keywords
- Mantener el significado original
- Variar la forma de expresar el mismo concepto

Responde SOLO con las variaciones, una por línea, sin numeración ni viñetas.""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({"keyword": keyword, "num": num_variations})
            
            # Parsear respuesta
            variations = [
                v.strip() 
                for v in response.content.split('\n') 
                if v.strip() and not v.strip().startswith(('1.', '2.', '3.', '-', '*'))
            ]
            
            # Limpiar y validar
            variations = [v for v in variations if len(v) > 3 and len(v) < 100]
            
            if variations:
                # Agregar original al inicio si no está
                if keyword not in variations:
                    variations.insert(0, keyword)
                return variations[:num_variations + 1]  # +1 para incluir original
            else:
                logger.warning(f"No se generaron variaciones para '{keyword}', usando fallback")
                return self._simple_variations(keyword, num_variations)
                
        except Exception as e:
            logger.warning(f"Error generando variaciones con LLM para '{keyword}': {e}")
            return self._simple_variations(keyword, num_variations)
    
    def _simple_variations(self, keyword: str, num_variations: int) -> List[str]:
        """
        Genera variaciones simples sin LLM (fallback).
        
        Args:
            keyword: Keyword original
            num_variations: Número de variaciones
        
        Returns:
            Lista de variaciones simples
        """
        variations = [keyword]
        
        # Variaciones básicas
        if num_variations > 1:
            variations.append(f"{keyword} jobs")
        if num_variations > 2:
            variations.append(f"{keyword} position")
        if num_variations > 3:
            variations.append(f"{keyword} opportunity")
        
        return variations[:num_variations + 1]
