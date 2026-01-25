"""Tests para http helpers."""

import pytest
from unittest.mock import Mock, MagicMock
from utils.http_helpers import (
    setup_session_headers,
    handle_rate_limit_error,
    get_default_headers,
    wait_with_delay
)
from requests import Session


class TestHttpHelpers:
    """Tests para http helpers."""
    
    def test_setup_session_headers_with_rotator(self):
        """Test configuración de headers con rotator."""
        session = Session()
        mock_rotator = Mock()
        mock_rotator.get_realistic_headers.return_value = {'User-Agent': 'Test UA'}
        
        setup_session_headers(session, mock_rotator)
        
        assert 'User-Agent' in session.headers
        assert session.headers['User-Agent'] == 'Test UA'
    
    def test_setup_session_headers_without_rotator(self):
        """Test configuración de headers sin rotator."""
        session = Session()
        
        setup_session_headers(session, None)
        
        assert 'User-Agent' in session.headers
        assert len(session.headers['User-Agent']) > 0
    
    def test_setup_session_headers_with_custom_ua(self):
        """Test configuración con User-Agent personalizado."""
        session = Session()
        custom_ua = "CustomBot/1.0"
        
        setup_session_headers(session, None, custom_ua)
        
        assert session.headers['User-Agent'] == custom_ua
    
    def test_handle_rate_limit_with_rotator(self):
        """Test manejo de rate limit con rotator."""
        mock_rotator = Mock()
        mock_rotator.rotate = Mock()
        mock_rotator.get_realistic_headers.return_value = {'User-Agent': 'New UA'}
        session = Session()
        
        handle_rate_limit_error(mock_rotator, session, "https://example.com")
        
        mock_rotator.rotate.assert_called_once()
        assert session.headers['User-Agent'] == 'New UA'
    
    def test_get_default_headers(self):
        """Test obtención de headers por defecto."""
        headers = get_default_headers()
        
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert 'Accept-Language' in headers
    
    def test_get_default_headers_custom_ua(self):
        """Test headers con UA personalizado."""
        custom_ua = "MyBot/1.0"
        headers = get_default_headers(custom_ua)
        
        assert headers['User-Agent'] == custom_ua
