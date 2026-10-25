"""Agente especializado para buscar trabajos en LinkedIn."""

import logging
import asyncio
from typing import List, Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.web_scraper import scrape_linkedin_jobs
from config.settings import MAX_JOBS_PER_SOURCE
from config.config_loader import load_job_sources_config

logger = logging.getLogger(__name__)


class LinkedInAgent:
    """Agente para buscar trabajos en LinkedIn."""
    
    def __init__(self):
        self.config = self._load_config()
        source_config = self.config.get("job_sources", {}).get("linkedin", {})
        self.max_results = min(MAX_JOBS_PER_SOURCE, int(source_config.get("max_results", MAX_JOBS_PER_SOURCE)))
        self.base_url = source_config.get("base_url", "https://www.linkedin.com/jobs/search")
        self.max_keywords = int(source_config.get("max_keywords", 3))
    
    def _load_config(self) -> Dict:
        """Carga configuración de job_sources.yaml."""
        return load_job_sources_config()
    
    async def search(self, keywords: List[str], countries: Optional[List[str]] = None) -> List[Dict]:
        """Busca trabajos en LinkedIn, opcionalmente filtrado por países."""
        if countries:
            logger.info(f"Buscando trabajos en LinkedIn con keywords: {keywords} en países: {countries}")
        else:
            logger.info(f"Buscando trabajos en LinkedIn con keywords: {keywords}")
        
        try:
            all_jobs = []
            
            if countries:
                # Hacer búsqueda por cada país
                for country in countries:
                    try:
                        jobs = await scrape_linkedin_jobs(keywords, self.max_results, location=country, base_url=self.base_url, max_keywords=self.max_keywords)
                        # Enriquecer con información adicional
                        for job in jobs:
                            job['source'] = 'linkedin'
                            job['search_keywords'] = keywords
                            job['search_country'] = country
                            title = (job.get('title') or '').casefold()
                            explicit_remote = any(term in title for term in ('remote', 'remoto', 'teletrabajo', 'work from home'))
                            job['is_remote'] = explicit_remote
                            if explicit_remote:
                                # LinkedIn may show the searched city on remote
                                # recommendations; keep that separate from the job's actual modality.
                                job['location'] = 'Remoto (Colombia)'
                            elif not job.get('location'):
                                job['location'] = 'Ubicación no confirmada'
                            job['search_location'] = country
                        all_jobs.extend(jobs)
                    except Exception as e:
                        logger.warning(f"Error buscando en LinkedIn para país {country}: {e}")
                        continue
            else:
                # Búsqueda normal (sin filtro de país)
                jobs = await scrape_linkedin_jobs(keywords, self.max_results, base_url=self.base_url, max_keywords=self.max_keywords)
                # Enriquecer con información adicional
                for job in jobs:
                    job['source'] = 'linkedin'
                    job['search_keywords'] = keywords
                    if not job.get('location'):
                        job['location'] = 'Remote'  # Asumir remote si no se especifica
                all_jobs = jobs
            
            logger.info(f"Encontrados {len(all_jobs)} trabajos en LinkedIn")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error buscando en LinkedIn: {e}")
            return []
    
    def filter_by_criteria(self, jobs: List[Dict], criteria: Dict) -> List[Dict]:
        """
        Filtra trabajos por criterios específicos.
        
        NOTA: Este método está definido pero NO se llama actualmente desde el orquestador.
        Está preparado para uso futuro cuando se implemente filtrado pre-búsqueda.
        
        Puede usar filters.employment_type y filters.location del job_sources.yaml.
        Actualmente, el sistema usa matching.employment_type_terms y matching.location_terms
        para scoring post-búsqueda en lugar de filtrado pre-búsqueda.
        """
        filtered = []
        
        for job in jobs:
            # Filtrar por tipo de empleo
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            
            # Verificar tipo de empleo
            employment_types = criteria.get('employment_type', [])
            if employment_types:
                matches_type = any(et.lower() in job_text for et in employment_types)
                if not matches_type:
                    continue
            
            # Verificar ubicación
            location = job.get('location', '').lower()
            locations = criteria.get('location', [])
            if locations:
                matches_location = any(loc.lower() in location for loc in locations)
                if not matches_location:
                    continue
            
            filtered.append(job)
        
        return filtered
