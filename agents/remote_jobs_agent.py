"""Agente especializado para buscar trabajos remotos en múltiples fuentes."""

import logging
import asyncio
from typing import List, Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.web_scraper import scrape_we_work_remotely
from tools.api_clients import RemoteOKClient
from config.settings import MAX_JOBS_PER_SOURCE

logger = logging.getLogger(__name__)


class RemoteJobsAgent:
    """Agente para buscar trabajos remotos en múltiples plataformas."""
    
    def __init__(self):
        self.max_results = MAX_JOBS_PER_SOURCE
        self.remoteok_client = RemoteOKClient()
    
    async def search(self, keywords: List[str], region_type: Optional[str] = None) -> List[Dict]:
        """Busca trabajos remotos en múltiples fuentes, marcando región preferida."""
        if region_type:
            logger.info(f"Buscando trabajos remotos con keywords: {keywords} (región: {region_type})")
        else:
            logger.info(f"Buscando trabajos remotos con keywords: {keywords}")
        
        all_jobs = []
        
        # 1. RemoteOK (API)
        try:
            logger.info("Buscando en RemoteOK...")
            remoteok_jobs = self.remoteok_client.search_jobs(keywords, self.max_results)
            all_jobs.extend(remoteok_jobs)
            logger.info(f"Encontrados {len(remoteok_jobs)} trabajos en RemoteOK")
        except Exception as e:
            logger.error(f"Error buscando en RemoteOK: {e}")
        
        # 2. We Work Remotely (Scraping)
        try:
            logger.info("Buscando en We Work Remotely...")
            wwr_jobs = await scrape_we_work_remotely(self.max_results)
            all_jobs.extend(wwr_jobs)
            logger.info(f"Encontrados {len(wwr_jobs)} trabajos en We Work Remotely")
        except Exception as e:
            logger.error(f"Error buscando en We Work Remotely: {e}")
        
        # Enriquecer todos los trabajos con metadata de región
        for job in all_jobs:
            if not job.get('source'):
                job['source'] = 'remote_jobs'
            job['search_keywords'] = keywords
            job['location'] = 'Remote'  # Todos son remotos
            if region_type:
                job['search_region'] = region_type
                job['region_priority'] = 1 if region_type == "hispanic" else 2
        
        logger.info(f"Total de trabajos remotos encontrados: {len(all_jobs)}")
        return all_jobs
