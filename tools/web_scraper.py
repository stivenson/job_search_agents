"""Herramientas de web scraping para job boards."""

import asyncio
import time
import logging
import random
from typing import List, Dict, Optional
from urllib.parse import urlencode, urljoin, urlparse
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    SCRAPING_DELAY, MAX_RETRIES, HEADLESS_BROWSER,
    USE_USER_AGENT_ROTATION, RANDOM_DELAY_ENABLED, MIN_DELAY, MAX_DELAY,
    ENABLE_BROWSER_STEALTH, SIMULATE_HUMAN_BEHAVIOR,
    USE_CIRCUIT_BREAKER, CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT,
    USE_SESSION_PERSISTENCE, USE_ADAPTIVE_RATE_LIMITING,
    USE_REFERER_HEADERS, USE_FINGERPRINT_CONSISTENCY,
    USE_SESSION_WARMUP, USE_TLS_FINGERPRINT_BYPASS, FAST_MODE
)
from utils.user_agent_rotator import UserAgentRotator
from utils.delay_manager import DelayManager
from utils.session_manager import SessionManager
from utils.circuit_breaker import CircuitBreaker
from utils.referer_manager import RefererManager
from utils.fingerprint_manager import FingerprintManager
from utils.adaptive_rate_limiter import AdaptiveRateLimiter
from utils.session_warmup import SessionWarmup
from utils.exceptions import ScrapingError, RateLimitError
from tools.http_client_strategy import HTTPClientStrategy, RequestsClientStrategy, TLSClientStrategy

logger = logging.getLogger(__name__)


