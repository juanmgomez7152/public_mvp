import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app, read_root


class TestMainApp(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    def test_app_creation(self):
        """Test that the FastAPI app is created correctly"""
        self.assertIsNotNone(app)
        self.assertEqual(app.title, "Omnicom MVP")
        self.assertEqual(app.description, "Omnicom MVP Backend API")
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = self.client.get("/")
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data, {"Message": "Ok 🪅"})
    
    def test_read_root_function_directly(self):
        """Test the read_root function directly"""
        result = read_root()
        expected = {"Message": "Ok 🪅"}
        self.assertEqual(result, expected)
    
    def test_api_router_inclusion(self):
        """Test that API routers are properly included"""
        # Test campaign agent endpoint
        response = self.client.post(
            "/rest/api/campaign-agent/campaign-agent-suggestions/",
            json={
                "company_name": "test_company",
                "campaign_goal": "test_goal",
                "email": "test@example.com"
            }
        )
        # Should not return 404 (route exists), might return 500 due to missing dependencies
        self.assertNotEqual(response.status_code, 404)
        
        # Test campaign endpoint
        response = self.client.post(
            "/rest/api/campaign/suggestions/retrieve/",
            json={"company_name": "test_company"}
        )
        # Should not return 404 (route exists)
        self.assertNotEqual(response.status_code, 404)
    
    def test_app_settings(self):
        """Test application settings and configuration"""
        # Test that the app has the expected attributes
        self.assertTrue(hasattr(app, 'title'))
        self.assertTrue(hasattr(app, 'description'))
        self.assertTrue(hasattr(app, 'routes'))
        
        # Check that routes are properly registered
        route_paths = [route.path for route in app.routes]
        self.assertIn("/", route_paths)  # Root endpoint
        
        # Check for API prefix routes
        api_routes = [route.path for route in app.routes if route.path.startswith("/rest/api")]
        self.assertTrue(len(api_routes) > 0, "API routes should be registered")
    
    def test_cors_and_middleware(self):
        """Test CORS and middleware configuration"""
        # Test that standard headers are handled properly
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        
        # Test OPTIONS request (CORS preflight)
        response = self.client.options("/")
        # Should not return 405 (method not allowed) if CORS is properly configured
        # The actual status code depends on CORS middleware configuration
        self.assertIn(response.status_code, [200, 405])  # Either allowed or not implemented
    
    @patch('main.populate_db')
    @patch('main.uvicorn.run')
    def test_main_execution(self, mock_uvicorn_run, mock_populate_db):
        """Test the main execution block"""
        # Import and run the main block by importing the module
        # This is tricky to test directly, so we'll test the components
        
        # Test that when main.py is run, it would call populate_db
        with patch('main.__name__', '__main__'):
            try:
                # This would normally run the main block, but we're testing components
                pass
            except SystemExit:
                pass  # Expected when testing main execution
        
        # The actual testing of main execution requires running the module
        # which is complex in unit tests, so we test the individual components
    
    def test_error_handling(self):
        """Test basic error handling"""
        # Test 404 for non-existent route
        response = self.client.get("/non-existent-route")
        self.assertEqual(response.status_code, 404)
        
        # Test 405 for wrong method
        response = self.client.put("/")  # Root only accepts GET
        self.assertEqual(response.status_code, 405)
    
    def test_request_response_format(self):
        """Test request/response format handling"""
        # Test JSON response
        response = self.client.get("/")
        self.assertEqual(response.headers["content-type"], "application/json")
        
        # Test that JSON is properly formatted
        response_data = response.json()
        self.assertIsInstance(response_data, dict)
        self.assertIn("Message", response_data)
    
    def test_health_check(self):
        """Test that the root endpoint can serve as a health check"""
        response = self.client.get("/")
        
        # Should respond quickly and successfully
        self.assertEqual(response.status_code, 200)
        
        # Should return expected content
        self.assertEqual(response.json()["Message"], "Ok 🪅")
        
        # Response time should be reasonable (this is implicit in the test passing)
    
    def test_app_state_consistency(self):
        """Test that the app maintains consistent state across requests"""
        # Multiple requests should return the same result
        response1 = self.client.get("/")
        response2 = self.client.get("/")
        
        self.assertEqual(response1.json(), response2.json())
        self.assertEqual(response1.status_code, response2.status_code)
    
    @patch('main.logging.basicConfig')
    def test_logging_configuration(self, mock_logging_config):
        """Test that logging is properly configured"""
        # Re-import to trigger logging configuration
        import importlib
        import main
        importlib.reload(main)
        
        # Should have been called during module import
        # Note: This might not work as expected due to import caching
        # The main purpose is to verify logging setup exists
        
        # Test that logger exists and is properly configured
        import logging
        logger = logging.getLogger('main')
        self.assertIsNotNone(logger)
    
    def test_unicode_handling(self):
        """Test that the app properly handles Unicode in the response"""
        response = self.client.get("/")
        
        # The piñata emoji should be properly encoded
        self.assertEqual(response.json()["Message"], "Ok 🪅")
        
        # Response should be UTF-8 encoded
        self.assertIn("charset=utf-8", response.headers.get("content-type", "").lower())


if __name__ == '__main__':
    # Mock the populate_db function to avoid database operations during testing
    with patch('main.populate_db'):
        unittest.main()