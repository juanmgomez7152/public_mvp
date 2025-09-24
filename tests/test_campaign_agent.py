import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.campaign_agent import CampaignAgent
from app.db.sqlite_conn import CompanyProfile, CampaignSuggestions, JobQueue


class TestCampaignAgent(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db_tool = Mock()
        self.mock_llm_toolkit = Mock()
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'EMAIL_USER': 'test@example.com',
            'EMAIL_APP_PASSWORD': 'test-password',
            'EMAIL_SERVER': 'smtp.gmail.com',
            'EMAIL_PORT': '587'
        })
        self.env_patcher.start()
        
        # Create CampaignAgent instance with mocked dependencies
        with patch('app.agent.campaign_agent.DBTool') as mock_db_tool_class, \
             patch('app.agent.campaign_agent.OpenAITool') as mock_llm_class:
            
            mock_db_tool_class.return_value = self.mock_db_tool
            mock_llm_class.return_value = self.mock_llm_toolkit
            
            self.agent = CampaignAgent(self.mock_db)
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
    
    @patch('app.agent.campaign_agent.smtplib.SMTP')
    def test_alert_completion_success(self, mock_smtp):
        """Test successful email notification"""
        # Setup
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Execute
        result = self.agent._alert_completion("test_company", "user@example.com")
        
        # Assert
        self.assertTrue(result)
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "test-password")
        mock_server.send_message.assert_called_once()
    
    @patch('app.agent.campaign_agent.smtplib.SMTP')
    def test_alert_completion_failure(self, mock_smtp):
        """Test email notification failure"""
        # Setup
        mock_smtp.side_effect = Exception("SMTP Error")
        
        # Execute
        result = self.agent._alert_completion("test_company", "user@example.com")
        
        # Assert
        self.assertFalse(result)
    
    def test_alert_completion_missing_credentials(self):
        """Test email notification with missing credentials"""
        # Setup - clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            agent = CampaignAgent(self.mock_db)
            
            # Execute
            result = agent._alert_completion("test_company", "user@example.com")
            
            # Assert
            self.assertFalse(result)
    
    async def test_extract_profile(self):
        """Test company profile extraction"""
        # Setup
        expected_profile = CompanyProfile(
            company_name="test_company",
            brand_voice="Professional",
            target_audience="Tech enthusiasts",
            product_category="Technology"
        )
        self.mock_db_tool.get_company_profile.return_value = expected_profile
        
        # Execute
        result = await self.agent._extract_profile("test_company")
        
        # Assert
        self.assertEqual(result, expected_profile)
        self.mock_db_tool.get_company_profile.assert_called_once_with("test_company")
    
    async def test_generate_suggestions(self):
        """Test campaign suggestions generation"""
        # Setup
        mock_profile = CompanyProfile(
            company_name="test_company",
            brand_voice="Professional",
            target_audience="Tech enthusiasts"
        )
        expected_suggestions = CampaignSuggestions(
            company_name="test_company",
            suggested_campaign={"suggestions": ["Campaign idea 1", "Campaign idea 2"]}
        )
        self.mock_llm_toolkit.generate_campaign_ideas.return_value = expected_suggestions
        
        # Execute
        result = await self.agent._generate_suggestions(mock_profile, "Increase awareness")
        
        # Assert
        self.assertEqual(result, expected_suggestions)
        self.mock_llm_toolkit.generate_campaign_ideas.assert_called_once_with(
            mock_profile, "Increase awareness"
        )
    
    async def test_store_suggestions_success(self):
        """Test storing suggestions successfully"""
        # Setup
        mock_suggestions = CampaignSuggestions(
            company_name="test_company",
            suggested_campaign={"suggestions": ["Campaign 1"]}
        )
        
        with patch.object(self.agent, '_alert_completion', return_value=True):
            # Execute
            await self.agent._store_suggestions("test_company", mock_suggestions, "user@example.com")
            
            # Assert
            self.mock_db_tool.save_campaign_suggestion.assert_called_once_with(mock_suggestions)
            self.mock_db_tool.update_job_status.assert_called_once_with("test_company", "completed")
    
    async def test_store_suggestions_email_failure(self):
        """Test storing suggestions with email failure"""
        # Setup
        mock_suggestions = CampaignSuggestions(
            company_name="test_company",
            suggested_campaign={"suggestions": ["Campaign 1"]}
        )
        
        with patch.object(self.agent, '_alert_completion', return_value=False):
            # Execute & Assert
            with self.assertRaises(Exception) as context:
                await self.agent._store_suggestions("test_company", mock_suggestions, "user@example.com")
            
            self.assertEqual(str(context.exception), "Failed to send email notification.")
    
    async def test_get_campaign_suggestions_success(self):
        """Test retrieving campaign suggestions successfully"""
        # Setup
        expected_suggestions = {"suggestions": ["Campaign 1", "Campaign 2"]}
        mock_campaign = Mock()
        mock_campaign.suggested_campaign = expected_suggestions
        self.mock_db_tool.get_campaign_suggestions.return_value = mock_campaign
        
        # Execute
        result = await self.agent.get_campaign_suggestions("test_company")
        
        # Assert
        self.assertEqual(result, expected_suggestions)
        self.mock_db_tool.get_campaign_suggestions.assert_called_once_with("test_company")
    
    async def test_get_campaign_suggestions_not_found(self):
        """Test retrieving campaign suggestions when none exist"""
        # Setup
        self.mock_db_tool.get_campaign_suggestions.return_value = None
        
        # Execute & Assert
        with self.assertRaises(Exception) as context:
            await self.agent.get_campaign_suggestions("test_company")
        
        self.assertEqual(str(context.exception), "No suggestions found for company: test_company")
    
    async def test_orchestrator_success(self):
        """Test full orchestration flow success"""
        # Setup
        campaign_request = {
            "company_name": "Test Company",
            "campaign_goal": "Increase sales",
            "email": "User@Example.com"
        }
        
        mock_profile = CompanyProfile(company_name="test company")
        mock_suggestions = CampaignSuggestions(
            company_name="test company",
            suggested_campaign={"suggestions": ["Campaign 1"]}
        )
        
        with patch.object(self.agent, '_extract_profile', return_value=mock_profile) as mock_extract, \
             patch.object(self.agent, '_generate_suggestions', return_value=mock_suggestions) as mock_generate, \
             patch.object(self.agent, '_store_suggestions') as mock_store:
            
            # Execute
            await self.agent.orchestrator(campaign_request)
            
            # Assert
            self.mock_db_tool.load_job.assert_called_once_with("test company")
            mock_extract.assert_called_once_with("test company")
            mock_generate.assert_called_once_with(mock_profile, "Increase sales")
            mock_store.assert_called_once_with("test company", mock_suggestions, "user@example.com")


if __name__ == '__main__':
    unittest.main()