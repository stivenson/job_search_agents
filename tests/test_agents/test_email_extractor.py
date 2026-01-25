"""Tests unitarios para el agente de extracción de emails."""

import pytest
from agents.email_extractor_agent import EmailExtractorAgent, ContactInfo


class TestEmailExtractorAgent:
    """Tests para EmailExtractorAgent."""
    
    @pytest.fixture
    def agent(self):
        """Crea una instancia del agente para tests."""
        return EmailExtractorAgent()
    
    @pytest.mark.asyncio
    async def test_extract_emails_basic(self, agent, sample_job_description):
        """Test extracción básica de emails."""
        result = await agent.extract_emails(sample_job_description)
        
        assert isinstance(result, dict)
        assert 'emails' in result
        assert isinstance(result['emails'], list)
        assert 'confidence' in result
    
    @pytest.mark.asyncio
    async def test_extract_emails_empty_description(self, agent):
        """Test extracción con descripción vacía."""
        result = await agent.extract_emails("")
        
        assert result['emails'] == []
        assert result['confidence'] == 0.0
    
    @pytest.mark.asyncio
    async def test_extract_emails_with_valid_email(self, agent):
        """Test extracción con email válido."""
        description = "Contact us at jobs@example.com for more information"
        result = await agent.extract_emails(description)
        
        assert 'jobs@example.com' in result['emails']
    
    @pytest.mark.asyncio
    async def test_extract_from_jobs_parallel(self, agent, sample_jobs):
        """Test extracción paralela de múltiples jobs."""
        enriched_jobs = await agent.extract_from_jobs(sample_jobs)
        
        assert len(enriched_jobs) == len(sample_jobs)
        for job in enriched_jobs:
            assert 'emails' in job
            assert 'contact_info' in job
            assert isinstance(job['emails'], list)
    
    @pytest.mark.asyncio
    async def test_extract_from_empty_jobs(self, agent):
        """Test con lista vacía de jobs."""
        result = await agent.extract_from_jobs([])
        
        assert result == []
    
    def test_contact_info_model(self):
        """Test modelo Pydantic ContactInfo."""
        contact = ContactInfo(
            emails=["test@example.com"],
            application_email="test@example.com",
            confidence=0.8
        )
        
        assert contact.emails == ["test@example.com"]
        assert contact.confidence == 0.8
        assert 0 <= contact.confidence <= 1
