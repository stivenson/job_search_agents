"""Tests para SemanticMatcherAgent."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from agents.semantic_matcher_agent import SemanticMatcherAgent, SemanticMatchResult


class TestSemanticMatcherAgent:
    """Tests para el agente de matching semántico."""
    
    @pytest.fixture
    def sample_job(self):
        """Job de ejemplo para tests."""
        return {
            'title': 'Senior Python Developer',
            'company': 'TechCorp',
            'location': 'Remote',
            'description': 'We are looking for a Senior Python Developer with 5+ years of experience in AI/ML...'
        }
    
    @pytest.fixture
    def sample_profile(self):
        """Perfil de ejemplo para tests."""
        return {
            'skills': {
                'Programming': ['Python', 'JavaScript'],
                'AI/ML': ['TensorFlow', 'LLM', 'Machine Learning']
            },
            'experience': [
                {
                    'role': 'Senior AI Engineer',
                    'company': 'TechCorp',
                    'technologies': ['Python', 'AWS', 'TensorFlow']
                }
            ]
        }
    
    def test_create_candidate_profile_summary(self, sample_profile):
        """Test que crea resumen del perfil correctamente."""
        agent = SemanticMatcherAgent()
        summary = agent._create_candidate_profile_summary(sample_profile)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'Python' in summary or 'Skills' in summary
    
    def test_create_candidate_profile_summary_empty(self):
        """Test con perfil vacío."""
        agent = SemanticMatcherAgent()
        summary = agent._create_candidate_profile_summary({})
        
        assert summary == "Perfil no disponible"
    
    @pytest.mark.asyncio
    async def test_analyze_match_no_llm(self, sample_job, sample_profile):
        """Test análisis sin LLM (fallback)."""
        with patch('agents.semantic_matcher_agent.OPENAI_API_KEY', None), \
             patch('agents.semantic_matcher_agent.ANTHROPIC_API_KEY', None):
            agent = SemanticMatcherAgent()
            result = await agent.analyze_match(sample_job, sample_profile)
            
            assert isinstance(result, dict)
            assert 'semantic_score' in result
            assert result['semantic_score'] == 0.0
            assert 'confidence' in result
            assert 'concerns' in result
    
    def test_combine_scores(self):
        """Test combinación de scores."""
        agent = SemanticMatcherAgent()
        
        # Test con ambos scores
        combined = agent.combine_scores(
            heuristic_score=70.0,
            semantic_score=90.0,
            heuristic_weight=0.4,
            semantic_weight=0.6
        )
        
        expected = (70.0 * 0.4) + (90.0 * 0.6)
        assert combined == pytest.approx(expected, rel=0.01)
    
    def test_combine_scores_no_semantic(self):
        """Test cuando no hay score semántico."""
        agent = SemanticMatcherAgent()
        
        combined = agent.combine_scores(
            heuristic_score=80.0,
            semantic_score=0.0,
            heuristic_weight=0.4,
            semantic_weight=0.6
        )
        
        # Debe retornar solo el heurístico
        assert combined == 80.0
    
    def test_combine_scores_bounds(self):
        """Test que scores combinados están en rango 0-100."""
        agent = SemanticMatcherAgent()
        
        # Test límite superior
        combined = agent.combine_scores(100.0, 100.0)
        assert combined <= 100.0
        
        # Test límite inferior
        combined = agent.combine_scores(0.0, 0.0)
        assert combined >= 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_batch_empty(self):
        """Test con lista vacía."""
        agent = SemanticMatcherAgent()
        result = await agent.analyze_batch([], {})
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_analyze_batch_no_llm(self, sample_job, sample_profile):
        """Test batch sin LLM."""
        with patch('agents.semantic_matcher_agent.OPENAI_API_KEY', None):
            agent = SemanticMatcherAgent()
            jobs = [sample_job]
            
            result = await agent.analyze_batch(jobs, sample_profile)
            
            # Debe retornar trabajos sin modificar si no hay LLM
            assert len(result) == 1
            assert result == jobs
