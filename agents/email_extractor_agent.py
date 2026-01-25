"""Agente para extraer emails de descripciones de trabajos usando LLM."""

import asyncio
import logging
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.email_validator import EmailValidator
from config.settings import (
    LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY,
    EMAIL_EXTRACTION_CONCURRENCY
)

logger = logging.getLogger(__name__)


class ContactInfo(BaseModel):
    """Modelo para información de contacto extraída."""
    emails: List[str] = Field(description="Lista de emails de contacto válidos")
    application_email: Optional[str] = Field(description="Email principal para aplicar", default=None)
    recruiter_email: Optional[str] = Field(description="Email del reclutador si está disponible", default=None)
    hr_email: Optional[str] = Field(description="Email de recursos humanos", default=None)
    confidence: float = Field(description="Confianza en la extracción (0-1)", ge=0, le=1)


class EmailExtractorAgent:
    """Agente que usa LLM para extraer emails de descripciones de trabajos."""
    
    def __init__(self):
        self.validator = EmailValidator()
        
        # Inicializar LLM según configuración
        if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(
                model=LLM_MODEL if "claude" in LLM_MODEL.lower() else "claude-3-5-sonnet-20241022",
                temperature=0
            )
        elif OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=LLM_MODEL,
                temperature=0
            )
        else:
            logger.warning("No hay API key configurada, usando extracción básica con regex")
            self.llm = None
        
        # Parser de salida
        self.output_parser = PydanticOutputParser(pydantic_object=ContactInfo)
        
        # Template de prompt
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto en extraer información de contacto de descripciones de trabajos.
            
Tu tarea es identificar emails de contacto relevantes para aplicar a un trabajo. Busca:
- Emails de aplicación directa
- Emails de reclutadores
- Emails de recursos humanos
- Emails de contacto general

Ignora:
- Emails de no-reply
- Emails de notificaciones automáticas
- Emails genéricos de sistemas

Responde solo con emails válidos y relevantes."""),
            ("human", """Extrae información de contacto de esta descripción de trabajo:

{description}

{format_instructions}""")
        ])
    
    async def extract_emails(self, job_description: str) -> Dict:
        """Extrae emails de una descripción de trabajo (versión async)."""
        if not job_description:
            return {
                'emails': [],
                'application_email': None,
                'recruiter_email': None,
                'hr_email': None,
                'confidence': 0.0
            }
        
        # Primero intentar con regex básico
        basic_emails = self.validator.extract_emails(job_description)
        valid_emails = self.validator.filter_valid_emails(basic_emails)
        
        # Si no hay LLM configurado, retornar resultado básico
        if not self.llm:
            return {
                'emails': valid_emails,
                'application_email': valid_emails[0] if valid_emails else None,
                'recruiter_email': None,
                'hr_email': None,
                'confidence': 0.5 if valid_emails else 0.0
            }
        
        # Usar LLM para extracción más inteligente
        try:
            prompt = self.prompt_template.format_messages(
                description=job_description[:2000],  # Limitar tamaño
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Usar ainvoke para llamada async
            response = await self.llm.ainvoke(prompt)
            parsed = self.output_parser.parse(response.content)
            
            # Validar emails extraídos por LLM
            all_emails = []
            if parsed.emails:
                all_emails.extend(self.validator.filter_valid_emails(parsed.emails))
            
            # Agregar emails específicos si son válidos
            if parsed.application_email:
                normalized = self.validator.normalize_email(parsed.application_email)
                if normalized and normalized not in all_emails:
                    all_emails.append(normalized)
            
            if parsed.recruiter_email:
                normalized = self.validator.normalize_email(parsed.recruiter_email)
                if normalized and normalized not in all_emails:
                    all_emails.append(normalized)
            
            if parsed.hr_email:
                normalized = self.validator.normalize_email(parsed.hr_email)
                if normalized and normalized not in all_emails:
                    all_emails.append(normalized)
            
            # Combinar con emails encontrados por regex
            for email in valid_emails:
                if email not in all_emails:
                    all_emails.append(email)
            
            return {
                'emails': all_emails,
                'application_email': parsed.application_email if self.validator.is_valid_email(parsed.application_email) else (all_emails[0] if all_emails else None),
                'recruiter_email': parsed.recruiter_email if self.validator.is_valid_email(parsed.recruiter_email) else None,
                'hr_email': parsed.hr_email if self.validator.is_valid_email(parsed.hr_email) else None,
                'confidence': parsed.confidence
            }
            
        except Exception as e:
            logger.warning(f"Error usando LLM para extraer emails, usando método básico: {e}")
            return {
                'emails': valid_emails,
                'application_email': valid_emails[0] if valid_emails else None,
                'recruiter_email': None,
                'hr_email': None,
                'confidence': 0.3 if valid_emails else 0.0
            }
    
    async def extract_from_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Extrae emails de una lista de trabajos en paralelo con límite de concurrencia."""
        if not jobs:
            return []
        
        # Crear semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(EMAIL_EXTRACTION_CONCURRENCY)
        
        async def process_job(job: Dict) -> Dict:
            """Procesa un trabajo individual con control de concurrencia."""
            async with semaphore:
                description = job.get('description', '') or job.get('summary', '')
                contact_info = await self.extract_emails(description)
                
                # Agregar información de contacto al job
                job['contact_info'] = contact_info
                job['emails'] = contact_info['emails']
                job['application_email'] = contact_info['application_email']
                
                return job
        
        # Procesar todos los trabajos en paralelo
        tasks = [process_job(job) for job in jobs]
        enriched_jobs = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar excepciones y retornar solo trabajos válidos
        result = []
        for i, job in enumerate(enriched_jobs):
            if isinstance(job, Exception):
                logger.warning(f"Error procesando trabajo {i}: {job}")
                # Retornar trabajo sin emails en caso de error
                original_job = jobs[i].copy()
                original_job['contact_info'] = {
                    'emails': [],
                    'application_email': None,
                    'recruiter_email': None,
                    'hr_email': None,
                    'confidence': 0.0
                }
                original_job['emails'] = []
                original_job['application_email'] = None
                result.append(original_job)
            else:
                result.append(job)
        
        return result
