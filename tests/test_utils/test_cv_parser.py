"""Tests unitarios para el parser de CV."""

import pytest
from pathlib import Path
from utils.cv_parser import CVParser
from utils.exceptions import CVParseError


class TestCVParser:
    """Tests para CVParser."""
    
    def test_parse_basic_cv(self, tmp_path, mock_cv_content):
        """Test parsing de CV básico."""
        # Crear archivo CV temporal
        cv_file = tmp_path / "test_cv.md"
        cv_file.write_text(mock_cv_content, encoding='utf-8')
        
        # Parsear CV
        parser = CVParser(cv_path=cv_file)
        profile = parser.parse()
        
        # Verificar que se extrajo información básica
        assert profile is not None
        assert isinstance(profile, dict)
        assert 'skills' in profile or 'experience' in profile
    
    def test_parse_missing_cv(self):
        """Test parsing cuando el CV no existe."""
        parser = CVParser(cv_path=Path("nonexistent.md"))
        
        with pytest.raises((CVParseError, FileNotFoundError, Exception)):
            parser.parse()
    
    def test_parse_empty_cv(self, tmp_path):
        """Test parsing de CV vacío."""
        cv_file = tmp_path / "empty_cv.md"
        cv_file.write_text("", encoding='utf-8')
        
        parser = CVParser(cv_path=cv_file)
        profile = parser.parse()
        
        # Debería retornar un dict, aunque vacío
        assert isinstance(profile, dict)
    
    def test_extract_skills(self, sample_profile):
        """Test extracción de skills del perfil."""
        parser = CVParser()
        skills = parser.get_skills_list(sample_profile)
        
        assert isinstance(skills, list)
        if 'skills' in sample_profile:
            assert len(skills) > 0
