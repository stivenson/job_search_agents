"""Configuración del sistema de búsqueda de empleo."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent.parent

# Paths configurables mediante variables de entorno
CV_PATH_ENV = os.getenv("CV_PATH")
if CV_PATH_ENV:
    CV_PATH = Path(CV_PATH_ENV)
else:
    CV_PATH = BASE_DIR / "CVs_Principales" / "CV_Dev_Senior_AI_Improvement.md"

OUTPUT_DIR_ENV = os.getenv("OUTPUT_DIR")
if OUTPUT_DIR_ENV:
    OUTPUT_DIR = Path(OUTPUT_DIR_ENV)
else:
    OUTPUT_DIR = BASE_DIR / "job_search_agents" / "results"

DATA_DIR_ENV = os.getenv("DATA_DIR")
if DATA_DIR_ENV:
    DATA_DIR = Path(DATA_DIR_ENV)
else:
    DATA_DIR = BASE_DIR / "job_search_agents" / "data"

# Crear directorios si no existen
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "anthropic"
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Default to cost-effective model

# Validar que la API key correspondiente al proveedor esté configurada
if LLM_PROVIDER.lower() == "anthropic" and not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY environment variable is required when LLM_PROVIDER=anthropic. "
        "Please set it in your .env file or environment variables."
    )
elif LLM_PROVIDER.lower() == "openai" and not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY environment variable is required when LLM_PROVIDER=openai. "
        "Please set it in your .env file or environment variables."
    )

# Job Board API Keys (opcionales)
LINKEDIN_API_KEY: Optional[str] = os.getenv("LINKEDIN_API_KEY")
INDEED_API_KEY: Optional[str] = os.getenv("INDEED_API_KEY")
REMOTEOK_API_KEY: Optional[str] = os.getenv("REMOTEOK_API_KEY")

# Search Configuration
MAX_JOBS_PER_SOURCE: int = int(os.getenv("MAX_JOBS_PER_SOURCE", "50"))
MIN_MATCH_SCORE: int = int(os.getenv("MIN_MATCH_SCORE", "60"))
SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "30"))  # segundos

# Scraping Configuration
SCRAPING_DELAY: float = float(os.getenv("SCRAPING_DELAY", "2.0"))  # segundos entre requests
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"

# Anti-Bot Configuration
USE_USER_AGENT_ROTATION: bool = os.getenv("USE_USER_AGENT_ROTATION", "true").lower() == "true"
RANDOM_DELAY_ENABLED: bool = os.getenv("RANDOM_DELAY_ENABLED", "true").lower() == "true"
MIN_DELAY: float = float(os.getenv("MIN_DELAY", "1.5"))  # Delay mínimo en segundos
MAX_DELAY: float = float(os.getenv("MAX_DELAY", "4.0"))  # Delay máximo en segundos
USE_PROXIES: bool = os.getenv("USE_PROXIES", "false").lower() == "true"
PROXY_LIST: Optional[str] = os.getenv("PROXY_LIST")  # Lista de proxies separados por coma
ENABLE_BROWSER_STEALTH: bool = os.getenv("ENABLE_BROWSER_STEALTH", "true").lower() == "true"
SIMULATE_HUMAN_BEHAVIOR: bool = os.getenv("SIMULATE_HUMAN_BEHAVIOR", "true").lower() == "true"

# Advanced Anti-Bot Configuration
USE_CIRCUIT_BREAKER: bool = os.getenv("USE_CIRCUIT_BREAKER", "true").lower() == "true"
CIRCUIT_BREAKER_THRESHOLD: int = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
CIRCUIT_BREAKER_TIMEOUT: int = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "300"))  # segundos
USE_SESSION_PERSISTENCE: bool = os.getenv("USE_SESSION_PERSISTENCE", "true").lower() == "true"
USE_ADAPTIVE_RATE_LIMITING: bool = os.getenv("USE_ADAPTIVE_RATE_LIMITING", "true").lower() == "true"
USE_TLS_FINGERPRINT_BYPASS: bool = os.getenv("USE_TLS_FINGERPRINT_BYPASS", "false").lower() == "true"  # Requiere curl_cffi
USE_REFERER_HEADERS: bool = os.getenv("USE_REFERER_HEADERS", "true").lower() == "true"
USE_FINGERPRINT_CONSISTENCY: bool = os.getenv("USE_FINGERPRINT_CONSISTENCY", "true").lower() == "true"
USE_SESSION_WARMUP: bool = os.getenv("USE_SESSION_WARMUP", "true").lower() == "true"  # Warm-up de sesión antes de scraping
USE_QUERY_VARIATIONS: bool = os.getenv("USE_QUERY_VARIATIONS", "true").lower() == "true"  # Generar variaciones de queries con LLM

# LLM-Enhanced Search Features
USE_ADAPTIVE_KEYWORDS: bool = os.getenv("USE_ADAPTIVE_KEYWORDS", "true").lower() == "true"  # Generar keywords adaptativos por fuente/región con LLM
USE_SEMANTIC_MATCHING: bool = os.getenv("USE_SEMANTIC_MATCHING", "true").lower() == "true"  # Análisis semántico profundo de relevancia
SEMANTIC_MATCHING_THRESHOLD: int = int(os.getenv("SEMANTIC_MATCHING_THRESHOLD", "50"))  # Score mínimo para análisis semántico
SEMANTIC_MAX_JOBS: int = int(os.getenv("SEMANTIC_MAX_JOBS", "100"))  # Máximo de trabajos a analizar semánticamente
SEMANTIC_WEIGHT: float = float(os.getenv("SEMANTIC_WEIGHT", "0.6"))  # Peso del score semántico en score final (0-1)
HEURISTIC_WEIGHT: float = float(os.getenv("HEURISTIC_WEIGHT", "0.4"))  # Peso del score heurístico en score final (0-1)

# User Profile (REQUIRED - no default values for privacy)
USER_EMAIL: Optional[str] = os.getenv("USER_EMAIL")
USER_PHONE: Optional[str] = os.getenv("USER_PHONE")

# Validar que las variables obligatorias estén configuradas
if not USER_EMAIL:
    raise ValueError(
        "USER_EMAIL environment variable is required. "
        "Please set it in your .env file or environment variables."
    )
if not USER_PHONE:
    raise ValueError(
        "USER_PHONE environment variable is required. "
        "Please set it in your .env file or environment variables."
    )

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: Optional[str] = os.getenv("LOG_FILE")

# Cache Configuration
USE_CACHE: bool = os.getenv("USE_CACHE", "true").lower() == "true"
CACHE_EXPIRY_HOURS: int = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))

# Performance Optimization Configuration
FAST_MODE: bool = os.getenv("FAST_MODE", "false").lower() == "true"
EMAIL_EXTRACTION_CONCURRENCY: int = int(os.getenv("EMAIL_EXTRACTION_CONCURRENCY", "10"))
EMAIL_BATCH_SIZE: int = int(os.getenv("EMAIL_BATCH_SIZE", "5"))

# Timeouts (milliseconds for browser, seconds for requests)
PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "30000"))  # milliseconds
SELECTOR_TIMEOUT: int = int(os.getenv("SELECTOR_TIMEOUT", "10000"))  # milliseconds
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds

# Truncation limits
DESCRIPTION_MAX_LENGTH: int = int(os.getenv("DESCRIPTION_MAX_LENGTH", "2000"))
TITLE_DISPLAY_LENGTH: int = int(os.getenv("TITLE_DISPLAY_LENGTH", "50"))
COMPANY_DISPLAY_LENGTH: int = int(os.getenv("COMPANY_DISPLAY_LENGTH", "30"))

# Score thresholds
HIGH_SCORE_THRESHOLD: int = int(os.getenv("HIGH_SCORE_THRESHOLD", "80"))
MEDIUM_SCORE_THRESHOLD: int = int(os.getenv("MEDIUM_SCORE_THRESHOLD", "60"))

# Display limits
MAX_DISPLAY_ITEMS: int = int(os.getenv("MAX_DISPLAY_ITEMS", "10"))
MAX_TOP_JOBS: int = int(os.getenv("MAX_TOP_JOBS", "5"))

# Adjust delays when FAST_MODE is enabled
if FAST_MODE:
    SCRAPING_DELAY = 0.5  # Reduced from 2.0s
    MIN_DELAY = 0.3  # Reduced from 1.5s
    MAX_DELAY = 1.0  # Reduced from 4.0s
    SIMULATE_HUMAN_BEHAVIOR = False  # Disable by default in fast mode

# Validate LLM-Enhanced Search weights
if not (0 <= SEMANTIC_WEIGHT <= 1):
    raise ValueError(
        f"SEMANTIC_WEIGHT ({SEMANTIC_WEIGHT}) must be between 0 and 1. "
        "Check your .env file or environment variables."
    )

if not (0 <= HEURISTIC_WEIGHT <= 1):
    raise ValueError(
        f"HEURISTIC_WEIGHT ({HEURISTIC_WEIGHT}) must be between 0 and 1. "
        "Check your .env file or environment variables."
    )

if abs((SEMANTIC_WEIGHT + HEURISTIC_WEIGHT) - 1.0) > 0.001:
    raise ValueError(
        f"SEMANTIC_WEIGHT ({SEMANTIC_WEIGHT}) and HEURISTIC_WEIGHT ({HEURISTIC_WEIGHT}) "
        "must sum to 1.0. Check your .env file or environment variables."
    )

# Validate configuration ranges
if MIN_DELAY >= MAX_DELAY:
    raise ValueError(
        f"MIN_DELAY ({MIN_DELAY}) must be less than MAX_DELAY ({MAX_DELAY}). "
        "Check your .env file or environment variables."
    )

if not 0 <= MIN_MATCH_SCORE <= 100:
    raise ValueError(
        f"MIN_MATCH_SCORE ({MIN_MATCH_SCORE}) must be between 0 and 100. "
        "Check your .env file or environment variables."
    )

if SCRAPING_DELAY < 0:
    raise ValueError(
        f"SCRAPING_DELAY ({SCRAPING_DELAY}) must be positive. "
        "Check your .env file or environment variables."
    )

if MAX_JOBS_PER_SOURCE <= 0:
    raise ValueError(
        f"MAX_JOBS_PER_SOURCE ({MAX_JOBS_PER_SOURCE}) must be positive. "
        "Check your .env file or environment variables."
    )

if SEARCH_TIMEOUT <= 0:
    raise ValueError(
        f"SEARCH_TIMEOUT ({SEARCH_TIMEOUT}) must be positive. "
        "Check your .env file or environment variables."
    )
