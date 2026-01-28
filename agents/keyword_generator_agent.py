"""Agente para generar keywords de búsqueda adaptativos usando LLM."""

import logging
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.skill_loader import SkillLoader
from config.settings import (
    LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY
)

logger = logging.getLogger(__name__)


class KeywordGeneratorAgent:
    """Agente que usa LLM para generar keywords de búsqueda adaptados dinámicamente."""
    
    def __init__(self):
        # Inicializar LLM según configuración
        if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(
                model=LLM_MODEL if "claude" in LLM_MODEL.lower() else "claude-3-5-sonnet-20241022",
                temperature=0.8  # Mayor creatividad para sinónimos
            )
        elif OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=LLM_MODEL,
                temperature=0.8
            )
        else:
            logger.warning("No hay API key configurada, usando keywords por defecto")
            self.llm = None
        
        # Cargar skill para template de prompt
        skill_loader = SkillLoader()
        try:
            self.prompt_template = skill_loader.load_skill("keyword-generator")
        except Exception as e:
            logger.warning(f"Error cargando skill keyword-generator: {e}")
            self.prompt_template = None
        
        # Caché para keywords generados
        self._cache: Dict[str, List[str]] = {}
    
    def _create_profile_summary(self, profile: Dict) -> str:
        """Crea un resumen conciso del perfil para el prompt."""
        if not profile:
            return "Perfil no disponible"
        
        summary_parts = []
        
        # Skills principales
        skills = profile.get('skills', {})
        if isinstance(skills, dict):
            # Si skills es un diccionario, tomar todas las skills
            all_skills = []
            for category, items in skills.items():
                if isinstance(items, list):
                    all_skills.extend([str(item)[:50] for item in items[:3]])  # Top 3 por categoría
            if all_skills:
                summary_parts.append(f"Skills: {', '.join(all_skills[:10])}")  # Top 10 total
        elif isinstance(skills, list):
            # Si skills es una lista directa
            summary_parts.append(f"Skills: {', '.join([str(s)[:50] for s in skills[:10]])}")
        
        # Experiencia
        experience = profile.get('experience', [])
        if experience and isinstance(experience, list) and len(experience) > 0:
            recent_exp = experience[0] if isinstance(experience[0], dict) else None
            if recent_exp and isinstance(recent_exp, dict):
                role = recent_exp.get('role', recent_exp.get('title', 'N/A'))
                summary_parts.append(f"Rol actual/reciente: {role}")
                
                # Tecnologías de experiencia reciente
                techs = recent_exp.get('technologies', [])
                if techs:
                    summary_parts.append(f"Tecnologías usadas: {', '.join(techs[:5])}")
        
        # Años de experiencia (estimado)
        years = len(experience) if isinstance(experience, list) else 0
        if years > 0:
            summary_parts.append(f"Experiencia aproximada: {min(years, 15)}+ años")
        
        return " | ".join(summary_parts) if summary_parts else "Perfil técnico"
    
    def _generate_cache_key(self, source: str, region: str, profile_hash: str) -> str:
        """Genera una clave de caché basada en parámetros."""
        return f"{source}:{region}:{profile_hash}"
    
    def _get_profile_hash(self, profile: Dict) -> str:
        """Genera un hash simple del perfil para caching."""
        # Usar skills principales como identificador
        skills = profile.get('skills', {})
        if isinstance(skills, dict):
            skills_str = str(sorted([str(k) for k in skills.keys()]))[:100]
        else:
            skills_str = str(skills)[:100]
        return str(hash(skills_str))
    
    async def generate_keywords(
        self,
        profile: Dict,
        source: str = "linkedin",
        region: str = "hispanic",
        base_keywords: Optional[List[str]] = None,
        num_keywords: int = 8
    ) -> List[str]:
        """
        Genera keywords de búsqueda adaptados dinámicamente.
        
        Args:
            profile: Perfil del usuario
            source: Fuente de búsqueda (linkedin, remoteok, etc.)
            region: Región objetivo (hispanic, english)
            base_keywords: Keywords base opcionales del config
            num_keywords: Número de keywords a generar
        
        Returns:
            Lista de keywords optimizados
        """
        # Verificar caché
        profile_hash = self._get_profile_hash(profile)
        cache_key = self._generate_cache_key(source, region, profile_hash)
        
        if cache_key in self._cache:
            logger.debug(f"Keywords obtenidos del caché para {source}/{region}")
            return self._cache[cache_key]
        
        # Si no hay LLM, usar keywords base o por defecto
        if not self.llm or not self.prompt_template:
            logger.warning("Usando keywords por defecto (LLM no disponible)")
            if base_keywords:
                return base_keywords[:num_keywords]
            return self._get_default_keywords(profile, num_keywords)
        
        try:
            # Crear resumen del perfil
            profile_summary = self._create_profile_summary(profile)
            
            # Formatear base_keywords para el prompt
            base_keywords_str = ", ".join(base_keywords) if base_keywords else "No especificados"
            
            # Generar keywords con LLM
            prompt = self.prompt_template.format_messages(
                profile_summary=profile_summary,
                source=source,
                region=region,
                base_keywords=base_keywords_str,
                num_keywords=num_keywords
            )
            
            # Llamar al LLM
            response = await self.llm.ainvoke(prompt)
            
            # Parsear respuesta
            keywords = [
                line.strip() 
                for line in response.content.split('\n') 
                if line.strip() and not line.strip().startswith(('1.', '2.', '3.', '-', '*', '#'))
            ]
            
            # Filtrar y limpiar
            keywords = [
                kw for kw in keywords 
                if len(kw) > 3 and len(kw) < 100 and kw.replace(' ', '').isalnum()
            ]
            
            # Limitar al número solicitado
            keywords = keywords[:num_keywords]
            
            if keywords:
                # Guardar en caché
                self._cache[cache_key] = keywords
                logger.info(f"Generados {len(keywords)} keywords para {source}/{region}")
                return keywords
            else:
                logger.warning(f"No se generaron keywords válidos, usando fallback")
                return self._get_fallback_keywords(profile, base_keywords, num_keywords)
                
        except Exception as e:
            logger.warning(f"Error generando keywords con LLM: {e}")
            return self._get_fallback_keywords(profile, base_keywords, num_keywords)
    
    def _get_default_keywords(self, profile: Dict, num_keywords: int) -> List[str]:
        """Genera keywords por defecto basados en el perfil."""
        keywords = []
        
        # Extraer skills del perfil
        skills = profile.get('skills', {})
        if isinstance(skills, dict):
            for category, items in list(skills.items())[:3]:  # Top 3 categorías
                if isinstance(items, list):
                    for item in items[:2]:  # Top 2 items por categoría
                        keywords.append(f"{item} Developer")
        
        # Agregar keywords genéricos si no hay suficientes
        if len(keywords) < num_keywords:
            generic = [
                "Senior Developer",
                "Software Engineer",
                "Tech Lead",
                "Full Stack Developer",
                "Backend Developer"
            ]
            keywords.extend(generic[:num_keywords - len(keywords)])
        
        return keywords[:num_keywords]
    
    def _get_fallback_keywords(
        self, 
        profile: Dict, 
        base_keywords: Optional[List[str]], 
        num_keywords: int
    ) -> List[str]:
        """Retorna keywords de fallback si la generación con LLM falla."""
        if base_keywords:
            return base_keywords[:num_keywords]
        return self._get_default_keywords(profile, num_keywords)
    
    def clear_cache(self):
        """Limpia el caché de keywords."""
        self._cache.clear()
        logger.debug("Caché de keywords limpiado")
