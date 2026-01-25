"""Excepciones personalizadas para el sistema de búsqueda de empleo."""


class JobSearchError(Exception):
    """Excepción base para errores del sistema de búsqueda de empleo."""
    pass


class ScrapingError(JobSearchError):
    """Excepción para errores de scraping de job boards."""
    pass


class RateLimitError(ScrapingError):
    """Excepción para cuando se detecta rate limiting (403/429)."""
    pass


class ConfigurationError(JobSearchError):
    """Excepción para errores de configuración."""
    pass


class CVParseError(JobSearchError):
    """Excepción para errores al parsear el CV."""
    pass


class LLMError(JobSearchError):
    """Excepción para errores al usar LLMs."""
    pass


class ValidationError(JobSearchError):
    """Excepción para errores de validación de datos."""
    pass
