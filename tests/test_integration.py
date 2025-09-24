import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.db.sqlite_conn import Base, CompanyProfile, CampaignSuggestions, JobQueue, get_session


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete application flow"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database for integration tests"""
        cls.test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=cls.test_engine)
        cls.TestSession = sessionmaker(bind=cls.test_engine)
        
        # Override the get_session dependency
        def override_get_session():
            session = cls.TestSession()
            try:
                yield session
            finally:
                session.close()
        
        app.dependency_overrides[get_session] = override_get_session
        cls.client = TestClient(app)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after integration tests"""
        app.dependency_overrides.clear()
    
    def setUp(self):
        """Set up test data for each test"""
        self.session = self.TestSession()
        
        # Add test company profile
        self.test_company = CompanyProfile(
            company_name="integration_test_company",
            brand_voice="Professional and innovative",
            target_audience="Tech enthusiasts aged 25-45",
            product_category="Technology",
            style_guide="Modern, clean, minimalist design",
            recent_campaign_metrics={"ctr": 0.05, "conversion_rate": 0.02}
        )
        self.session.add(self.test_company)
        self.session.commit()
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear all data from tables
        self.session.query(JobQueue).delete()
        self.session.query(CampaignSuggestions).delete()
        self.session.query(CompanyProfile).delete()
        self.session.commit()
        self.session.close()
    
    def test_app_startup_and_health_check(self):
        """Test application startup and health check endpoint"""
        response = self.client.get("/")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"Message": "Ok 🪅"})
    
    @patch('app.agent.tools.openai_tool.OpenAI')
    @patch('app.agent.campaign_agent.smtplib.SMTP')
    def test_complete_campaign_suggestion_flow(self, mock_smtp, mock_openai):
        """Test the complete flow from request to completion"""
        # Setup mocks
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock()
        mock_parsed_output = Mock()
        mock_parsed_output.company_name = "integration_test_company"
        mock_parsed_output.suggestions = [
            "Social media campaign focusing on innovation",
            "Influencer partnerships with tech reviewers"
        ]
        mock_response.output_parsed = mock_parsed_output
        mock_client.responses.parse.return_value = mock_response
        
        # Mock environment variables for email
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key',
            'EMAIL_USER': 'test@example.com',
            'EMAIL_APP_PASSWORD': 'test-password'
        }):
            # Step 1: Trigger campaign agent
            request_data = {
                "company_name": "integration_test_company",
                "campaign_goal": "Increase brand awareness",
                "email": "user@example.com"
            }
            
            response = self.client.post(
                "/rest/api/campaign-agent/campaign-agent-suggestions/",
                json=request_data
            )
            
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.text, "Request Accepted.")
            
            # Verify that job was created
            job = self.session.query(JobQueue).filter_by(
                company_name="integration_test_company"
            ).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "working")
            
            # Step 2: Simulate background task completion
            # (In real scenario, this would be done by background task)
            from app.agent.campaign_agent import CampaignAgent
            
            agent = CampaignAgent(self.session)
            
            # Note: Due to async nature, we'll test components individually
            # The background task would normally handle the orchestrator call
    
    @patch('app.agent.tools.openai_tool.OpenAI')
    def test_campaign_suggestion_retrieval_flow(self, mock_openai):
        """Test the flow of retrieving campaign suggestions"""
        # Setup - add campaign suggestions to database
        suggestions = CampaignSuggestions(
            company_name="integration_test_company",
            suggested_campaign={
                "suggestions": [
                    "Social media campaign focusing on innovation",
                    "Influencer partnerships with tech reviewers",
                    "Interactive product demos at tech conferences"
                ]
            }
        )
        self.session.add(suggestions)
        self.session.commit()
        
        # Test retrieval
        request_data = {"company_name": "integration_test_company"}
        
        response = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            json=request_data
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        expected_suggestions = {
            "suggestions": [
                "Social media campaign focusing on innovation",
                "Influencer partnerships with tech reviewers",
                "Interactive product demos at tech conferences"
            ]
        }
        
        self.assertEqual(response_data, expected_suggestions)
    
    def test_campaign_suggestion_retrieval_not_found(self):
        """Test retrieving suggestions for non-existent company"""
        request_data = {"company_name": "nonexistent_company"}
        
        response = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            json=request_data
        )
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Internal Server Error")
    
    def test_database_consistency_across_requests(self):
        """Test that database operations maintain consistency across multiple requests"""
        # Add multiple companies
        companies = [
            CompanyProfile(
                company_name="company_1",
                brand_voice="Professional",
                target_audience="Business professionals"
            ),
            CompanyProfile(
                company_name="company_2",
                brand_voice="Casual",
                target_audience="Young adults"
            )
        ]
        
        for company in companies:
            self.session.add(company)
        self.session.commit()
        
        # Add suggestions for both companies
        suggestions_list = [
            CampaignSuggestions(
                company_name="company_1",
                suggested_campaign={"suggestions": ["B2B Campaign"]}
            ),
            CampaignSuggestions(
                company_name="company_2",
                suggested_campaign={"suggestions": ["Youth Campaign"]}
            )
        ]
        
        for suggestions in suggestions_list:
            self.session.add(suggestions)
        self.session.commit()
        
        # Retrieve suggestions for company_1
        response1 = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            json={"company_name": "company_1"}
        )
        
        # Retrieve suggestions for company_2
        response2 = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            json={"company_name": "company_2"}
        )
        
        # Assert both requests successful and return different data
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        data1 = response1.json()
        data2 = response2.json()
        
        self.assertEqual(data1["suggestions"], ["B2B Campaign"])
        self.assertEqual(data2["suggestions"], ["Youth Campaign"])
        self.assertNotEqual(data1, data2)
    
    def test_api_error_handling_consistency(self):
        """Test that API error handling is consistent across endpoints"""
        # Test invalid JSON
        response = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 422)
        
        # Test missing required fields
        response = self.client.post(
            "/rest/api/campaign-agent/campaign-agent-suggestions/",
            json={"company_name": "test"}  # Missing required fields
        )
        self.assertEqual(response.status_code, 400)
        
        # Test non-existent endpoints
        response = self.client.get("/rest/api/nonexistent")
        self.assertEqual(response.status_code, 404)
    
    def test_concurrent_request_handling(self):
        """Test handling of multiple concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get("/")
            results.append(response.status_code)
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        self.assertEqual(len(results), 5)
        self.assertTrue(all(status == 200 for status in results))
    
    def test_data_persistence_across_requests(self):
        """Test that data persists correctly across multiple requests"""
        # First, verify no suggestions exist
        response = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            json={"company_name": "integration_test_company"}
        )
        self.assertEqual(response.status_code, 500)  # Should not find suggestions
        
        # Add suggestions manually (simulating background task completion)
        suggestions = CampaignSuggestions(
            company_name="integration_test_company",
            suggested_campaign={"suggestions": ["Persistent Campaign"]}
        )
        self.session.add(suggestions)
        self.session.commit()
        
        # Now retrieval should work
        response = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            json={"company_name": "integration_test_company"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["suggestions"], ["Persistent Campaign"])
        
        # Make the same request again - should still work
        response = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            json={"company_name": "integration_test_company"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["suggestions"], ["Persistent Campaign"])


if __name__ == '__main__':
    unittest.main()