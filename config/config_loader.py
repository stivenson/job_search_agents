"""Cargador centralizado de configuración YAML."""

import logging
from pathlib import Path
from typing import Dict, Optional
import yaml

logger = logging.getLogger(__name__)

# Cache para evitar recargar el archivo múltiples veces
_cached_config: Optional[Dict] = None
_config_path: Optional[Path] = None


def load_job_sources_config(force_reload: bool = False) -> Dict:
    """Carga y cachea la configuración de job_sources.yaml.
    
    Args:
        force_reload: Si True, recarga el archivo aunque esté cacheado
    
    Returns:
        Diccionario con la configuración de job_sources
    
    Raises:
        FileNotFoundError: Si el archivo de configuración no existe
        yaml.YAMLError: Si hay un error al parsear el YAML
    """
    global _cached_config, _config_path
    
    # Retornar cache si existe y no se fuerza recarga
    if _cached_config is not None and not force_reload:
        return _cached_config
    
    # Determinar ruta al archivo
    if _config_path is None:
        # Buscar desde el directorio actual
        current_file = Path(__file__)
        _config_path = current_file.parent / "job_sources.yaml"
        
        # Si no existe, intentar desde el directorio base del proyecto
        if not _config_path.exists():
            base_dir = current_file.parent.parent
            _config_path = base_dir / "config" / "job_sources.yaml"
    
    # Verificar que existe
    if not _config_path.exists():
        logger.error(f"Archivo de configuración no encontrado: {_config_path}")
        return {}
    
    # Cargar y cachear
    try:
        with open(_config_path, 'r', encoding='utf-8') as f:
            _cached_config = yaml.safe_load(f)
            logger.debug(f"Configuración cargada desde {_config_path}")
            return _cached_config
    except yaml.YAMLError as e:
        logger.error(f"Error parseando YAML: {e}")
        raise
    except Exception as e:
        logger.error(f"Error leyendo archivo de configuración: {e}")
        return {}


def get_job_source_config(source_name: str) -> Optional[Dict]:
    """Obtiene la configuración de una fuente específica.
    
    Args:
        source_name: Nombre de la fuente (ej: 'linkedin', 'remoteok')
    
    Returns:
        Configuración de la fuente o None si no existe
    """
    config = load_job_sources_config()
    job_sources = config.get('job_sources', {})
    return job_sources.get(source_name)


def is_source_enabled(source_name: str) -> bool:
    """Verifica si una fuente de empleo está habilitada.
    
    Args:
        source_name: Nombre de la fuente
    
    Returns:
        True si está habilitada, False en caso contrario
    """
    source_config = get_job_source_config(source_name)
    if source_config is None:
        return False
    return source_config.get('enabled', True)


def get_keywords() -> list:
    """Obtiene la lista de keywords de búsqueda.
    
    Returns:
        Lista de keywords configurados
    """
    config = load_job_sources_config()
    return config.get('keywords', [])


def get_search_regions() -> Dict:
    """Obtiene la configuración de regiones de búsqueda.
    
    Returns:
        Diccionario con regiones hispanas y angloparlantes
    """
    config = load_job_sources_config()
    return config.get('search_regions', {})


def clear_cache():
    """Limpia el cache de configuración."""
    global _cached_config
    _cached_config = None
    logger.debug("Cache de configuración limpiado")