class WebScraper:
    """Clase base para web scraping de job boards con técnicas anti-detección avanzadas."""
    
    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        fingerprint_manager: Optional[FingerprintManager] = None,
        rate_limiter: Optional[AdaptiveRateLimiter] = None
    ):
        """
        Inicializa WebScraper con inyección de dependencias (SOLID: Dependency Inversion).
        
        Args:
            circuit_breaker: Circuit breaker para detectar bloqueos (opcional)
            fingerprint_manager: Gestor de fingerprint (opcional)
            rate_limiter: Rate limiter adaptativo (opcional)
        """
        self.delay = SCRAPING_DELAY
        self.max_retries = MAX_RETRIES
        self.headless = HEADLESS_BROWSER
        self.browser: Optional[Browser] = None
        
        # Inyección de dependencias
        self.circuit_breaker = circuit_breaker if USE_CIRCUIT_BREAKER else None
        if not self.circuit_breaker and USE_CIRCUIT_BREAKER:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=CIRCUIT_BREAKER_THRESHOLD,
                timeout_seconds=CIRCUIT_BREAKER_TIMEOUT
            )
        
        self.fingerprint_manager = fingerprint_manager if USE_FINGERPRINT_CONSISTENCY else None
        if not self.fingerprint_manager and USE_FINGERPRINT_CONSISTENCY:
            self.fingerprint_manager = FingerprintManager()
        
        self.rate_limiter = rate_limiter if USE_ADAPTIVE_RATE_LIMITING else None
        if not self.rate_limiter and USE_ADAPTIVE_RATE_LIMITING:
            self.rate_limiter = AdaptiveRateLimiter()
        
        # Mantener compatibilidad
        self.ua_rotator = UserAgentRotator() if USE_USER_AGENT_ROTATION else None
        self.delay_manager = DelayManager(MIN_DELAY, MAX_DELAY) if RANDOM_DELAY_ENABLED else None
        
    async def __aenter__(self):
        """Context manager entry con configuración anti-detección."""
        self.playwright = await async_playwright().start()
        
        # Configuración anti-detección para Playwright
        launch_args = []
        if ENABLE_BROWSER_STEALTH:
            launch_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-infobars',
                '--disable-blink-features=AutomationControlled'
            ]
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()
    
    async def _simulate_human_behavior(self, page: Page):
        """Simula comportamiento humano en la página para evitar detección."""
        if not SIMULATE_HUMAN_BEHAVIOR:
            return
        
        try:
            # Ajustar delays según FAST_MODE
            if FAST_MODE:
                scroll_delay = random.uniform(0.2, 0.5)
                mouse_delay = random.uniform(0.1, 0.3)
                additional_delay = random.uniform(0.1, 0.3)
            else:
                scroll_delay = random.uniform(0.5, 1.5)
                mouse_delay = random.uniform(0.2, 0.8)
                additional_delay = random.uniform(0.3, 1.0)
            
            # Scroll aleatorio suave
            scroll_amount = random.randint(200, 800)
            await page.evaluate(f"""
                window.scrollTo({{
                    top: {scroll_amount},
                    behavior: 'smooth'
                }});
            """)
            await asyncio.sleep(scroll_delay)
            
            # Movimiento de mouse aleatorio
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
            await asyncio.sleep(mouse_delay)
            
            # Scroll adicional aleatorio
            if random.random() > 0.5:
                await page.evaluate("""
                    window.scrollBy({
                        top: Math.random() * 500 - 250,
                        behavior: 'smooth'
                    });
                """)
                await asyncio.sleep(additional_delay)
        except Exception as e:
            logger.debug(f"Error en simulación de comportamiento humano: {e}")
    
    def _get_domain(self, url: str) -> str:
        """Extrae dominio de una URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '').lower()
        except Exception:
            return 'unknown'
    
    async def fetch_page(self, url: str, wait_selector: Optional[str] = None) -> str:
        """
        Obtiene el contenido HTML de una página con técnicas anti-detección avanzadas.
        
        Integra:
        - Circuit Breaker para detectar bloqueos persistentes
        - Fingerprint Manager para consistencia
        - Adaptive Rate Limiter para delays adaptativos
        - Scripts de stealth mejorados
        - Viewport consistente con fingerprint
        """
        if not self.browser:
            raise RuntimeError("Browser no inicializado. Usa 'async with WebScraper()'")
        
        domain = self._get_domain(url)
        start_time = time.time()
        
        # Verificar Circuit Breaker
        if self.circuit_breaker and self.circuit_breaker.is_open(domain):
            logger.warning(f"Circuit breaker OPEN para {domain}, saltando request")
            raise Exception(f"Dominio {domain} está bloqueado temporalmente (Circuit Breaker)")
        
        for attempt in range(self.max_retries):
            try:
                page = await self.browser.new_page()
                
                # Obtener fingerprint consistente
                if self.fingerprint_manager:
                    fingerprint = self.fingerprint_manager.get_current_fingerprint()
                    
                    # Configurar viewport consistente con fingerprint
                    viewport = fingerprint['viewport']
                    await page.set_viewport_size({"width": viewport['width'], "height": viewport['height']})
                    
                    # Headers basados en fingerprint
                    if self.ua_rotator:
                        headers = self.ua_rotator.get_realistic_headers(fingerprint['user_agent'])
                    else:
                        headers = {'User-Agent': fingerprint['user_agent']}
                    
                    await page.set_extra_http_headers(headers)
                elif self.ua_rotator:
                    headers = self.ua_rotator.get_realistic_headers()
                    await page.set_extra_http_headers(headers)
                
                # Scripts de stealth mejorados
                if ENABLE_BROWSER_STEALTH:
                    await page.add_init_script("""
                        // Ocultar propiedades de automatización
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        
                        // Simular plugins
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        
                        // Simular languages
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['es-ES', 'es', 'en-US', 'en']
                        });
                        
                        // Ocultar Chrome automation
                        window.navigator.chrome = {
                            runtime: {},
                            loadTimes: function() {},
                            csi: function() {},
                            app: {}
                        };
                        
                        // Simular permisos
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                        
                        // Ocultar propiedad automation
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => false
                        });
                        
                        // Simular hardwareConcurrency
                        Object.defineProperty(navigator, 'hardwareConcurrency', {
                            get: () => 8
                        });
                        
                        // Simular deviceMemory
                        Object.defineProperty(navigator, 'deviceMemory', {
                            get: () => 8
                        });
                    """)
                
                # Navegar a la URL
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Simular comportamiento humano antes de esperar selector
                if SIMULATE_HUMAN_BEHAVIOR:
                    await self._simulate_human_behavior(page)
                
                # Esperar selector específico si se proporciona
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                
                # Esperar un poco más para que cargue JavaScript (reducido en FAST_MODE)
                if FAST_MODE:
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                else:
                    await asyncio.sleep(random.uniform(1.5, 3.0))
                
                # Obtener HTML
                content = await page.content()
                await page.close()
                
                response_time = time.time() - start_time
                
                # Registrar éxito en Circuit Breaker y Rate Limiter
                if self.circuit_breaker:
                    self.circuit_breaker.record_success(domain)
                if self.rate_limiter:
                    self.rate_limiter.record_response(domain, 200, response_time)
                
                # Delay adaptativo entre requests
                if self.rate_limiter:
                    delay = self.rate_limiter.get_delay(domain)
                    await asyncio.sleep(delay)
                elif self.delay_manager:
                    await self.delay_manager.wait()
                else:
                    await asyncio.sleep(self.delay)
                
                return content
                
            except Exception as e:
                response_time = time.time() - start_time
                
                # Registrar fallo
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure(domain)
                if self.rate_limiter:
                    self.rate_limiter.record_response(domain, 0, response_time)  # 0 = error desconocido
                
                logger.warning(f"Intento {attempt + 1} fallido para {url}: {e}")
                if attempt < self.max_retries - 1:
                    # Rotar User-Agent y fingerprint en caso de error
                    if self.ua_rotator:
                        self.ua_rotator.rotate()
                    if self.fingerprint_manager:
                        self.fingerprint_manager.reset_fingerprint()
                    # Backoff exponencial con jitter
                    backoff_delay = self.delay * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.error(f"Error al obtener {url} después de {self.max_retries} intentos")
                    raise
        
        return ""
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parsea HTML con BeautifulSoup."""
        return BeautifulSoup(html, 'html.parser')
    
    def extract_text(self, element, default: str = "") -> str:
        """Extrae texto de un elemento BeautifulSoup."""
        if element:
            return element.get_text(strip=True)
        return default
    
    def build_search_url(self, base_url: str, params: Dict) -> str:
        """Construye URL de búsqueda con parámetros."""
        return f"{base_url}?{urlencode(params)}"


