"""Tests para job enricher."""

import pytest
from utils.job_enricher import enrich_job, batch_enrich_jobs, normalize_job_fields


class TestJobEnricher:
    """Tests para job enricher."""
    
    def test_enrich_job_basic(self):
        """Test enriquecimiento básico de job."""
        job = {
            'title': 'Python Developer',
            'company': 'Test Corp'
        }
        
        enriched = enrich_job(job, 'linkedin', ['Python'], 'Colombia', 'hispanic')
        
        assert enriched['source'] == 'linkedin'
        assert enriched['search_keywords'] == ['Python']
        assert enriched['search_country'] == 'Colombia'
        assert enriched['search_region'] == 'hispanic'
        assert enriched['region_priority'] == 1
    
    def test_enrich_job_sets_location(self):
        """Test que enrich_job establece location si falta."""
        job = {'title': 'Dev'}
        
        enriched = enrich_job(job, 'linkedin', [], 'Mexico')
        
        assert enriched['location'] == 'Mexico'
    
    def test_enrich_job_preserves_location(self):
        """Test que enrich_job preserva location existente."""
        job = {'title': 'Dev', 'location': 'Remote'}
        
        enriched = enrich_job(job, 'linkedin', [], 'Mexico')
        
        assert enriched['location'] == 'Remote'
    
    def test_batch_enrich_jobs(self):
        """Test enriquecimiento en batch."""
        jobs = [
            {'title': 'Job 1'},
            {'title': 'Job 2'},
            {'title': 'Job 3'}
        ]
        
        enriched = batch_enrich_jobs(jobs, 'remoteok', ['Python'])
        
        assert len(enriched) == 3
        for job in enriched:
            assert job['source'] == 'remoteok'
            assert job['search_keywords'] == ['Python']
    
    def test_normalize_job_fields(self):
        """Test normalización de campos."""
        job = {
            'title': '  Python Developer  ',
            'company': '  ACME Corp  ',
            'location': '  Remote  ',
            'url': '  https://example.com  '
        }
        
        normalized = normalize_job_fields(job)
        
        assert normalized['title'] == 'Python Developer'
        assert normalized['company'] == 'ACME Corp'
        assert normalized['location'] == 'Remote'
        assert normalized['url'] == 'https://example.com'
    
    def test_normalize_sets_defaults(self):
        """Test que normalize establece campos por defecto."""
        job = {'title': 'Dev'}
        
        normalized = normalize_job_fields(job)
        
        assert 'source' in normalized
        assert 'search_keywords' in normalized
        assert normalized['source'] == 'unknown'
        assert normalized['search_keywords'] == []
