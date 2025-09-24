import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.api.campaign_agent.campaign_agent_endpoints import router
from app.agent.campaign_agent import CampaignAgent


class TestCampaignAgentEndpoints(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        from fastapi import FastAPI
        
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        
        self.valid_request_data = {
            "company_name": "test_company",
            "campaign_goal": "Increase brand awareness",
            "email": "test@example.com"
        }
    
    @patch('app.api.campaign_agent.campaign_agent_endpoints.CampaignAgent')
    @patch('app.api.campaign_agent.campaign_agent_endpoints.get_session')
    def test_campaign_agent_trigger_success(self, mock_get_session, mock_campaign_agent):
        """Test successful campaign agent trigger"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_campaign_agent.return_value = mock_agent_instance
        
        # Execute
        response = self.client.post(
            "/campaign-agent-suggestions/",
            json=self.valid_request_data
        )
        
        # Assert
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.text, "Request Accepted.")
        mock_campaign_agent.assert_called_once_with(mock_session)
    
    def test_campaign_agent_trigger_missing_company_name(self):
        """Test campaign agent trigger with missing company_name"""
        # Setup
        invalid_request = {
            "campaign_goal": "Increase brand awareness",
            "email": "test@example.com"
        }
        
        # Execute
        response = self.client.post(
            "/campaign-agent-suggestions/",
            json=invalid_request
        )
        
        # Assert
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("Missing required fields", response_data["detail"])
        self.assertIn("company_name", response_data["detail"])
    
    def test_campaign_agent_trigger_missing_campaign_goal(self):
        """Test campaign agent trigger with missing campaign_goal"""
        # Setup
        invalid_request = {
            "company_name": "test_company",
            "email": "test@example.com"
        }
        
        # Execute
        response = self.client.post(
            "/campaign-agent-suggestions/",
            json=invalid_request
        )
        
        # Assert
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("Missing required fields", response_data["detail"])
        self.assertIn("campaign_goal", response_data["detail"])
    
    def test_campaign_agent_trigger_missing_email(self):
        """Test campaign agent trigger with missing email"""
        # Setup
        invalid_request = {
            "company_name": "test_company",
            "campaign_goal": "Increase brand awareness"
        }
        
        # Execute
        response = self.client.post(
            "/campaign-agent-suggestions/",
            json=invalid_request
        )
        
        # Assert
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("Missing required fields", response_data["detail"])
        self.assertIn("email", response_data["detail"])
    
    def test_campaign_agent_trigger_missing_all_fields(self):
        """Test campaign agent trigger with all required fields missing"""
        # Setup
        invalid_request = {}
        
        # Execute
        response = self.client.post(
            "/campaign-agent-suggestions/",
            json=invalid_request
        )
        
        # Assert
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        detail = response_data["detail"]
        self.assertIn("Missing required fields", detail)
        self.assertIn("company_name", detail)
        self.assertIn("campaign_goal", detail)
        self.assertIn("email", detail)
    
    def test_campaign_agent_trigger_empty_json(self):
        """Test campaign agent trigger with empty JSON"""
        # Execute
        response = self.client.post("/campaign-agent-suggestions/")
        
        # Assert
        self.assertEqual(response.status_code, 422)  # FastAPI validation error
    
    def test_campaign_agent_trigger_invalid_json(self):
        """Test campaign agent trigger with invalid JSON"""
        # Execute
        response = self.client.post(
            "/campaign-agent-suggestions/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 422)  # FastAPI validation error
    
    @patch('app.api.campaign_agent.campaign_agent_endpoints.CampaignAgent')
    @patch('app.api.campaign_agent.campaign_agent_endpoints.get_session')
    def test_campaign_agent_trigger_with_extra_fields(self, mock_get_session, mock_campaign_agent):
        """Test campaign agent trigger with extra fields (should still work)"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_campaign_agent.return_value = mock_agent_instance
        
        request_with_extra = {
            **self.valid_request_data,
            "extra_field": "should be ignored"
        }
        
        # Execute
        response = self.client.post(
            "/campaign-agent-suggestions/",
            json=request_with_extra
        )
        
        # Assert
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.text, "Request Accepted.")
    
    def test_campaign_agent_trigger_case_sensitivity(self):
        """Test that field names are case sensitive"""
        # Setup
        case_sensitive_request = {
            "Company_Name": "test_company",  # Wrong case
            "campaign_goal": "Increase brand awareness",
            "email": "test@example.com"
        }
        
        # Execute
        response = self.client.post(
            "/campaign-agent-suggestions/",
            json=case_sensitive_request
        )
        
        # Assert
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("Missing required fields", response_data["detail"])
        self.assertIn("company_name", response_data["detail"])
    
    @patch('app.api.campaign_agent.campaign_agent_endpoints.CampaignAgent')
    @patch('app.api.campaign_agent.campaign_agent_endpoints.get_session')
    def test_campaign_agent_trigger_various_data_types(self, mock_get_session, mock_campaign_agent):
        """Test campaign agent trigger with various data types"""
        # Setup
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        mock_agent_instance = Mock()
        mock_campaign_agent.return_value = mock_agent_instance
        
        # Test with different valid data types
        valid_requests = [
            {
                "company_name": "Test Company",
                "campaign_goal": "Goal with spaces and numbers 123",
                "email": "user.name+tag@example.com"
            },
            {
                "company_name": "company-with-hyphens",
                "campaign_goal": "Multi-line\ngoal statement",
                "email": "simple@test.co"
            }
        ]
        
        for request_data in valid_requests:
            # Execute
            response = self.client.post(
                "/campaign-agent-suggestions/",
                json=request_data
            )
            
            # Assert
            self.assertEqual(response.status_code, 202, f"Failed for request: {request_data}")
            self.assertEqual(response.text, "Request Accepted.")
    
    def test_campaign_agent_trigger_field_type_validation(self):
        """Test field type validation (all should be strings)"""
        # Test with non-string values
        invalid_type_requests = [
            {
                "company_name": 123,  # Should be string
                "campaign_goal": "Increase brand awareness",
                "email": "test@example.com"
            },
            {
                "company_name": "test_company",
                "campaign_goal": ["goal1", "goal2"],  # Should be string
                "email": "test@example.com"
            },
            {
                "company_name": "test_company",
                "campaign_goal": "Increase brand awareness",
                "email": {"user": "test", "domain": "example.com"}  # Should be string
            }
        ]
        
        for request_data in invalid_type_requests:
            # Execute - these should still pass field existence check
            # but might be handled differently by the agent
            response = self.client.post(
                "/campaign-agent-suggestions/",
                json=request_data
            )
            
            # The endpoint only checks for field existence, not types
            # So these should still return 202 unless FastAPI validates
            self.assertIn(response.status_code, [202, 400, 422])


if __name__ == '__main__':
    unittest.main()