"""Tests para utilidades de URL."""

import pytest
from utils.url_utils import get_domain, normalize_url, is_valid_url


class TestUrlUtils:
    """Tests para utilidades de URL."""
    
    def test_get_domain_standard_url(self):
        """Test extracción de dominio de URL estándar."""
        assert get_domain("https://www.example.com/path") == "example.com"
        assert get_domain("http://jobs.github.com/api") == "jobs.github.com"
        assert get_domain("https://stackoverflow.com") == "stackoverflow.com"
    
    def test_get_domain_without_www(self):
        """Test que se elimina 'www.' del dominio."""
        assert get_domain("https://www.linkedin.com") == "linkedin.com"
        assert get_domain("http://www.remoteok.com") == "remoteok.com"
    
    def test_get_domain_invalid_url(self):
        """Test con URL inválida."""
        assert get_domain("not a url") == "unknown"
        assert get_domain("") == "unknown"
    
    def test_normalize_url_absolute(self):
        """Test normalización de URL absoluta."""
        url = "https://example.com/jobs"
        assert normalize_url(url) == url
    
    def test_normalize_url_relative_with_base(self):
        """Test normalización de URL relativa con base."""
        base = "https://example.com"
        relative = "/jobs/123"
        result = normalize_url(relative, base)
        
        assert result == "https://example.com/jobs/123"
    
    def test_normalize_url_empty(self):
        """Test normalización de URL vacía."""
        assert normalize_url("") == ""
        assert normalize_url(None) == ""
    
    def test_is_valid_url_valid(self):
        """Test validación de URLs válidas."""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://jobs.com/path?q=python") is True
    
    def test_is_valid_url_invalid(self):
        """Test validación de URLs inválidas."""
        assert is_valid_url("not a url") is False
        assert is_valid_url("example.com") is False  # Sin scheme
        assert is_valid_url("") is False
