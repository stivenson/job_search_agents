"""Agente especializado para buscar trabajos en Findjobit."""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.web_scraper import SimpleHTTPScraper

logger = logging.getLogger(__name__)


class FindjobitAgent:
    """Agente para buscar trabajos en Findjobit (portal LATAM)."""

    def __init__(self):
        self.scraper = SimpleHTTPScraper()
        self.base_url = "https://findjobit.com"

    async def search(self, keywords: List[str], region_type: Optional[str] = None) -> List[Dict]:
        """
        Busca trabajos en Findjobit con soporte para filtros regionales.

        Findjobit es un portal enfocado en LATAM con trabajos técnicos.
        Soporta búsqueda por keywords y tiene filtros por país LATAM.
        """
        if region_type:
            logger.info(f"Buscando trabajos en Findjobit con keywords: {keywords} (región: {region_type})")
        else:
            logger.info(f"Buscando trabajos en Findjobit con keywords: {keywords}")

        all_jobs = []

        # Findjobit no tiene API, necesitamos scraping web
        # La página principal muestra trabajos por categoría
        try:
            html = await asyncio.get_event_loop().run_in_executor(None, self.scraper.fetch, self.base_url)
            soup = self.scraper.parse_html(html)

            # Buscar trabajos en la página principal
            jobs_found = self._extract_jobs_from_page(soup, keywords)
            all_jobs.extend(jobs_found)

            # También buscar en páginas de categorías específicas si los keywords lo sugieren
            category_jobs = await self._search_by_categories(keywords)
            all_jobs.extend(category_jobs)

            # Filtrar duplicados por URL
            unique_jobs = self._remove_duplicates(all_jobs)

            # Marcar metadata de región
            for job in unique_jobs:
                job['search_keywords'] = keywords
                if not job.get('location'):
                    job['location'] = 'Remote/LATAM'
                if region_type:
                    job['search_region'] = region_type
                    job['region_priority'] = 1 if region_type == "hispanic" else 2

            logger.info(f"Encontrados {len(unique_jobs)} trabajos en Findjobit")
            return unique_jobs

        except Exception as e:
            logger.error(f"Error buscando en Findjobit: {e}")
            return []

    def _extract_jobs_from_page(self, soup: BeautifulSoup, keywords: List[str]) -> List[Dict]:
        """Extrae trabajos de una página HTML de Findjobit.
        
        Args:
            soup: BeautifulSoup object con el HTML parseado
            keywords: Lista de keywords para filtrar trabajos
        
        Returns:
            Lista de trabajos extraídos
        """
        jobs = []

        # Selectores CSS basados en la estructura de Findjobit
        # Buscar elementos de trabajo (ajustar según la estructura real)
        job_selectors = [
            '.job-card',
            '.vacancy-card',
            '.job-listing',
            'article.job',
            '.job-item'
        ]

        job_elements = []
        for selector in job_selectors:
            elements = soup.select(selector)
            if elements:
                job_elements = elements
                logger.debug(f"Encontrados {len(elements)} trabajos con selector: {selector}")
                break

        # Si no encontramos con selectores específicos, buscar en todo el contenido
        if not job_elements:
            # Buscar enlaces que contengan "job" o títulos de trabajo
            all_links = soup.find_all('a', href=True)
            job_links = [link for link in all_links if any(kw.lower() in link.get_text().lower() or kw.lower() in link.get('href', '').lower()
                                                           for kw in ['ingeniero', 'developer', 'engineer', 'desarrollador', 'backend', 'frontend', 'fullstack', 'ai', 'python', 'llm', 'ml'])]

            # Convertir enlaces en objetos de trabajo básicos
            for link in job_links[:20]:  # Limitar a 20 trabajos
                title = link.get_text().strip()
                url = link.get('href')
                if url and not url.startswith('http'):
                    url = f"{self.base_url}{url}" if url.startswith('/') else f"{self.base_url}/{url}"

                if title and len(title) > 10:  # Evitar títulos demasiado cortos
                    job = {
                        'title': title,
                        'company': self._extract_company_from_title(title),
                        'location': 'LATAM/Remote',
                        'url': url,
                        'description': title,  # Usar título como descripción básica
                        'source': 'findjobit',
                        'keywords': keywords
                    }
                    jobs.append(job)

        # Procesar elementos de trabajo encontrados con selectores
        for element in job_elements[:50]:  # Limitar a 50 trabajos por página
            try:
                # Extraer información del trabajo
                title_elem = element.select_one('h3, .title, .job-title, .position')
                company_elem = element.select_one('.company, .employer, .company-name')
                location_elem = element.select_one('.location, .place, .country')
                link_elem = element.select_one('a') or element.find_parent('a')

                title = self.scraper.extract_text(title_elem) if title_elem else ""
                company = self.scraper.extract_text(company_elem) if company_elem else ""
                location = self.scraper.extract_text(location_elem) if location_elem else "LATAM"

                # Si no hay compañía en elemento específico, intentar extraerla del título
                if not company and title:
                    company = self._extract_company_from_title(title)

                url = ""
                if link_elem:
                    href = link_elem.get('href')
                    if href:
                        if href.startswith('http'):
                            url = href
                        else:
                            url = f"{self.base_url}{href}" if href.startswith('/') else f"{self.base_url}/{href}"

                if title and url:
                    job = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'url': url,
                        'description': title,  # Descripción básica
                        'source': 'findjobit',
                        'keywords': keywords
                    }
                    jobs.append(job)

            except Exception as e:
                logger.warning(f"Error procesando elemento de trabajo en Findjobit: {e}")
                continue

        return jobs

    def _extract_company_from_title(self, title: str) -> str:
        """Extrae nombre de compañía del título si está presente.
        
        Args:
            title: Título del trabajo que puede contener nombre de compañía
        
        Returns:
            Nombre de la compañía extraído, o string vacío si no se encuentra
        """
        # Patrones comunes: "Company - Title" o "Title at Company"
        separators = [' - ', ' at ', ' | ', ' @ ', ' para ', ' en ']

        for sep in separators:
            if sep in title:
                parts = title.split(sep)
                if len(parts) >= 2:
                    # Asumir que la compañía está al inicio o final según el separador
                    if sep in [' - ', ' | ']:
                        return parts[0].strip()
                    elif sep in [' at ', ' @ ', ' en ']:
                        return parts[-1].strip()

        return ""

    async def _search_by_categories(self, keywords: List[str]) -> List[Dict]:
        """
        Busca trabajos en categorías específicas de Findjobit.

        Nota: Findjobit tiene una estructura de URLs compleja.
        Por ahora nos enfocamos en la página principal que funciona bien.
        """
        # TODO: Implementar búsqueda por categorías cuando se determine la estructura correcta
        # Las URLs de categorías parecen devolver errores 500 actualmente
        logger.debug("Búsqueda por categorías deshabilitada temporalmente - enfocándonos en página principal")
        return []

    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Elimina trabajos duplicados basados en URL.
        
        Args:
            jobs: Lista de trabajos que puede contener duplicados
        
        Returns:
            Lista de trabajos únicos (sin duplicados por URL)
        """
        seen_urls = set()
        unique_jobs = []

        for job in jobs:
            url = job.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)

        return unique_jobs