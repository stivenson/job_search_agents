"""Tests para validadores de configuración."""

import pytest
from config.validators import (
    JobSourceConfig, 
    JobSourcesConfig, 
    validate_job_sources_config
)
from pydantic import ValidationError


class TestJobSourceConfig:
    """Tests para JobSourceConfig."""
    
    def test_valid_config(self):
        """Test configuración válida."""
        config = JobSourceConfig(
            enabled=True,
            max_results=50,
            base_url="https://example.com"
        )
        
        assert config.enabled is True
        assert config.max_results == 50
        assert config.base_url == "https://example.com"
    
    def test_max_results_validation(self):
        """Test validación de max_results."""
        with pytest.raises(ValidationError):
            JobSourceConfig(
                enabled=True,
                max_results=0,  # Inválido
                base_url="https://example.com"
            )
        
        with pytest.raises(ValidationError):
            JobSourceConfig(
                enabled=True,
                max_results=-10,  # Inválido
                base_url="https://example.com"
            )
    
    def test_defaults(self):
        """Test valores por defecto."""
        config = JobSourceConfig(base_url="https://example.com")
        
        assert config.enabled is True
        assert config.use_api is False
        assert config.max_results == 50


class TestJobSourcesConfig:
    """Tests para JobSourcesConfig."""
    
    def test_valid_full_config(self):
        """Test configuración completa válida."""
        config_dict = {
            "keywords": ["Python", "AI"],
            "job_sources": {
                "linkedin": {
                    "enabled": True,
                    "max_results": 50,
                    "base_url": "https://linkedin.com"
                }
            }
        }
        
        config = JobSourcesConfig(**config_dict)
        
        assert len(config.keywords) == 2
        assert "linkedin" in config.job_sources
    
    def test_empty_keywords_invalid(self):
        """Test que keywords vacíos son inválidos."""
        config_dict = {
            "keywords": [],
            "job_sources": {
                "linkedin": {
                    "enabled": True,
                    "max_results": 50,
                    "base_url": "https://linkedin.com"
                }
            }
        }
        
        with pytest.raises(ValidationError):
            JobSourcesConfig(**config_dict)
    
    def test_no_sources_enabled_invalid(self):
        """Test que al menos una fuente debe estar habilitada."""
        config_dict = {
            "keywords": ["Python"],
            "job_sources": {
                "linkedin": {
                    "enabled": False,
                    "max_results": 50,
                    "base_url": "https://linkedin.com"
                }
            }
        }
        
        with pytest.raises(ValidationError):
            JobSourcesConfig(**config_dict)
    
    def test_validate_function(self):
        """Test función de validación."""
        config_dict = {
            "keywords": ["Python", "AI"],
            "job_sources": {
                "linkedin": {
                    "enabled": True,
                    "max_results": 50,
                    "base_url": "https://linkedin.com"
                }
            }
        }
        
        config = validate_job_sources_config(config_dict)
        
        assert isinstance(config, JobSourcesConfig)
        assert len(config.keywords) == 2
