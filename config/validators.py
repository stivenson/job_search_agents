"""Validadores de configuración usando Pydantic."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class JobSourceConfig(BaseModel):
    """Configuración para una fuente de empleo."""
    enabled: bool = True
    use_api: bool = False
    max_results: int = Field(default=50, gt=0, le=1000)
    base_url: str
    
    @validator('max_results')
    def max_results_valid(cls, v):
        """Valida que max_results sea positivo y razonable."""
        if v <= 0:
            raise ValueError('max_results must be positive')
        if v > 1000:
            raise ValueError('max_results should not exceed 1000')
        return v


class LanguagePreferencesConfig(BaseModel):
    """Configuración de preferencias de idioma."""
    preferred_languages: List[str] = Field(default_factory=list)
    acceptable_english: List[str] = Field(default_factory=list)
    fluent_english_required: List[str] = Field(default_factory=list)
    preferred_regions: List[str] = Field(default_factory=list)


class SearchRegionsConfig(BaseModel):
    """Configuración de regiones de búsqueda."""
    hispanic_countries: List[str] = Field(default_factory=list)
    english_countries: List[str] = Field(default_factory=list)
    country_codes: Dict[str, str] = Field(default_factory=dict)


class FiltersConfig(BaseModel):
    """Configuración de filtros de búsqueda."""
    employment_type: List[str] = Field(default_factory=list)
    location: List[str] = Field(default_factory=list)
    experience_level: List[str] = Field(default_factory=list)


class JobSourcesConfig(BaseModel):
    """Configuración completa de job_sources.yaml."""
    keywords: List[str] = Field(min_items=1)
    filters: Optional[FiltersConfig] = None
    skills_required: List[str] = Field(default_factory=list)
    language_preferences: Optional[LanguagePreferencesConfig] = None
    search_regions: Optional[SearchRegionsConfig] = None
    job_sources: Dict[str, JobSourceConfig]
    
    @validator('keywords')
    def keywords_not_empty(cls, v):
        """Valida que haya al menos un keyword."""
        if not v or len(v) == 0:
            raise ValueError('At least one keyword is required')
        return v
    
    @validator('job_sources')
    def at_least_one_source_enabled(cls, v):
        """Valida que al menos una fuente esté habilitada."""
        if not any(source.enabled for source in v.values()):
            raise ValueError('At least one job source must be enabled')
        return v


def validate_job_sources_config(config_dict: Dict) -> JobSourcesConfig:
    """Valida la configuración de job_sources.yaml.
    
    Args:
        config_dict: Diccionario con la configuración cargada del YAML
    
    Returns:
        JobSourcesConfig validado
    
    Raises:
        ValidationError: Si la configuración no es válida
    """
    return JobSourcesConfig(**config_dict)
