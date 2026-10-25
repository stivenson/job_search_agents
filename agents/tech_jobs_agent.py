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

        # Buscar Stack Overflow y GitHub Jobs en paralelo
        logger.info("Buscando en Stack Overflow y GitHub Jobs en paralelo...")
        results = await asyncio.gather(
            self.stackoverflow_client.search_jobs_async(keywords, self.max_results),
            self.github_client.search_jobs_async(keywords, self.max_results),
            return_exceptions=True
        )

        so_jobs, gh_jobs = results
        if isinstance(so_jobs, Exception):
            logger.error(f"Error buscando en Stack Overflow: {so_jobs}")
            so_jobs = []
        if isinstance(gh_jobs, Exception):
            logger.error(f"Error buscando en GitHub Jobs: {gh_jobs}")
            gh_jobs = []

        all_jobs.extend(so_jobs)
        all_jobs.extend(gh_jobs)
        logger.info(f"Stack Overflow: {len(so_jobs)} | GitHub Jobs: {len(gh_jobs)}")
        
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
