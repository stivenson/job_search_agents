"""Agente especializado para buscar trabajos técnicos en plataformas tech."""

import logging
import asyncio
from typing import List, Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.api_clients import StackOverflowJobsClient, GitHubJobsClient
from config.settings import MAX_JOBS_PER_SOURCE

logger = logging.getLogger(__name__)


class TechJobsAgent:
    """Agente para buscar trabajos técnicos en plataformas especializadas."""
    
    def __init__(self):
        self.max_results = MAX_JOBS_PER_SOURCE
        self.stackoverflow_client = StackOverflowJobsClient()
        self.github_client = GitHubJobsClient()
    
    async def search(self, keywords: List[str], region_type: Optional[str] = None) -> List[Dict]:
        """Busca trabajos técnicos en múltiples fuentes, marcando región preferida."""
        if region_type:
            logger.info(f"Buscando trabajos técnicos con keywords: {keywords} (región: {region_type})")
        else:
            logger.info(f"Buscando trabajos técnicos con keywords: {keywords}")
        
        all_jobs = []
        
        # Para trabajos remotos, no podemos filtrar por país específico,
        # pero podemos marcar la región preferida
        location_param = None  # Stack Overflow y GitHub Jobs son principalmente remotos
        
        # 1. Stack Overflow Jobs (RSS Feed)
        try:
            logger.info("Buscando en Stack Overflow Jobs...")
            so_jobs = self.stackoverflow_client.search_jobs(keywords, self.max_results, location=location_param)
            all_jobs.extend(so_jobs)
            logger.info(f"Encontrados {len(so_jobs)} trabajos en Stack Overflow")
        except Exception as e:
            logger.error(f"Error buscando en Stack Overflow: {e}")
        
        # 2. GitHub Jobs (API)
        try:
            logger.info("Buscando en GitHub Jobs...")
            gh_jobs = self.github_client.search_jobs(keywords, self.max_results)
            all_jobs.extend(gh_jobs)
            logger.info(f"Encontrados {len(gh_jobs)} trabajos en GitHub Jobs")
        except Exception as e:
            logger.error(f"Error buscando en GitHub Jobs: {e}")
        
        # Enriquecer todos los trabajos con metadata de región
        for job in all_jobs:
            if not job.get('source'):
                job['source'] = 'tech_jobs'
            job['search_keywords'] = keywords
            if not job.get('location'):
                job['location'] = 'Remote'
            if region_type:
                job['search_region'] = region_type
                job['region_priority'] = 1 if region_type == "hispanic" else 2
        
        logger.info(f"Total de trabajos técnicos encontrados: {len(all_jobs)}")
        return all_jobs
