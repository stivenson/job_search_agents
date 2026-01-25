"""Orquestador principal usando LangGraph para coordinar todos los agentes."""

import logging
import asyncio
import sys
from typing import TypedDict, List, Dict
from pathlib import Path
from langgraph.graph import StateGraph, END
import yaml

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.linkedin_agent import LinkedInAgent
# from agents.indeed_agent import IndeedAgent  # Deshabilitado: difícil acceso
from agents.remote_jobs_agent import RemoteJobsAgent
from agents.tech_jobs_agent import TechJobsAgent
from agents.findjobit_agent import FindjobitAgent
from agents.email_extractor_agent import EmailExtractorAgent
from agents.matcher_agent import MatcherAgent
from utils.cv_parser import CVParser
from utils.progress_logger import get_progress_logger
from config.settings import DATA_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)


class JobSearchState(TypedDict):
    """Estado compartido del workflow de búsqueda de empleo."""
    profile: Dict
    keywords: List[str]
    jobs: List[Dict]
    matched_jobs: List[Dict]
    emails: List[str]
    summary: Dict
    errors: List[str]


class JobSearchOrchestrator:
    """Orquestador principal que coordina todos los agentes."""
    
    def __init__(self):
        self.linkedin_agent = LinkedInAgent()
        # self.indeed_agent = IndeedAgent()  # Deshabilitado: difícil acceso
        self.remote_agent = RemoteJobsAgent()
        self.tech_agent = TechJobsAgent()
        self.findjobit_agent = FindjobitAgent()
        self.email_extractor = EmailExtractorAgent()
        self.matcher = MatcherAgent()
        self.cv_parser = CVParser()
        
        # Cargar configuración
        config_path = Path(__file__).parent.parent / "config" / "job_sources.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
        
        # Construir grafo
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construye el grafo de LangGraph."""
        workflow = StateGraph(JobSearchState)
        
        # Agregar nodos
        workflow.add_node("parse_profile", self._parse_profile)
        workflow.add_node("search_all", self._search_all_parallel)
        workflow.add_node("extract_emails", self._extract_emails)
        workflow.add_node("match_jobs", self._match_jobs)
        workflow.add_node("generate_summary", self._generate_summary)
        
        # Definir flujo secuencial (la paralelización se hace dentro de search_all)
        workflow.set_entry_point("parse_profile")
        workflow.add_edge("parse_profile", "search_all")
        workflow.add_edge("search_all", "extract_emails")
        workflow.add_edge("extract_emails", "match_jobs")
        workflow.add_edge("match_jobs", "generate_summary")
        workflow.add_edge("generate_summary", END)
        
        return workflow.compile()
    
    async def _search_all_parallel(self, state: JobSearchState) -> JobSearchState:
        """Busca trabajos en ambas regiones en paralelo (hispanos y angloparlantes)."""
        progress_logger = get_progress_logger()
        progress_logger.print_info("Iniciando búsqueda en todas las fuentes...")
        
        keywords = state.get('keywords', [])
        
        # Iniciar barra de progreso
        progress = progress_logger.start_progress()
        phase_task = progress.add_task("[cyan]Buscando trabajos en paralelo...", total=2)
        
        # Buscar en ambas regiones en paralelo
        progress.update(phase_task, description="[cyan]Buscando en países hispanos y angloparlantes en paralelo...", completed=0)
        
        hispanic_task = self._search_by_region("hispanic", keywords)
        english_task = self._search_by_region("english", keywords)
        
        # Ejecutar ambas búsquedas simultáneamente
        hispanic_jobs, english_jobs = await asyncio.gather(
            hispanic_task,
            english_task,
            return_exceptions=True
        )
        
        # Manejar excepciones
        if isinstance(hispanic_jobs, Exception):
            progress_logger.print_error(f"Error en búsqueda hispana: {hispanic_jobs}")
            hispanic_jobs = []
        if isinstance(english_jobs, Exception):
            progress_logger.print_error(f"Error en búsqueda angloparlante: {english_jobs}")
            english_jobs = []
        
        all_jobs = list(hispanic_jobs) + list(english_jobs)
        
        progress.update(phase_task, advance=2, description=f"[green]Búsqueda completada: {len(hispanic_jobs)} hispanos + {len(english_jobs)} angloparlantes")
        progress_logger.stop_progress()
        
        state['jobs'] = all_jobs
        progress_logger.print_success(
            f"Total: {len(all_jobs)} trabajos (🇪🇸 {len(hispanic_jobs)} | 🇬🇧 {len(english_jobs)})"
        )
        
        return state
    
    async def _search_by_region(self, region_type: str, keywords: List[str]) -> List[Dict]:
        """Busca trabajos en una región específica (hispanic o english)."""
        progress_logger = get_progress_logger()
        region_config = self.config.get('search_regions', {})
        countries = region_config.get(f"{region_type}_countries", [])
        
        if not countries:
            progress_logger.print_warning(f"No hay países configurados para región {region_type}")
            return []
        
        all_jobs = []
        tasks = []
        source_names = []
        
        # Ejecutar búsquedas en paralelo para todas las fuentes
        if self.config.get('job_sources', {}).get('linkedin', {}).get('enabled', True):
            tasks.append(self.linkedin_agent.search(keywords, countries=countries))
            source_names.append("LinkedIn")
        
        # Indeed deshabilitado: difícil acceso, bloqueos frecuentes
        # if self.config.get('job_sources', {}).get('indeed', {}).get('enabled', True):
        #     tasks.append(self.indeed_agent.search(keywords, countries=countries))
        
        if self.config.get('job_sources', {}).get('remoteok', {}).get('enabled', True):
            tasks.append(self.remote_agent.search(keywords, region_type=region_type))
            source_names.append("RemoteOK")
        
        if self.config.get('job_sources', {}).get('stack_overflow', {}).get('enabled', True):
            tasks.append(self.tech_agent.search(keywords, region_type=region_type))
            source_names.append("Stack Overflow")
        
        if self.config.get('job_sources', {}).get('findjobit', {}).get('enabled', True):
            tasks.append(self.findjobit_agent.search(keywords, region_type=region_type))
            source_names.append("Findjobit")
        
        # Ejecutar todas las tareas en paralelo con barra de progreso
        if tasks:
            progress = progress_logger.start_progress()
            search_task = progress.add_task(
                f"[cyan]Buscando en {len(source_names)} fuentes ({', '.join(source_names)})...",
                total=len(tasks)
            )
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                progress.update(search_task, advance=1, description=f"[green]✓ {source_names[i] if i < len(source_names) else 'Fuente'}")
                
                if isinstance(result, Exception):
                    progress_logger.print_error(f"Error en {source_names[i] if i < len(source_names) else 'fuente'}: {result}")
                elif isinstance(result, list):
                    # Marcar trabajos con metadata de región
                    for job in result:
                        job['search_region'] = region_type
                        job['region_priority'] = 1 if region_type == "hispanic" else 2
                    all_jobs.extend(result)
            
            progress_logger.stop_progress()
        
        return all_jobs
    
    def _parse_profile(self, state: JobSearchState) -> JobSearchState:
        """Parsea el CV y extrae el perfil."""
        progress_logger = get_progress_logger()
        progress_logger.print_info("Parseando perfil del CV...")
        try:
            profile = self.cv_parser.parse()
            keywords = self.config.get('keywords', [])
            
            state['profile'] = profile
            state['keywords'] = keywords
            state['jobs'] = []
            state['errors'] = []
            
            progress_logger.print_success(f"Perfil parseado. Keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
        except CVParseError as e:
            progress_logger.print_error(f"Error parseando perfil: {e}")
            logger.error(f"Error parseando perfil: {e}")
            state['errors'].append(f"Error parseando perfil: {str(e)}")
        except (FileNotFoundError, IOError) as e:
            progress_logger.print_error(f"Error leyendo archivo CV: {e}")
            logger.error(f"Error leyendo archivo CV: {e}")
            state['errors'].append(f"Error leyendo CV: {str(e)}")
        except Exception as e:
            progress_logger.print_error(f"Error inesperado parseando perfil: {e}")
            logger.error(f"Error inesperado parseando perfil: {e}")
            state['errors'].append(f"Error parseando perfil: {str(e)}")
        
        return state
    
    async def _search_linkedin(self, state: JobSearchState) -> JobSearchState:
        """Busca trabajos en LinkedIn."""
        if not self.config.get('job_sources', {}).get('linkedin', {}).get('enabled', True):
            return state
        
        logger.info("Buscando en LinkedIn...")
        try:
            keywords = state.get('keywords', [])
            jobs = await self.linkedin_agent.search(keywords)
            state['jobs'].extend(jobs)
            logger.info(f"Encontrados {len(jobs)} trabajos en LinkedIn")
        except ScrapingError as e:
            logger.error(f"Error de scraping en LinkedIn: {e}")
            state['errors'].append(f"Error LinkedIn (scraping): {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado buscando en LinkedIn: {e}")
            state['errors'].append(f"Error LinkedIn: {str(e)}")
        
        return state
    
    # Indeed deshabilitado: difícil acceso, bloqueos frecuentes
    # async def _search_indeed(self, state: JobSearchState) -> JobSearchState:
    #     """Busca trabajos en Indeed."""
    #     if not self.config.get('job_sources', {}).get('indeed', {}).get('enabled', True):
    #         return state
    #     
    #     logger.info("Buscando en Indeed...")
    #     try:
    #         keywords = state.get('keywords', [])
    #         jobs = await self.indeed_agent.search(keywords)
    #         state['jobs'].extend(jobs)
    #         logger.info(f"Encontrados {len(jobs)} trabajos en Indeed")
    #     except Exception as e:
    #         logger.error(f"Error buscando en Indeed: {e}")
    #         state['errors'].append(f"Error Indeed: {str(e)}")
    #     
    #     return state
    
    async def _search_remote(self, state: JobSearchState) -> JobSearchState:
        """Busca trabajos remotos."""
        if not self.config.get('job_sources', {}).get('remoteok', {}).get('enabled', True):
            return state
        
        logger.info("Buscando trabajos remotos...")
        try:
            keywords = state.get('keywords', [])
            jobs = await self.remote_agent.search(keywords)
            state['jobs'].extend(jobs)
            logger.info(f"Encontrados {len(jobs)} trabajos remotos")
        except Exception as e:
            logger.error(f"Error buscando trabajos remotos: {e}")
            state['errors'].append(f"Error Remote Jobs: {str(e)}")
        
        return state
    
    async def _search_tech(self, state: JobSearchState) -> JobSearchState:
        """Busca trabajos técnicos."""
        if not self.config.get('job_sources', {}).get('stack_overflow', {}).get('enabled', True):
            return state
        
        logger.info("Buscando trabajos técnicos...")
        try:
            keywords = state.get('keywords', [])
            jobs = await self.tech_agent.search(keywords)
            state['jobs'].extend(jobs)
            logger.info(f"Encontrados {len(jobs)} trabajos técnicos")
        except Exception as e:
            logger.error(f"Error buscando trabajos técnicos: {e}")
            state['errors'].append(f"Error Tech Jobs: {str(e)}")
        
        return state
    
    async def _extract_emails(self, state: JobSearchState) -> JobSearchState:
        """Extrae emails de los trabajos encontrados (versión async paralela)."""
        progress_logger = get_progress_logger()
        jobs = state.get('jobs', [])
        
        if not jobs:
            return state
        
        progress_logger.print_info(f"Extrayendo emails de {len(jobs)} trabajos en paralelo...")
        try:
            progress = progress_logger.start_progress()
            email_task = progress.add_task("[cyan]Extrayendo emails con LLM (paralelo)...", total=len(jobs))
            
            # Usar el método async paralelo
            enriched_jobs = await self.email_extractor.extract_from_jobs(jobs)
            
            # Recopilar todos los emails únicos
            all_emails = set()
            for job in enriched_jobs:
                emails = job.get('emails', [])
                all_emails.update(emails)
            
            progress.update(email_task, completed=len(jobs), description=f"[green]✓ {len(jobs)} trabajos procesados")
            progress_logger.stop_progress()
            
            state['jobs'] = enriched_jobs
            state['emails'] = list(all_emails)
            progress_logger.print_success(f"Extraídos {len(all_emails)} emails únicos")
        except LLMError as e:
            progress_logger.print_error(f"Error LLM extrayendo emails: {e}")
            logger.error(f"Error LLM extrayendo emails: {e}")
            state['errors'].append(f"Error LLM en extracción de emails: {str(e)}")
        except Exception as e:
            progress_logger.print_error(f"Error inesperado extrayendo emails: {e}")
            logger.error(f"Error inesperado extrayendo emails: {e}")
            state['errors'].append(f"Error extrayendo emails: {str(e)}")
        
        return state
    
    def _match_jobs(self, state: JobSearchState) -> JobSearchState:
        """Matchea trabajos con el perfil."""
        progress_logger = get_progress_logger()
        jobs = state.get('jobs', [])
        
        if not jobs:
            state['matched_jobs'] = []
            return state
        
        progress_logger.print_info(f"Matcheando {len(jobs)} trabajos con perfil...")
        try:
            progress = progress_logger.start_progress()
            match_task = progress.add_task("[cyan]Calculando scores de match...", total=len(jobs))
            
            matched_jobs = self.matcher.match_jobs(jobs)
            
            progress_logger.stop_progress()
            
            state['matched_jobs'] = matched_jobs
            progress_logger.print_success(f"Matcheados {len(matched_jobs)} trabajos")
        except Exception as e:
            progress_logger.print_error(f"Error matcheando trabajos: {e}")
            logger.error(f"Error matcheando trabajos: {e}")
            state['errors'].append(f"Error matcheando: {str(e)}")
            state['matched_jobs'] = []
        
        return state
    
    def _generate_summary(self, state: JobSearchState) -> JobSearchState:
        """Genera resumen de resultados."""
        progress_logger = get_progress_logger()
        progress_logger.print_info("Generando resumen de resultados...")
        try:
            matched_jobs = state.get('matched_jobs', [])
            summary = self.matcher.get_match_summary(matched_jobs)
            
            # Agregar estadísticas por fuente
            by_source = {}
            for job in matched_jobs:
                source = job.get('source', 'unknown')
                by_source[source] = by_source.get(source, 0) + 1
            
            summary['by_source'] = by_source
            summary['total_emails'] = len(state.get('emails', []))
            
            state['summary'] = summary
            logger.info(f"Resumen generado: {summary}")
        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
            state['errors'].append(f"Error generando resumen: {str(e)}")
            state['summary'] = {}
        
        return state
    
    async def run(self) -> Dict:
        """Ejecuta el workflow completo."""
        logger.info("Iniciando búsqueda de empleo...")
        
        initial_state: JobSearchState = {
            'profile': {},
            'keywords': [],
            'jobs': [],
            'matched_jobs': [],
            'emails': [],
            'summary': {},
            'errors': []
        }
        
        try:
            # Ejecutar el grafo
            final_state = await self.graph.ainvoke(initial_state)
            
            logger.info("Búsqueda completada")
            return final_state
            
        except Exception as e:
            logger.error(f"Error ejecutando workflow: {e}")
            initial_state['errors'].append(f"Error en workflow: {str(e)}")
            return initial_state
