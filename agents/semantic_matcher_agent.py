"""Agente para matching semántico inteligente usando LLM."""

import asyncio
import logging
import json
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.skill_loader import SkillLoader
from config.settings import (
    LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY,
    EMAIL_EXTRACTION_CONCURRENCY  # Reusar el mismo límite de concurrencia
)

logger = logging.getLogger(__name__)


class SemanticMatchResult(BaseModel):
    """Modelo para el resultado del matching semántico."""
    semantic_score: float = Field(description="Score de relevancia semántica (0-100)", ge=0, le=100)
    confidence: float = Field(description="Confianza en el análisis (0-100)", ge=0, le=100)
    key_matches: List[str] = Field(description="Razones principales por las que es un buen match")
    concerns: List[str] = Field(description="Concerns o problemas potenciales")
    recommendation: str = Field(description="Categoría del match: strong_match, good_match, fair_match, poor_match")


class SemanticMatcherAgent:
    """Agente que usa LLM para análisis semántico de relevancia entre trabajos y perfil."""
    
    def __init__(self):
        # Inicializar LLM según configuración
        if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(
                model=LLM_MODEL if "claude" in LLM_MODEL.lower() else "claude-3-5-sonnet-20241022",
                temperature=0  # Consistencia en análisis
            )
        elif OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=LLM_MODEL,
                temperature=0
            )
        else:
            logger.warning("No hay API key configurada, análisis semántico deshabilitado")
            self.llm = None
        
        # Parser de salida JSON
        self.output_parser = JsonOutputParser(pydantic_object=SemanticMatchResult)
        
        # Cargar skill para template de prompt
        skill_loader = SkillLoader()
        try:
            self.prompt_template = skill_loader.load_skill("semantic-matcher")
        except Exception as e:
            logger.warning(f"Error cargando skill semantic-matcher: {e}")
            self.prompt_template = None
    
    def _create_candidate_profile_summary(self, profile: Dict) -> str:
        """Crea un resumen del perfil del candidato para el prompt."""
        if not profile:
            return "Perfil no disponible"
        
        summary_parts = []
        
        # Skills
        skills = profile.get('skills', {})
        if isinstance(skills, dict):
            all_skills = []
            for category, items in skills.items():
                if isinstance(items, list):
                    all_skills.extend([str(item) for item in items[:5]])
            if all_skills:
                summary_parts.append(f"**Skills**: {', '.join(all_skills[:15])}")
        elif isinstance(skills, list):
            summary_parts.append(f"**Skills**: {', '.join([str(s) for s in skills[:15]])}")
        
        # Experiencia
        experience = profile.get('experience', [])
        if experience and isinstance(experience, list):
            exp_summary = []
            for exp in experience[:3]:  # Top 3 experiencias
                if isinstance(exp, dict):
                    role = exp.get('role', exp.get('title', 'N/A'))
                    company = exp.get('company', 'N/A')
                    techs = exp.get('technologies', [])
                    exp_summary.append(f"- {role} @ {company}" + (f" (Techs: {', '.join(techs[:5])})" if techs else ""))
            if exp_summary:
                summary_parts.append(f"**Experiencia Reciente**:\n" + "\n".join(exp_summary))
        
        # Nivel estimado
        years = len(experience) if isinstance(experience, list) else 0
        if years >= 5:
            level = "Senior"
        elif years >= 2:
            level = "Mid-level"
        else:
            level = "Junior/Entry"
        summary_parts.append(f"**Nivel**: {level} (~{years}+ años)")
        
        return "\n\n".join(summary_parts) if summary_parts else "Perfil técnico general"
    
    async def analyze_match(
        self,
        job: Dict,
        profile: Dict
    ) -> Dict:
        """
        Analiza semánticamente la relevancia entre un trabajo y el perfil.
        
        Args:
            job: Diccionario con información del trabajo
            profile: Perfil del candidato
        
        Returns:
            Diccionario con resultado del análisis semántico
        """
        # Si no hay LLM, retornar resultado vacío
        if not self.llm or not self.prompt_template:
            logger.debug("Análisis semántico deshabilitado (LLM no disponible)")
            return {
                'semantic_score': 0.0,
                'confidence': 0.0,
                'key_matches': [],
                'concerns': ['Análisis semántico no disponible'],
                'recommendation': 'unknown'
            }
        
        try:
            # Extraer información del trabajo
            job_title = job.get('title', 'N/A')
            job_company = job.get('company', 'N/A')
            job_location = job.get('location', 'N/A')
            job_description = job.get('description', job.get('summary', 'N/A'))[:2000]  # Limitar tamaño
            
            # Crear resumen del perfil
            candidate_profile = self._create_candidate_profile_summary(profile)
            
            # Generar prompt
            prompt = self.prompt_template.format_messages(
                job_title=job_title,
                job_company=job_company,
                job_location=job_location,
                job_description=job_description,
                candidate_profile=candidate_profile
            )
            
            # Llamar al LLM
            response = await self.llm.ainvoke(prompt)
            
            # Parsear respuesta JSON
            try:
                # Extraer JSON del contenido (puede venir con markdown)
                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
                
                # Validar campos requeridos
                required_fields = ['semantic_score', 'confidence', 'key_matches', 'concerns', 'recommendation']
                for field in required_fields:
                    if field not in result:
                        result[field] = 0.0 if field in ['semantic_score', 'confidence'] else []
                
                logger.debug(f"Análisis semántico completado: {job_title} - Score: {result['semantic_score']}")
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Error parseando JSON del análisis semántico: {e}")
                # Retornar resultado por defecto
                return {
                    'semantic_score': 50.0,  # Score neutro
                    'confidence': 30.0,
                    'key_matches': ['Análisis completado con errores de parseo'],
                    'concerns': ['No se pudo parsear respuesta completa del LLM'],
                    'recommendation': 'fair_match'
                }
                
        except Exception as e:
            logger.warning(f"Error en análisis semántico: {e}")
            return {
                'semantic_score': 0.0,
                'confidence': 0.0,
                'key_matches': [],
                'concerns': [f'Error en análisis: {str(e)[:100]}'],
                'recommendation': 'unknown'
            }
    
    async def analyze_batch(
        self,
        jobs: List[Dict],
        profile: Dict,
        concurrency_limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Analiza semánticamente un lote de trabajos en paralelo.
        
        Args:
            jobs: Lista de trabajos a analizar
            profile: Perfil del candidato
            concurrency_limit: Límite de llamadas paralelas (default: EMAIL_EXTRACTION_CONCURRENCY)
        
        Returns:
            Lista de trabajos enriquecidos con análisis semántico
        """
        if not jobs:
            return []
        
        if not self.llm or not self.prompt_template:
            logger.info("Análisis semántico deshabilitado, retornando trabajos sin modificar")
            return jobs
        
        # Usar límite de concurrencia configurado
        if concurrency_limit is None:
            concurrency_limit = EMAIL_EXTRACTION_CONCURRENCY
        
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def process_job(job: Dict) -> Dict:
            """Procesa un trabajo individual con control de concurrencia."""
            async with semaphore:
                semantic_result = await self.analyze_match(job, profile)
                
                # Agregar resultado semántico al job
                job['semantic_analysis'] = semantic_result
                job['semantic_score'] = semantic_result['semantic_score']
                
                return job
        
        logger.info(f"Analizando semánticamente {len(jobs)} trabajos en paralelo (concurrencia: {concurrency_limit})")
        
        # Procesar todos los trabajos en paralelo
        tasks = [process_job(job) for job in jobs]
        enriched_jobs = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar excepciones y retornar trabajos
        result = []
        for i, job in enumerate(enriched_jobs):
            if isinstance(job, Exception):
                logger.warning(f"Error procesando trabajo {i}: {job}")
                # Retornar trabajo sin análisis semántico
                original_job = jobs[i].copy()
                original_job['semantic_analysis'] = {
                    'semantic_score': 0.0,
                    'confidence': 0.0,
                    'key_matches': [],
                    'concerns': ['Error en análisis'],
                    'recommendation': 'unknown'
                }
                original_job['semantic_score'] = 0.0
                result.append(original_job)
            else:
                result.append(job)
        
        logger.info(f"Análisis semántico completado para {len(result)} trabajos")
        return result
    
    def combine_scores(
        self,
        heuristic_score: float,
        semantic_score: float,
        heuristic_weight: float = 0.4,
        semantic_weight: float = 0.6
    ) -> float:
        """
        Combina score heurístico y semántico con pesos configurables.
        
        Args:
            heuristic_score: Score del matching heurístico (0-100)
            semantic_score: Score del análisis semántico (0-100)
            heuristic_weight: Peso del score heurístico (default: 0.4)
            semantic_weight: Peso del score semántico (default: 0.6)
        
        Returns:
            Score combinado (0-100)
        """
        # Si no hay análisis semántico, usar solo heurístico
        if semantic_score == 0.0:
            return heuristic_score
        
        combined = (heuristic_score * heuristic_weight) + (semantic_score * semantic_weight)
        return min(100, max(0, combined))
