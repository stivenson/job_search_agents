"""Tests para KeywordGeneratorAgent."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from agents.keyword_generator_agent import KeywordGeneratorAgent


class TestKeywordGeneratorAgent:
    """Tests para el agente de generación de keywords."""
    
    @pytest.fixture
    def sample_profile(self):
        """Perfil de ejemplo para tests."""
        return {
            'skills': {
                'AI/ML': ['Python', 'TensorFlow', 'LLM'],
                'Cloud': ['AWS', 'Docker', 'Kubernetes']
            },
            'experience': [
                {
                    'role': 'Senior AI Engineer',
                    'company': 'TechCorp',
                    'technologies': ['Python', 'AWS', 'LLM']
                }
            ]
        }
    
    def test_create_profile_summary(self, sample_profile):
        """Test que crea resumen del perfil correctamente."""
        agent = KeywordGeneratorAgent()
        summary = agent._create_profile_summary(sample_profile)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'Python' in summary or 'Skills' in summary
    
    def test_create_profile_summary_empty(self):
        """Test con perfil vacío."""
        agent = KeywordGeneratorAgent()
        summary = agent._create_profile_summary({})
        
        assert summary == "Perfil no disponible"
    
    def test_get_profile_hash(self, sample_profile):
        """Test que genera hash del perfil."""
        agent = KeywordGeneratorAgent()
        hash1 = agent._get_profile_hash(sample_profile)
        hash2 = agent._get_profile_hash(sample_profile)
        
        # Mismo perfil debe generar mismo hash
        assert hash1 == hash2
        assert isinstance(hash1, str)
    
    def test_generate_cache_key(self):
        """Test que genera cache key correctamente."""
        agent = KeywordGeneratorAgent()
        key = agent._generate_cache_key("linkedin", "hispanic", "abc123")
        
        assert key == "linkedin:hispanic:abc123"
    
    def test_get_default_keywords(self, sample_profile):
        """Test que genera keywords por defecto."""
        agent = KeywordGeneratorAgent()
        keywords = agent._get_default_keywords(sample_profile, 5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        assert all(isinstance(kw, str) for kw in keywords)
    
    @pytest.mark.asyncio
    async def test_generate_keywords_no_llm(self, sample_profile):
        """Test generación de keywords sin LLM (fallback)."""
        with patch('agents.keyword_generator_agent.OPENAI_API_KEY', None), \
             patch('agents.keyword_generator_agent.ANTHROPIC_API_KEY', None):
            agent = KeywordGeneratorAgent()
            keywords = await agent.generate_keywords(
                profile=sample_profile,
                source="linkedin",
                region="hispanic",
                num_keywords=5
            )
            
            assert isinstance(keywords, list)
            assert len(keywords) > 0
    
    @pytest.mark.asyncio
    async def test_generate_keywords_with_base_keywords(self, sample_profile):
        """Test con keywords base."""
        with patch('agents.keyword_generator_agent.OPENAI_API_KEY', None):
            agent = KeywordGeneratorAgent()
            base_keywords = ["AI Engineer", "Python Developer"]
            
            keywords = await agent.generate_keywords(
                profile=sample_profile,
                source="linkedin",
                region="hispanic",
                base_keywords=base_keywords,
                num_keywords=5
            )
            
            assert isinstance(keywords, list)
            assert len(keywords) > 0
    
    def test_clear_cache(self):
        """Test que limpia el caché."""
        agent = KeywordGeneratorAgent()
        agent._cache["test"] = ["keyword1", "keyword2"]
        
        agent.clear_cache()
        
        assert len(agent._cache) == 0