class SimpleHTTPScraper:
    """Scraper simple usando requests (sin JavaScript) con técnicas anti-detección avanzadas."""
    
    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        referer_manager: Optional[RefererManager] = None,
        fingerprint_manager: Optional[FingerprintManager] = None,
        rate_limiter: Optional[AdaptiveRateLimiter] = None,
        http_client_strategy: Optional[HTTPClientStrategy] = None
    ):
        """
        Inicializa SimpleHTTPScraper con inyección de dependencias (SOLID: Dependency Inversion).
        
        Args:
            session_manager: Gestor de sesiones/cookies (opcional)
            circuit_breaker: Circuit breaker para detectar bloqueos (opcional)
            referer_manager: Gestor de referers (opcional)
            fingerprint_manager: Gestor de fingerprint (opcional)
            rate_limiter: Rate limiter adaptativo (opcional)
            http_client_strategy: Estrategia de HTTP client (opcional)
        """
        self.delay = SCRAPING_DELAY
        self.session = requests.Session()
        
        # Inyección de dependencias (Dependency Inversion)
        self.session_manager = session_manager if USE_SESSION_PERSISTENCE else None
        if not self.session_manager and USE_SESSION_PERSISTENCE:
            self.session_manager = SessionManager()
        
        self.circuit_breaker = circuit_breaker if USE_CIRCUIT_BREAKER else None
        if not self.circuit_breaker and USE_CIRCUIT_BREAKER:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=CIRCUIT_BREAKER_THRESHOLD,
                timeout_seconds=CIRCUIT_BREAKER_TIMEOUT
            )
        
        self.referer_manager = referer_manager if USE_REFERER_HEADERS else None
        if not self.referer_manager and USE_REFERER_HEADERS:
            self.referer_manager = RefererManager()
        
        self.fingerprint_manager = fingerprint_manager if USE_FINGERPRINT_CONSISTENCY else None
        if not self.fingerprint_manager and USE_FINGERPRINT_CONSISTENCY:
            self.fingerprint_manager = FingerprintManager()
        
        self.rate_limiter = rate_limiter if USE_ADAPTIVE_RATE_LIMITING else None
        if not self.rate_limiter and USE_ADAPTIVE_RATE_LIMITING:
            self.rate_limiter = AdaptiveRateLimiter()
        
        # HTTP Client Strategy (SOLID: Dependency Inversion)
        # Usar TLS bypass si está habilitado y disponible, sino usar requests estándar
        if http_client_strategy:
            self.http_client = http_client_strategy
        elif USE_TLS_FINGERPRINT_BYPASS:
            try:
                tls_client = TLSClientStrategy()
                # Si TLSClientStrategy usa curl_cffi, mantenerlo; si no, usar requests con nuestra sesión
                if not tls_client.use_curl:
                    # Fallback a requests, usar nuestra sesión configurada
                    self.http_client = RequestsClientStrategy(self.session)
                else:
                    self.http_client = tls_client
            except Exception as e:
                logger.warning(f"Error inicializando TLSClientStrategy: {e}, usando requests estándar")
                self.http_client = RequestsClientStrategy(self.session)
        else:
            self.http_client = RequestsClientStrategy(self.session)
        
        # Session Warmup (SOLID: Dependency Inversion)
        self.warmup = SessionWarmup(self.http_client) if USE_SESSION_WARMUP else None
        
        # User-Agent y delays (mantener compatibilidad)
        self.ua_rotator = UserAgentRotator() if USE_USER_AGENT_ROTATION else None
        self.delay_manager = DelayManager(MIN_DELAY, MAX_DELAY) if RANDOM_DELAY_ENABLED else None
        
        # Configurar headers iniciales
        if self.fingerprint_manager:
            fingerprint = self.fingerprint_manager.get_current_fingerprint()
            headers = self.ua_rotator.get_realistic_headers(fingerprint['user_agent']) if self.ua_rotator else {}
            self.session.headers.update(headers)
        elif self.ua_rotator:
            self.session.headers.update(self.ua_rotator.get_realistic_headers())
        else:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
    
    def _get_domain(self, url: str) -> str:
        """Extrae dominio de una URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '').lower()
        except Exception:
            return 'unknown'
    
    def fetch(self, url: str, params: Optional[Dict] = None) -> str:
        """
        Obtiene contenido HTML usando requests con técnicas anti-detección avanzadas.
        
        Integra:
        - Circuit Breaker para detectar bloqueos persistentes
        - Session Manager para cookies persistentes
        - Referer Manager para referers realistas
        - Adaptive Rate Limiter para delays adaptativos
        - Fingerprint Manager para consistencia
        """
        domain = self._get_domain(url)
        start_time = time.time()
        
        # Verificar Circuit Breaker
        if self.circuit_breaker and self.circuit_breaker.is_open(domain):
            logger.warning(f"Circuit breaker OPEN para {domain}, saltando request")
            raise Exception(f"Dominio {domain} está bloqueado temporalmente (Circuit Breaker)")
        
        # Warm-up session si es necesario (solo una vez por dominio, antes del loop de retries)
        if self.warmup:
            self.warmup.warm_up(domain)
        
        # Cargar cookies guardadas
        if self.session_manager:
            saved_cookies = self.session_manager.load_cookies(domain)
            if saved_cookies:
                self.session.cookies.update(saved_cookies)
                logger.debug(f"Cookies cargadas para {domain}")
        
        for attempt in range(MAX_RETRIES):
            try:
                # Preparar headers con fingerprint consistente
                headers = {}
                
                if self.fingerprint_manager:
                    fingerprint = self.fingerprint_manager.get_current_fingerprint()
                    if self.ua_rotator:
                        headers = self.ua_rotator.get_realistic_headers(fingerprint['user_agent'])
                    else:
                        headers['User-Agent'] = fingerprint['user_agent']
                elif self.ua_rotator and attempt == 0:
                    headers = self.ua_rotator.get_realistic_headers()
                
                # Agregar referer realista
                if self.referer_manager:
                    referer = self.referer_manager.get_referer(url)
                    if referer:
                        headers['Referer'] = referer
                
                # Actualizar headers de sesión
                if headers:
                    self.session.headers.update(headers)
                
                # Ejecutar request usando estrategia HTTP (SOLID: Dependency Inversion)
                response = self.http_client.get(url, params=params, headers=headers, timeout=30)
                response_time = time.time() - start_time
                
                # Registrar respuesta en Adaptive Rate Limiter
                if self.rate_limiter:
                    self.rate_limiter.record_response(domain, response.status_code, response_time)
                
                response.raise_for_status()
                
                # Guardar cookies si hay respuesta exitosa
                if self.session_manager and response.cookies:
                    self.session_manager.update_cookies_from_response(domain, response.cookies)
                
                # Registrar éxito en Circuit Breaker
                if self.circuit_breaker:
                    self.circuit_breaker.record_success(domain)
                
                # Delay adaptativo después del request exitoso
                if self.rate_limiter:
                    delay = self.rate_limiter.get_delay(domain)
                    time.sleep(delay)
                elif self.delay_manager:
                    self.delay_manager.wait_sync()
                else:
                    time.sleep(self.delay)
                
                return response.text
                
            except requests.exceptions.HTTPError as e:
                response_time = time.time() - start_time
                
                # Registrar respuesta en Adaptive Rate Limiter
                if self.rate_limiter and e.response:
                    self.rate_limiter.record_response(domain, e.response.status_code, response_time)
                
                if e.response and e.response.status_code in [403, 429]:
                    # Registrar fallo en Circuit Breaker
                    if self.circuit_breaker:
                        self.circuit_breaker.record_failure(domain)
                    
                    # Si es bloqueo, rotar User-Agent y fingerprint
                    if self.ua_rotator:
                        self.ua_rotator.rotate()
                    if self.fingerprint_manager:
                        self.fingerprint_manager.reset_fingerprint()
                        fingerprint = self.fingerprint_manager.get_current_fingerprint()
                        headers = self.ua_rotator.get_realistic_headers(fingerprint['user_agent']) if self.ua_rotator else {}
                        self.session.headers.update(headers)
                    
                    logger.warning(f"Bloqueo detectado (403/429) para {url}, rotando User-Agent y fingerprint...")
                
                logger.warning(f"Intento {attempt + 1} fallido para {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    # Backoff exponencial con jitter
                    backoff_delay = self.delay * (2 ** attempt) + random.uniform(0, 2)
                    time.sleep(backoff_delay)
                else:
                    logger.error(f"Error al obtener {url}")
                    raise
            except Exception as e:
                response_time = time.time() - start_time
                
                # Registrar fallo genérico
                if self.rate_limiter:
                    self.rate_limiter.record_response(domain, 0, response_time)  # 0 = error desconocido
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure(domain)
                
                logger.warning(f"Intento {attempt + 1} fallido para {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    backoff_delay = self.delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(backoff_delay)
                else:
                    logger.error(f"Error al obtener {url}")
                    raise
        
        return ""
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parsea HTML con BeautifulSoup."""
        return BeautifulSoup(html, 'html.parser')


