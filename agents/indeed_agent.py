"""Agente especializado para buscar trabajos en Indeed."""

import logging
import asyncio
from typing import List, Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.web_scraper import scrape_indeed_jobs
from tools.api_clients import IndeedAPIClient
from utils.query_variator import QueryVariator
from config.settings import MAX_JOBS_PER_SOURCE, INDEED_API_KEY, USE_QUERY_VARIATIONS

logger = logging.getLogger(__name__)


class IndeedAgent:
    """Agente para buscar trabajos en Indeed."""
    
    def __init__(self, query_variator: Optional[QueryVariator] = None):
        """
        Inicializa IndeedAgent.
        
        Args:
            query_variator: Generador de variaciones de queries (opcional, Dependency Inversion)
        """
        self.max_results = MAX_JOBS_PER_SOURCE
        self.api_client = IndeedAPIClient(INDEED_API_KEY)
        self.use_api = bool(INDEED_API_KEY)
        
        # QueryVariator para generar variaciones más naturales (SOLID: Dependency Inversion)
        self.query_variator = query_variator if query_variator else (QueryVariator() if USE_QUERY_VARIATIONS else None)
    
    async def search(self, keywords: List[str], countries: Optional[List[str]] = None) -> List[Dict]:
        """Busca trabajos en Indeed, opcionalmente filtrado por países."""
        # Generar variaciones de queries si está habilitado
        search_keywords = keywords
        if self.query_variator:
            try:
                # Generar variaciones para cada keyword (máximo 2 variaciones por keyword)
                expanded_keywords = []
                for keyword in keywords:
                    variations = self.query_variator.generate_variations(keyword, num_variations=2)
                    expanded_keywords.extend(variations[:3])  # Limitar a 3 por keyword
                
                if expanded_keywords:
                    search_keywords = expanded_keywords
                    logger.debug(f"Keywords expandidos: {len(keywords)} -> {len(search_keywords)} variaciones")
            except Exception as e:
                logger.warning(f"Error generando variaciones de queries: {e}, usando keywords originales")
                search_keywords = keywords
        
        if countries:
            logger.info(f"Buscando trabajos en Indeed con keywords: {keywords} en países: {countries}")
        else:
            logger.info(f"Buscando trabajos en Indeed con keywords: {keywords}")
        
        all_jobs = []
        
        try:
            if countries:
                # Hacer búsqueda por cada país
                for country in countries:
                    try:
                        if self.use_api:
                            # Intentar usar API primero
                            logger.info(f"Usando Indeed API para país: {country}")
                            jobs = self.api_client.search_jobs(search_keywords, self.max_results, location=country)
                        else:
                            # Fallback a scraping
                            logger.info(f"Usando scraping para Indeed en país: {country}")
                            jobs = await scrape_indeed_jobs(search_keywords, self.max_results, location=country)
                        
                        # Enriquecer con información adicional
                        for job in jobs:
                            job['source'] = 'indeed'
                            job['search_keywords'] = keywords
                            job['search_country'] = country
                            if not job.get('location'):
                                job['location'] = country or 'Remote'
                        all_jobs.extend(jobs)
                    except Exception as e:
                        logger.warning(f"Error buscando en Indeed para país {country}: {e}")
                        continue
            else:
                # Búsqueda normal (sin filtro de país)
                if self.use_api:
                    # Intentar usar API primero
                    logger.info("Usando Indeed API")
                    jobs = self.api_client.search_jobs(search_keywords, self.max_results)
                else:
                    # Fallback a scraping
                    logger.info("Usando scraping para Indeed")
                    jobs = await scrape_indeed_jobs(search_keywords, self.max_results)
                
                # Enriquecer con información adicional
                for job in jobs:
                    job['source'] = 'indeed'
                    job['search_keywords'] = keywords
                    if not job.get('location'):
                        job['location'] = 'Remote'
                all_jobs = jobs
            
            logger.info(f"Encontrados {len(all_jobs)} trabajos en Indeed")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error buscando en Indeed: {e}")
            return []
