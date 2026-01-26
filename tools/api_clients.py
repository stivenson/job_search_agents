"""Clientes para APIs de job boards."""

import requests
import logging
import random
from typing import List, Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    LINKEDIN_API_KEY, INDEED_API_KEY, REMOTEOK_API_KEY, 
    DESCRIPTION_MAX_LENGTH, REQUEST_TIMEOUT,
    USE_USER_AGENT_ROTATION, RANDOM_DELAY_ENABLED,
    MIN_DELAY, MAX_DELAY
)
from tools.base_api_client import BaseAPIClient
from utils.user_agent_rotator import UserAgentRotator
from utils.delay_manager import DelayManager
import time

logger = logging.getLogger(__name__)


class RemoteOKClient(BaseAPIClient):
    """Cliente para la API de RemoteOK."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or REMOTEOK_API_KEY
        super().__init__(base_url="https://remoteok.com/api", api_key=self.api_key)
    
    def search_jobs(self, keywords: List[str], max_results: int = 100) -> List[Dict]:
        """Busca trabajos en RemoteOK.
        
        Args:
            keywords: Lista de keywords de búsqueda
            max_results: Número máximo de resultados
        
        Returns:
            Lista de trabajos encontrados
        """
        jobs = []
        
        try:
            # Usar método base para hacer request
            response = self._make_request(self.base_url, timeout=REQUEST_TIMEOUT)
            data = response.json()
            
            # Filtrar por keywords
            for job in data[:max_results]:
                if isinstance(job, dict) and job.get('id'):
                    title = job.get('position', '')
                    description = job.get('description', '')
                    
                    # Verificar si coincide con keywords
                    matches_keyword = False
                    if keywords:
                        text_to_search = f"{title} {description}".lower()
                        for keyword in keywords:
                            if keyword.lower() in text_to_search:
                                matches_keyword = True
                                break
                    else:
                        matches_keyword = True
                    
                    if matches_keyword:
                        jobs.append({
                            'title': title,
                            'company': job.get('company', ''),
                            'location': 'Remote',
                            'url': job.get('url', ''),
                            'description': description[:DESCRIPTION_MAX_LENGTH],
                            'source': 'remoteok',
                            'keywords': keywords,
                            'tags': job.get('tags', [])
                        })
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error obteniendo trabajos de RemoteOK: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout obteniendo trabajos de RemoteOK: {e}")
        except ValueError as e:
            logger.error(f"Error parseando JSON de RemoteOK: {e}")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo trabajos de RemoteOK: {e}")
        
        return jobs


class StackOverflowJobsClient:
    """Cliente para Stack Overflow Jobs (RSS feed)."""
    
    def __init__(self):
        self.base_url = "https://stackoverflow.com/jobs/feed"
        self.session = requests.Session()
        self.ua_rotator = UserAgentRotator() if USE_USER_AGENT_ROTATION else None
        self.delay_manager = DelayManager(MIN_DELAY, MAX_DELAY) if RANDOM_DELAY_ENABLED else None
        
        # Configurar headers iniciales
        if self.ua_rotator:
            self.session.headers.update(self.ua_rotator.get_realistic_headers())
        else:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
    
    def search_jobs(self, keywords: List[str], max_results: int = 50, location: Optional[str] = None) -> List[Dict]:
        """Busca trabajos en Stack Overflow Jobs usando RSS feed.
        
        Args:
            keywords: Lista de keywords de búsqueda
            max_results: Número máximo de resultados
            location: Ubicación opcional (default: 'Remote')
        
        Returns:
            Lista de trabajos encontrados
        """
        jobs = []
        
        try:
            params = {
                'q': ' OR '.join(keywords) if keywords else '',
                'l': location or 'Remote',
                'd': '20',  # Últimos 20 días
                'u': 'Miles'
            }
            
            response = self._make_request(self.base_url, params=params, timeout=REQUEST_TIMEOUT)
            
            # Parsear RSS XML
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            items = root.findall('.//item')[:max_results]
            
            for item in items:
                try:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    company = item.find('a10:author', {'a10': 'http://www.w3.org/2005/Atom'})
                    
                    if title is not None and link is not None:
                        jobs.append({
                            'title': title.text if title.text else '',
                            'company': company.text if company is not None and company.text else '',
                            'location': 'Remote',
                            'url': link.text if link.text else '',
                            'description': description.text[:DESCRIPTION_MAX_LENGTH] if description is not None and description.text else '',
                            'source': 'stack_overflow',
                            'keywords': keywords
                        })
                except Exception as e:
                    logger.warning(f"Error procesando item de Stack Overflow: {e}")
                    continue
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP obteniendo trabajos de Stack Overflow: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout obteniendo trabajos de Stack Overflow: {e}")
        except ET.ParseError as e:
            logger.error(f"Error parseando XML de Stack Overflow: {e}")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo trabajos de Stack Overflow: {e}")
        
        return jobs


class GitHubJobsClient(BaseAPIClient):
    """Cliente para GitHub Jobs (deprecated pero aún funcional)."""
    
    def __init__(self):
        super().__init__(base_url="https://jobs.github.com/positions.json")
    
    def search_jobs(self, keywords: List[str], max_results: int = 30) -> List[Dict]:
        """Busca trabajos en GitHub Jobs."""
        jobs = []
        
        try:
            params = {
                'description': ' OR '.join(keywords) if keywords else '',
                'location': 'Remote'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            for job in data[:max_results]:
                jobs.append({
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', 'Remote'),
                    'url': job.get('url', ''),
                    'description': job.get('description', '')[:500],
                    'source': 'github_jobs',
                    'keywords': keywords,
                    'type': job.get('type', '')
                })
            
            # Delay aleatorio después del request exitoso
            if self.delay_manager:
                self.delay_manager.wait_sync()
            else:
                time.sleep(SCRAPING_DELAY)
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code in [403, 429]:
                # Rotar User-Agent si hay bloqueo
                if self.ua_rotator:
                    self.ua_rotator.rotate()
                    self.session.headers.update(self.ua_rotator.get_realistic_headers())
                logger.warning(f"Bloqueo detectado (403/429) en GitHub Jobs, rotando User-Agent...")
            logger.error(f"Error obteniendo trabajos de GitHub Jobs: {e}")
        except Exception as e:
            logger.error(f"Error obteniendo trabajos de GitHub Jobs: {e}")
        
        return jobs


class IndeedAPIClient:
    """Cliente para Indeed API (requiere API key)."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or INDEED_API_KEY
        self.base_url = "https://api.indeed.com/ads/apisearch"
        self.session = requests.Session()
        self.ua_rotator = UserAgentRotator() if USE_USER_AGENT_ROTATION else None
        self.delay_manager = DelayManager(MIN_DELAY, MAX_DELAY) if RANDOM_DELAY_ENABLED else None
        
        # Configurar headers iniciales
        if self.ua_rotator:
            self.session.headers.update(self.ua_rotator.get_realistic_headers())
        else:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
    
    def search_jobs(self, keywords: List[str], max_results: int = 50, location: Optional[str] = None) -> List[Dict]:
        """Busca trabajos usando Indeed API con ubicación opcional."""
        jobs = []
        
        if not self.api_key:
            logger.warning("Indeed API key no configurada, usando scraping en su lugar")
            return jobs
        
        try:
            params = {
                'publisher': self.api_key,
                'q': ' OR '.join(keywords) if keywords else '',
                'l': location or 'Remote',  # Usar location si se proporciona, sino 'Remote'
                'jt': 'fulltime',
                'limit': min(max_results, 25),  # API limit
                'format': 'json'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            for result in data.get('results', [])[:max_results]:
                jobs.append({
                    'title': result.get('jobtitle', ''),
                    'company': result.get('company', ''),
                    'location': result.get('formattedLocation', 'Remote'),
                    'url': result.get('url', ''),
                    'description': result.get('snippet', ''),
                    'source': 'indeed',
                    'keywords': keywords
                })
            
            # Delay aleatorio después del request exitoso
            if self.delay_manager:
                self.delay_manager.wait_sync()
            else:
                time.sleep(SCRAPING_DELAY)
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code in [403, 429]:
                # Rotar User-Agent si hay bloqueo
                if self.ua_rotator:
                    self.ua_rotator.rotate()
                    self.session.headers.update(self.ua_rotator.get_realistic_headers())
                logger.warning(f"Bloqueo detectado (403/429) en Indeed API, rotando User-Agent...")
            logger.error(f"Error obteniendo trabajos de Indeed API: {e}")
        except Exception as e:
            logger.error(f"Error obteniendo trabajos de Indeed API: {e}")
        
        return jobs
