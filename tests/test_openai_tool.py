import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.tools.openai_tool import OpenAITool, CampaignLLMResponse
from app.db.sqlite_conn import CompanyProfile, CampaignSuggestions


class TestOpenAITool(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key'
        })
        self.env_patcher.start()
        
        self.sample_company_profile = CompanyProfile(
            company_name="test_company",
            brand_voice="Professional and innovative",
            target_audience="Tech enthusiasts aged 25-45",
            product_category="Technology",
            style_guide="Modern, clean, minimalist design",
            recent_campaign_metrics={"ctr": 0.05, "conversion_rate": 0.02}
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
    
    @patch('app.agent.tools.openai_tool.OpenAI')
    def test_init_success(self, mock_openai_class):
        """Test successful initialization of OpenAITool"""
        # Execute
        tool = OpenAITool()
        
        # Assert
        self.assertEqual(tool.OPENAI_API_KEY, "test-api-key")
        self.assertEqual(tool.MODEL_NAME, "gpt-5-nano")
        mock_openai_class.assert_called_once_with(api_key="test-api-key")
    
    def test_init_missing_api_key(self):
        """Test initialization failure when API key is missing"""
        # Setup - remove API key from environment
        with patch.dict(os.environ, {}, clear=True):
            # Execute & Assert
            with self.assertRaises(ValueError) as context:
                OpenAITool()
            
            self.assertEqual(str(context.exception), "OPENAI_API_KEY environment variable not set.")
    
    @patch('app.agent.tools.openai_tool.OpenAI')
    def test_openai_call_success(self, mock_openai_class):
        """Test successful OpenAI API call"""
        # Setup
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_parsed_output = CampaignLLMResponse(
            company_name="test_company",
            suggestions=["Campaign idea 1", "Campaign idea 2"]
        )
        mock_response.output_parsed = mock_parsed_output
        mock_client.responses.parse.return_value = mock_response
        
        tool = OpenAITool()
        
        # Execute
        result = tool._openai_call("Test prompt")
        
        # Assert
        self.assertEqual(result, mock_parsed_output)
        mock_client.responses.parse.assert_called_once_with(
            model="gpt-5-nano",
            input=[
                {
                    "role": "system",
                    "content": "You are an expert consultant that helps Companies achieve their desired campaign goals by generating marketing campaign ideas based on company profiles and the goal the company provides."
                },
                {
                    "role": "user",
                    "content": "Test prompt"
                }
            ],
            text_format=CampaignLLMResponse
        )
    
    @patch('app.agent.tools.openai_tool.OpenAI')
    def test_openai_call_with_custom_parameters(self, mock_openai_class):
        """Test OpenAI API call with custom parameters"""
        # Setup
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_parsed_output = CampaignLLMResponse(
            company_name="test_company",
            suggestions=["Campaign idea 1"]
        )
        mock_response.output_parsed = mock_parsed_output
        mock_client.responses.parse.return_value = mock_response
        
        tool = OpenAITool()
        
        # Custom BaseModel for testing
        from pydantic import BaseModel
        class CustomResponse(BaseModel):
            message: str
        
        # Execute
        result = tool._openai_call(
            "Test prompt",
            text_structure=CustomResponse,
            temperature=0.5,
            seed=123,
            top_p=0.9
        )
        
        # Assert
        self.assertEqual(result, mock_parsed_output)
        # Note: The current implementation doesn't use temperature, seed, top_p parameters
        # This test verifies the method signature accepts them
    
    @patch('app.agent.tools.openai_tool.OpenAI')
    def test_generate_campaign_ideas_success(self, mock_openai_class):
        """Test successful campaign ideas generation"""
        # Setup
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_llm_response = CampaignLLMResponse(
            company_name="test_company",
            suggestions=[
                "Social media campaign focusing on innovation",
                "Influencer partnerships with tech reviewers",
                "Interactive product demos at tech conferences"
            ]
        )
        mock_response.output_parsed = mock_llm_response
        mock_client.responses.parse.return_value = mock_response
        
        tool = OpenAITool()
        
        # Execute
        result = tool.generate_campaign_ideas(self.sample_company_profile, "Increase brand awareness")
        
        # Assert
        self.assertIsInstance(result, CampaignSuggestions)
        self.assertEqual(result.company_name, "test_company")
        self.assertEqual(result.suggested_campaign["suggestions"], mock_llm_response.suggestions)
        
        # Verify the prompt construction
        call_args = mock_client.responses.parse.call_args
        user_content = call_args[1]["input"][1]["content"]
        
        self.assertIn("Increase brand awareness", user_content)
        self.assertIn("test_company", user_content)
        self.assertIn("Professional and innovative", user_content)
        self.assertIn("Tech enthusiasts aged 25-45", user_content)
        self.assertIn("Technology", user_content)
        self.assertIn("Modern, clean, minimalist design", user_content)
    
    @patch('app.agent.tools.openai_tool.OpenAI')
    def test_generate_campaign_ideas_api_error(self, mock_openai_class):
        """Test campaign ideas generation with API error"""
        # Setup
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.responses.parse.side_effect = Exception("API Error")
        
        tool = OpenAITool()
        
        # Execute & Assert
        with self.assertRaises(Exception) as context:
            tool.generate_campaign_ideas(self.sample_company_profile, "Increase brand awareness")
        
        self.assertEqual(str(context.exception), "API Error")
    
    @patch('app.agent.tools.openai_tool.OpenAI')
    def test_prompt_construction(self, mock_openai_class):
        """Test that the prompt is constructed correctly"""
        # Setup
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_llm_response = CampaignLLMResponse(
            company_name="test_company",
            suggestions=["Campaign 1"]
        )
        mock_response.output_parsed = mock_llm_response
        mock_client.responses.parse.return_value = mock_response
        
        tool = OpenAITool()
        
        # Execute
        tool.generate_campaign_ideas(self.sample_company_profile, "Test Goal")
        
        # Assert - check prompt contains all required elements
        call_args = mock_client.responses.parse.call_args
        user_content = call_args[1]["input"][1]["content"]
        
        expected_elements = [
            "Generate campaign ideas for the following campaign goal: Test Goal",
            "Company Name: test_company",
            "brand_voice: Professional and innovative",
            "target_audience: Tech enthusiasts aged 25-45",
            "product_category: Technology",
            "style_guide: Modern, clean, minimalist design",
            "recent_campaign_metrics: {'ctr': 0.05, 'conversion_rate': 0.02}"
        ]
        
        for element in expected_elements:
            self.assertIn(element, user_content)
    
    def test_campaign_llm_response_model(self):
        """Test the CampaignLLMResponse Pydantic model"""
        # Execute
        response = CampaignLLMResponse(
            company_name="test_company",
            suggestions=["Suggestion 1", "Suggestion 2"]
        )
        
        # Assert
        self.assertEqual(response.company_name, "test_company")
        self.assertEqual(response.suggestions, ["Suggestion 1", "Suggestion 2"])
        self.assertEqual(len(response.suggestions), 2)
    
    def test_campaign_llm_response_validation(self):
        """Test CampaignLLMResponse model validation"""
        # Test missing required fields
        with self.assertRaises(Exception):
            CampaignLLMResponse(company_name="test")  # Missing suggestions
        
        with self.assertRaises(Exception):
            CampaignLLMResponse(suggestions=["test"])  # Missing company_name


if __name__ == '__main__':
    unittest.main()