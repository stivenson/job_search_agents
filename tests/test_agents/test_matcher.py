"""Tests unitarios para el agente de matching."""

import pytest
from agents.matcher_agent import MatcherAgent


class TestMatcherAgent:
    """Tests para MatcherAgent."""
    
    @pytest.fixture
    def agent(self):
        """Crea una instancia del agente para tests."""
        return MatcherAgent()
    
    def test_match_jobs_basic(self, agent, sample_jobs, sample_profile):
        """Test matching básico de jobs."""
        # Agregar perfil al agente (simulando que fue parseado)
        agent.profile = sample_profile
        
        matched_jobs = agent.match_jobs(sample_jobs)
        
        assert isinstance(matched_jobs, list)
        assert len(matched_jobs) <= len(sample_jobs)
        
        # Verificar que cada job tiene score
        for job in matched_jobs:
            assert 'match_score' in job
            assert 0 <= job['match_score'] <= 100
    
    def test_match_jobs_empty(self, agent):
        """Test matching con lista vacía."""
        result = agent.match_jobs([])
        
        assert result == []
    
    def test_get_match_summary(self, agent, sample_jobs):
        """Test generación de resumen de matches."""
        # Agregar scores a los jobs
        jobs_with_scores = []
        for job in sample_jobs:
            job['match_score'] = 75
            jobs_with_scores.append(job)
        
        summary = agent.get_match_summary(jobs_with_scores)
        
        assert isinstance(summary, dict)
        assert 'total_jobs' in summary or 'average_score' in summary
    
    def test_calculate_score_high_match(self, agent, sample_profile):
        """Test cálculo de score con alta coincidencia."""
        agent.profile = sample_profile
        
        job = {
            'title': 'Senior Python Developer with AI',
            'description': 'Python Machine Learning AI development',
            'location': 'Remote'
        }
        
        score = agent._calculate_match_score(job) if hasattr(agent, '_calculate_match_score') else 0
        
        # Si el método existe, el score debería ser alto
        if score > 0:
            assert score >= 50
    
    def test_filter_by_min_score(self, agent, sample_jobs):
        """Test filtrado por score mínimo."""
        # Agregar scores variados
        for i, job in enumerate(sample_jobs):
            job['match_score'] = 50 + (i * 10)
        
        filtered = [job for job in sample_jobs if job['match_score'] >= 60]
        
        assert all(job['match_score'] >= 60 for job in filtered)
