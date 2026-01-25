"""Fixtures compartidos para tests de job_search_agents."""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al Python path
# Esto permite que los tests importen módulos como 'utils', 'agents', 'config', etc.
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from typing import Dict, List


@pytest.fixture
def sample_profile() -> Dict:
    """Perfil de usuario de ejemplo para tests."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1234567890",
        "skills": ["Python", "Machine Learning", "AI"],
        "experience": ["Senior Developer", "AI Engineer"],
        "education": ["Computer Science"]
    }


@pytest.fixture
def sample_jobs() -> List[Dict]:
    """Lista de trabajos de ejemplo para tests."""
    return [
        {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "location": "Remote",
            "url": "https://example.com/job1",
            "description": "Looking for a senior Python developer with AI experience",
            "source": "test",
            "keywords": ["Python", "AI"]
        },
        {
            "title": "AI Engineer",
            "company": "AI Startup",
            "location": "Colombia",
            "url": "https://example.com/job2",
            "description": "Join our AI team to build cutting-edge solutions",
            "source": "test",
            "keywords": ["AI", "Machine Learning"]
        }
    ]


@pytest.fixture
def sample_job_description() -> str:
    """Descripción de trabajo de ejemplo para tests."""
    return """
    We are looking for a Senior Python Developer to join our team.
    
    Requirements:
    - 5+ years of Python experience
    - Experience with Machine Learning and AI
    - Strong problem-solving skills
    
    Contact: hr@example.com or apply at jobs@example.com
    """


@pytest.fixture
def mock_cv_content() -> str:
    """Contenido de CV de ejemplo para tests."""
    return """# Curriculum Vitae

## Personal Information
Name: Test User
Email: test@example.com
Phone: +1234567890

## Professional Summary
Senior Python Developer with 5+ years of experience in AI and Machine Learning.

## Skills
- Python
- Machine Learning
- AI
- Django
- FastAPI

## Experience
### Senior Developer at Tech Corp (2020-2024)
- Built AI-powered applications
- Led team of 5 developers

## Education
Bachelor in Computer Science - 2019
"""


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Directorio temporal para archivos de test."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def test_results_dir(tmp_path: Path) -> Path:
    """Directorio temporal para resultados de test."""
    results_dir = tmp_path / "test_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir
