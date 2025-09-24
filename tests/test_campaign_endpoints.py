import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.api.campaign.campaign_endpoints import router
from app.agent.campaign_agent import CampaignAgent


class TestCampaignEndpoints(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        from fastapi import FastAPI
        
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        
        self.valid_request_data = {
            "company_name": "test_company"
        }
        
        self.sample_suggestions = {
            "suggestions": [
                "Social media campaign focusing on innovation",
                "Influencer partnerships with tech reviewers",
                "Interactive product demos at tech conferences"
            ]
        }
    
    @patch('app.api.campaign.campaign_endpoints.CampaignAgent')
    @patch('app.api.campaign.campaign_endpoints.get_session')
    async def test_retrieve_suggestions_success(self, mock_get_session, mock_campaign_agent):
        """Test successful suggestions retrieval"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_agent_instance.get_campaign_suggestions = AsyncMock(return_value=self.sample_suggestions)
        mock_campaign_agent.return_value = mock_agent_instance
        
        # Execute
        response = self.client.post(
            "/suggestions/retrieve/",
            json=self.valid_request_data
        )
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        
        response_data = response.json()
        self.assertEqual(response_data, self.sample_suggestions)
        
        mock_campaign_agent.assert_called_once_with(mock_session)
        mock_agent_instance.get_campaign_suggestions.assert_called_once_with("test_company")
    
    @patch('app.api.campaign.campaign_endpoints.CampaignAgent')
    @patch('app.api.campaign.campaign_endpoints.get_session')
    async def test_retrieve_suggestions_company_not_found(self, mock_get_session, mock_campaign_agent):
        """Test suggestions retrieval when company not found"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_agent_instance.get_campaign_suggestions = AsyncMock(
            side_effect=Exception("No suggestions found for company: nonexistent_company")
        )
        mock_campaign_agent.return_value = mock_agent_instance
        
        request_data = {"company_name": "nonexistent_company"}
        
        # Execute
        response = self.client.post(
            "/suggestions/retrieve/",
            json=request_data
        )
        
        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertEqual(response_data["detail"], "Internal Server Error")
    
    @patch('app.api.campaign.campaign_endpoints.CampaignAgent')
    @patch('app.api.campaign.campaign_endpoints.get_session')
    async def test_retrieve_suggestions_general_exception(self, mock_get_session, mock_campaign_agent):
        """Test suggestions retrieval with general exception"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_agent_instance.get_campaign_suggestions = AsyncMock(
            side_effect=Exception("Database connection error")
        )
        mock_campaign_agent.return_value = mock_agent_instance
        
        # Execute
        response = self.client.post(
            "/suggestions/retrieve/",
            json=self.valid_request_data
        )
        
        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertEqual(response_data["detail"], "Internal Server Error")
    
    def test_retrieve_suggestions_missing_company_name(self):
        """Test suggestions retrieval with missing company_name"""
        # Execute
        response = self.client.post(
            "/suggestions/retrieve/",
            json={}
        )
        
        # Assert - This should cause a KeyError which becomes 500 Internal Server Error
        self.assertEqual(response.status_code, 500)
    
    def test_retrieve_suggestions_invalid_json(self):
        """Test suggestions retrieval with invalid JSON"""
        # Execute
        response = self.client.post(
            "/suggestions/retrieve/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 422)  # FastAPI validation error
    
    def test_retrieve_suggestions_no_body(self):
        """Test suggestions retrieval with no request body"""
        # Execute
        response = self.client.post("/suggestions/retrieve/")
        
        # Assert
        self.assertEqual(response.status_code, 422)  # FastAPI validation error
    
    @patch('app.api.campaign.campaign_endpoints.CampaignAgent')
    @patch('app.api.campaign.campaign_endpoints.get_session')
    async def test_retrieve_suggestions_empty_suggestions(self, mock_get_session, mock_campaign_agent):
        """Test suggestions retrieval with empty suggestions"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_agent_instance.get_campaign_suggestions = AsyncMock(return_value={})
        mock_campaign_agent.return_value = mock_agent_instance
        
        # Execute
        response = self.client.post(
            "/suggestions/retrieve/",
            json=self.valid_request_data
        )
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data, {})
    
    @patch('app.api.campaign.campaign_endpoints.CampaignAgent')
    @patch('app.api.campaign.campaign_endpoints.get_session')
    async def test_retrieve_suggestions_complex_data(self, mock_get_session, mock_campaign_agent):
        """Test suggestions retrieval with complex nested data"""
        # Setup
        complex_suggestions = {
            "suggestions": [
                {
                    "title": "Social Media Campaign",
                    "description": "Focus on innovation and tech leadership",
                    "channels": ["Twitter", "LinkedIn", "Instagram"],
                    "budget": 50000,
                    "duration": "3 months"
                },
                {
                    "title": "Influencer Partnership",
                    "description": "Partner with tech reviewers",
                    "channels": ["YouTube", "TikTok"],
                    "budget": 30000,
                    "duration": "2 months"
                }
            ],
            "metadata": {
                "generated_at": "2023-01-01T12:00:00Z",
                "version": "1.0"
            }
        }
        
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_agent_instance.get_campaign_suggestions = AsyncMock(return_value=complex_suggestions)
        mock_campaign_agent.return_value = mock_agent_instance
        
        # Execute
        response = self.client.post(
            "/suggestions/retrieve/",
            json=self.valid_request_data
        )
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data, complex_suggestions)
    
    @patch('app.api.campaign.campaign_endpoints.CampaignAgent')
    @patch('app.api.campaign.campaign_endpoints.get_session')
    async def test_retrieve_suggestions_different_company_names(self, mock_get_session, mock_campaign_agent):
        """Test suggestions retrieval with different company name formats"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_agent_instance.get_campaign_suggestions = AsyncMock(return_value=self.sample_suggestions)
        mock_campaign_agent.return_value = mock_agent_instance
        
        test_company_names = [
            "simple_company",
            "Company With Spaces",
            "company-with-hyphens",
            "Company123",
            "UPPERCASE_COMPANY",
            "company.with.dots"
        ]
        
        for company_name in test_company_names:
            request_data = {"company_name": company_name}
            
            # Execute
            response = self.client.post(
                "/suggestions/retrieve/",
                json=request_data
            )
            
            # Assert
            self.assertEqual(response.status_code, 200, f"Failed for company: {company_name}")
            mock_agent_instance.get_campaign_suggestions.assert_called_with(company_name)
    
    @patch('app.api.campaign.campaign_endpoints.CampaignAgent')
    @patch('app.api.campaign.campaign_endpoints.get_session')
    @patch('app.api.campaign.campaign_endpoints.logger')
    async def test_retrieve_suggestions_logging(self, mock_logger, mock_get_session, mock_campaign_agent):
        """Test that errors are properly logged"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        test_exception = Exception("Test error for logging")
        mock_agent_instance.get_campaign_suggestions = AsyncMock(side_effect=test_exception)
        mock_campaign_agent.return_value = mock_agent_instance
        
        # Execute
        response = self.client.post(
            "/suggestions/retrieve/",
            json=self.valid_request_data
        )
        
        # Assert
        self.assertEqual(response.status_code, 500)
        mock_logger.error.assert_called_once_with(f"Error retrieving suggestions: {test_exception}")
    
    def test_retrieve_suggestions_extra_fields(self):
        """Test suggestions retrieval with extra fields in request"""
        # Setup
        request_with_extra = {
            "company_name": "test_company",
            "extra_field": "should be ignored",
            "another_field": 123
        }
        
        # The endpoint only uses company_name, so extra fields should be ignored
        with patch('app.api.campaign.campaign_endpoints.CampaignAgent') as mock_campaign_agent, \
             patch('app.api.campaign.campaign_endpoints.get_session') as mock_get_session:
            
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            mock_agent_instance = Mock()
            mock_agent_instance.get_campaign_suggestions = AsyncMock(return_value=self.sample_suggestions)
            mock_campaign_agent.return_value = mock_agent_instance
            
            # Execute
            response = self.client.post(
                "/suggestions/retrieve/",
                json=request_with_extra
            )
            
            # Assert
            self.assertEqual(response.status_code, 200)
            mock_agent_instance.get_campaign_suggestions.assert_called_once_with("test_company")


if __name__ == '__main__':
    unittest.main()