"""Agente para consultar las ofertas públicas de Computrabajo Colombia."""

import asyncio
import logging
from typing import Dict, List, Optional
from config.config_loader import load_job_sources_config
from config.settings import MAX_JOBS_PER_SOURCE
from tools.web_scraper import scrape_computrabajo_jobs

logger = logging.getLogger(__name__)


class ComputrabajoAgent:
    """Busca vacantes y conserva solo las ubicadas en la región solicitada."""

    def __init__(self):
        config = load_job_sources_config()
        source_config = config.get("job_sources", {}).get("computrabajo", {})
        self.max_results = min(MAX_JOBS_PER_SOURCE, int(source_config.get("max_results", MAX_JOBS_PER_SOURCE)))
        self.base_url = source_config.get("base_url", "https://co.computrabajo.com")
        self.search_path_template = source_config.get("search_path_template", "/trabajo-de-{keyword}-en-{city}")
        self.max_keywords = int(source_config.get("max_keywords", 8))
        self.location_terms = config.get("matching", {}).get("locality_terms", [])

    async def search(
        self,
        keywords: List[str],
        countries: Optional[List[str]] = None,
        region_type: Optional[str] = None,
    ) -> List[Dict]:
        if not countries:
            return []

        all_jobs: List[Dict] = []
        for location in countries:
            jobs = await asyncio.to_thread(
                scrape_computrabajo_jobs,
                keywords[:self.max_keywords],
                self.max_results - len(all_jobs),
                location,
                self.base_url,
                self.search_path_template,
                self.location_terms,
            )
            for job in jobs:
                job["search_country"] = location
                job["search_region"] = region_type
                job["region_priority"] = 1 if region_type == "hispanic" else 2
            all_jobs.extend(jobs)
            if len(all_jobs) >= self.max_results:
                break

        logger.info("Computrabajo: %s vacantes en %s", len(all_jobs), ", ".join(countries))
        return all_jobs[:self.max_results]
