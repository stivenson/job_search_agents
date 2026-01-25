"""Tests para excepciones personalizadas."""

import pytest
from utils.exceptions import (
    JobSearchError,
    ScrapingError,
    RateLimitError,
    ConfigurationError,
    CVParseError,
    LLMError,
    ValidationError
)


class TestExceptions:
    """Tests para jerarquía de excepciones."""
    
    def test_job_search_error_is_exception(self):
        """Test que JobSearchError hereda de Exception."""
        assert issubclass(JobSearchError, Exception)
    
    def test_scraping_error_hierarchy(self):
        """Test jerarquía de ScrapingError."""
        assert issubclass(ScrapingError, JobSearchError)
        assert issubclass(ScrapingError, Exception)
    
    def test_rate_limit_error_hierarchy(self):
        """Test jerarquía de RateLimitError."""
        assert issubclass(RateLimitError, ScrapingError)
        assert issubclass(RateLimitError, JobSearchError)
    
    def test_raise_job_search_error(self):
        """Test lanzar JobSearchError."""
        with pytest.raises(JobSearchError):
            raise JobSearchError("Test error")
    
    def test_raise_scraping_error(self):
        """Test lanzar ScrapingError."""
        with pytest.raises(ScrapingError):
            raise ScrapingError("Scraping failed")
    
    def test_catch_base_exception(self):
        """Test que las excepciones derivadas se pueden capturar con la base."""
        try:
            raise RateLimitError("Rate limited")
        except JobSearchError as e:
            assert isinstance(e, RateLimitError)
            assert "Rate limited" in str(e)
    
    def test_all_exceptions_instantiate(self):
        """Test que todas las excepciones se pueden instanciar."""
        exceptions = [
            JobSearchError("test"),
            ScrapingError("test"),
            RateLimitError("test"),
            ConfigurationError("test"),
            CVParseError("test"),
            LLMError("test"),
            ValidationError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, Exception)
            assert str(exc) == "test"
