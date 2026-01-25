"""Agente especializado para buscar trabajos en LinkedIn."""

import logging
import asyncio
from typing import List, Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.web_scraper import scrape_linkedin_jobs
from config.settings import MAX_JOBS_PER_SOURCE
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class LinkedInAgent:
    """Agente para buscar trabajos en LinkedIn."""
    
    def __init__(self):
        self.max_results = MAX_JOBS_PER_SOURCE
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Carga configuración de job_sources.yaml."""
        config_path = Path(__file__).parent.parent / "config" / "job_sources.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
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
                        jobs = await scrape_linkedin_jobs(keywords, self.max_results, location=country)
                        # Enriquecer con información adicional
                        for job in jobs:
                            job['source'] = 'linkedin'
                            job['search_keywords'] = keywords
                            job['search_country'] = country
                            if not job.get('location'):
                                job['location'] = country or 'Remote'
                        all_jobs.extend(jobs)
                    except Exception as e:
                        logger.warning(f"Error buscando en LinkedIn para país {country}: {e}")
                        continue
            else:
                # Búsqueda normal (sin filtro de país)
                jobs = await scrape_linkedin_jobs(keywords, self.max_results)
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
        """Filtra trabajos por criterios específicos."""
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