async def scrape_linkedin_jobs(keywords: List[str], max_results: int = 50, location: Optional[str] = None) -> List[Dict]:
    """Scraping básico de LinkedIn Jobs con filtro de ubicación opcional."""
    # Nota: LinkedIn tiene protección anti-scraping fuerte
    # Esta es una implementación básica que puede necesitar mejoras
    jobs = []
    
    async with WebScraper() as scraper:
        for keyword in keywords[:3]:  # Limitar keywords para evitar rate limiting
            try:
                # Construir URL de búsqueda de LinkedIn Jobs con ubicación opcional
                if location:
                    # URLencode location para URL
                    from urllib.parse import quote
                    location_encoded = quote(location)
                    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location_encoded}&f_TPR=r86400&f_JT=P&f_WT=2"
                else:
                    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&f_TPR=r86400&f_JT=P&f_WT=2"
                
                html = await scraper.fetch_page(search_url, wait_selector=".jobs-search__results-list")
                soup = scraper.parse_html(html)
                
                # Buscar elementos de trabajo (selectores pueden cambiar)
                job_cards = soup.select(".job-search-card, .base-card")
                
                for card in job_cards[:max_results // len(keywords)]:
                    try:
                        title_elem = card.select_one(".base-search-card__title, h3")
                        company_elem = card.select_one(".base-search-card__subtitle, h4")
                        location_elem = card.select_one(".job-search-card__location")
                        link_elem = card.select_one("a")
                        
                        if title_elem:
                            job = {
                                'title': scraper.extract_text(title_elem),
                                'company': scraper.extract_text(company_elem),
                                'location': scraper.extract_text(location_elem),
                                'url': link_elem.get('href', '') if link_elem else '',
                                'source': 'linkedin',
                                'keywords': [keyword]
                            }
                            if job['url']:
                                jobs.append(job)
                    except Exception as e:
                        logger.warning(f"Error procesando card de LinkedIn: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error scraping LinkedIn para keyword {keyword}: {e}")
                continue
    
    return jobs


async def scrape_indeed_jobs(keywords: List[str], max_results: int = 50, location: Optional[str] = None) -> List[Dict]:
    """Scraping de Indeed Jobs con filtro de ubicación opcional."""
    jobs = []
    scraper = SimpleHTTPScraper()
    
    for keyword in keywords[:3]:
        try:
            params = {
                'q': keyword,
                'l': location or 'remote',  # Usar location si se proporciona, sino 'remote'
                'jt': 'parttime',
                'limit': 25
            }
            
            url = "https://www.indeed.com/jobs"
            html = scraper.fetch(url, params=params)
            soup = scraper.parse_html(html)
            
            # Buscar cards de trabajo
            job_cards = soup.select(".job_seen_beacon, .slider_container")
            
            for card in job_cards[:max_results // len(keywords)]:
                try:
                    title_elem = card.select_one("h2.jobTitle a, .jobTitle")
                    company_elem = card.select_one(".companyName")
                    location_elem = card.select_one(".companyLocation")
                    
                    if title_elem:
                        job = {
                            'title': scraper.extract_text(title_elem),
                            'company': scraper.extract_text(company_elem),
                            'location': scraper.extract_text(location_elem),
                            'url': urljoin("https://www.indeed.com", title_elem.get('href', '')),
                            'source': 'indeed',
                            'keywords': [keyword]
                        }
                        if job['url']:
                            jobs.append(job)
                except Exception as e:
                    logger.warning(f"Error procesando card de Indeed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Indeed para keyword {keyword}: {e}")
            continue
    
    return jobs


async def scrape_we_work_remotely(max_results: int = 50) -> List[Dict]:
    """Scraping de We Work Remotely."""
    jobs = []
    
    async with WebScraper() as scraper:
        try:
            url = "https://weworkremotely.com/categories/remote-programming-jobs"
            html = await scraper.fetch_page(url, wait_selector=".jobs")
            soup = scraper.parse_html(html)
            
            job_cards = soup.select(".job-listing")
            
            for card in job_cards[:max_results]:
                try:
                    title_elem = card.select_one(".title")
                    company_elem = card.select_one(".company")
                    link_elem = card.select_one("a")
                    
                    if title_elem and link_elem:
                        job = {
                            'title': scraper.extract_text(title_elem),
                            'company': scraper.extract_text(company_elem),
                            'location': 'Remote',
                            'url': urljoin("https://weworkremotely.com", link_elem.get('href', '')),
                            'source': 'we_work_remotely',
                            'keywords': []
                        }
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"Error procesando card de We Work Remotely: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping We Work Remotely: {e}")
    
    return jobs
