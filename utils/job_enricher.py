"""Utilidades para enriquecer jobs con metadata estándar."""

from typing import Dict, List, Optional


def enrich_job(job: Dict, source: str, keywords: List[str], 
               country: Optional[str] = None, region_type: Optional[str] = None) -> Dict:
    """Enriquece un job con metadata estándar.
    
    Args:
        job: Diccionario con datos del trabajo
        source: Nombre de la fuente (ej: 'linkedin', 'remoteok')
        keywords: Lista de keywords usados en la búsqueda
        country: País de búsqueda opcional
        region_type: Tipo de región opcional ('hispanic', 'english')
    
    Returns:
        Job enriquecido con metadata adicional
    
    Examples:
        >>> job = {'title': 'Python Developer', 'company': 'ACME'}
        >>> enrich_job(job, 'linkedin', ['Python'], 'Colombia', 'hispanic')
        {'title': 'Python Developer', 'company': 'ACME', 'source': 'linkedin', ...}
    """
    # Copiar job para no modificar el original
    enriched = job.copy()
    
    # Agregar metadata de fuente
    enriched['source'] = source
    enriched['search_keywords'] = keywords
    
    # Agregar metadata de región si está disponible
    if country:
        enriched['search_country'] = country
    
    if region_type:
        enriched['search_region'] = region_type
        enriched['region_priority'] = 1 if region_type == "hispanic" else 2
    
    # Asegurar que location tenga un valor
    if not enriched.get('location'):
        enriched['location'] = country or 'Remote'
    
    # Asegurar que haya un URL
    if not enriched.get('url'):
        enriched['url'] = ''
    
    return enriched


def batch_enrich_jobs(jobs: List[Dict], source: str, keywords: List[str],
                     country: Optional[str] = None, region_type: Optional[str] = None) -> List[Dict]:
    """Enriquece una lista de jobs con metadata estándar.
    
    Args:
        jobs: Lista de jobs a enriquecer
        source: Nombre de la fuente
        keywords: Lista de keywords usados en la búsqueda
        country: País de búsqueda opcional
        region_type: Tipo de región opcional
    
    Returns:
        Lista de jobs enriquecidos
    """
    return [enrich_job(job, source, keywords, country, region_type) for job in jobs]


def normalize_job_fields(job: Dict) -> Dict:
    """Normaliza campos comunes de un job a un formato estándar.
    
    Args:
        job: Job a normalizar
    
    Returns:
        Job con campos normalizados
    """
    normalized = job.copy()
    
    # Normalizar título
    if 'title' in normalized and normalized['title']:
        normalized['title'] = normalized['title'].strip()
    
    # Normalizar compañía
    if 'company' in normalized and normalized['company']:
        normalized['company'] = normalized['company'].strip()
    
    # Normalizar location
    if 'location' in normalized and normalized['location']:
        normalized['location'] = normalized['location'].strip()
    
    # Normalizar URL
    if 'url' in normalized and normalized['url']:
        normalized['url'] = normalized['url'].strip()
    
    # Asegurar que existan campos requeridos
    if 'source' not in normalized:
        normalized['source'] = 'unknown'
    
    if 'search_keywords' not in normalized:
        normalized['search_keywords'] = []
    
    return normalized
