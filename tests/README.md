# Testing Documentation

## Overview

This test suite provides comprehensive testing for the Omnicom MVP project. The tests are organized into unit tests and integration tests to ensure all components work correctly both in isolation and together.

## Test Structure

```
tests/
├── __init__.py                          # Package initialization
├── conftest.py                          # pytest fixtures and configuration
├── run_tests.py                         # Test runner script
├── test_requirements.txt                # Testing dependencies
├── README.md                           # This documentation
│
├── Unit Tests:
├── test_campaign_agent.py              # CampaignAgent class tests
├── test_db_tool.py                     # DBTool class tests
├── test_openai_tool.py                 # OpenAITool class tests
├── test_campaign_agent_endpoints.py    # Campaign agent API tests
├── test_campaign_endpoints.py          # Campaign API tests
├── test_database_models.py             # Database model tests
├── test_main.py                        # Main application tests
│
└── Integration Tests:
└── test_integration.py                 # End-to-end workflow tests
```

## Running Tests

### Quick Start

```bash
# Run all tests
python tests/run_tests.py

# Run only unit tests
python tests/run_tests.py --unit

# Run only integration tests
python tests/run_tests.py --integration

# Run with verbose output
python tests/run_tests.py --verbose

# Run with coverage report
python tests/run_tests.py --coverage
```

### Using unittest directly

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_campaign_agent

# Run specific test class
python -m unittest tests.test_campaign_agent.TestCampaignAgent

# Run specific test method
python -m unittest tests.test_campaign_agent.TestCampaignAgent.test_alert_completion_success
```

### Using pytest (optional)

If you install pytest:

```bash
# Install pytest
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_campaign_agent.py

# Run with verbose output
pytest tests/ -v
```

## Test Categories

### Unit Tests

Test individual components in isolation:

- **test_campaign_agent.py**: Tests the main CampaignAgent orchestration logic
- **test_db_tool.py**: Tests database operations and data access layer
- **test_openai_tool.py**: Tests OpenAI integration and LLM interactions
- **test_campaign_agent_endpoints.py**: Tests campaign agent API endpoints
- **test_campaign_endpoints.py**: Tests campaign retrieval API endpoints
- **test_database_models.py**: Tests SQLAlchemy models and database schema
- **test_main.py**: Tests main application setup and routing

### Integration Tests

Test complete workflows:

- **test_integration.py**: Tests end-to-end scenarios including API calls, database operations, and component interactions

## Test Features

### Mocking Strategy

The tests use extensive mocking to:
- Isolate components under test
- Avoid external dependencies (OpenAI API, email servers)
- Control test data and scenarios
- Ensure tests run quickly and reliably

### Database Testing

- Uses SQLite in-memory databases for fast, isolated tests
- Creates fresh database instances for each test
- Tests both model definitions and database operations
- Verifies data consistency and constraints

### API Testing

- Uses FastAPI's TestClient for endpoint testing
- Tests request/response formats
- Validates error handling and status codes
- Checks authentication and authorization flows

### Async Testing

- Properly handles async/await patterns
- Uses AsyncMock for async method mocking
- Tests background task scenarios

## Coverage Reports

When running with coverage, the system generates:
- Console coverage report showing line coverage percentages
- HTML coverage report in `htmlcov/index.html` for detailed analysis
- Coverage data file (`.coverage`) for additional tooling

## Environment Setup

### Required Environment Variables for Testing

Most tests use mocked values, but for integration tests you may want:

```bash
# OpenAI (mocked in tests, but required for structure)
OPENAI_API_KEY=test-key

# Email (mocked in tests, but required for structure)
EMAIL_USER=test@example.com
EMAIL_APP_PASSWORD=test-password
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
```

### Test Database

Tests use SQLite in-memory databases, so no external database setup is required.

## Writing New Tests

### Adding Unit Tests

1. Create test file following naming convention: `test_[module_name].py`
2. Import the module under test
3. Use unittest.TestCase as base class
4. Mock external dependencies
5. Test both success and failure scenarios

Example:
```python
import unittest
from unittest.mock import Mock, patch
from app.your_module import YourClass

class TestYourClass(unittest.TestCase):
    def setUp(self):
        self.mock_dependency = Mock()
        self.instance = YourClass(self.mock_dependency)
    
    def test_your_method_success(self):
        # Setup
        self.mock_dependency.method.return_value = "expected"
        
        # Execute
        result = self.instance.your_method("input")
        
        # Assert
        self.assertEqual(result, "expected")
        self.mock_dependency.method.assert_called_once_with("input")
```

### Adding Integration Tests

Add test methods to `test_integration.py` that test complete workflows:

```python
def test_your_integration_scenario(self):
    # Test complete flow from API call to database
    response = self.client.post("/api/endpoint", json={"data": "test"})
    self.assertEqual(response.status_code, 200)
    
    # Verify database state
    record = self.session.query(Model).first()
    self.assertIsNotNone(record)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Mock Issues**: Verify mock paths match actual import paths
3. **Async Tests**: Use AsyncMock for async methods
4. **Database Tests**: Ensure test database is properly cleaned up
5. **Coverage Issues**: Make sure all code paths are tested

### Debugging Tests

```bash
# Run single test with full output
python -m unittest tests.test_module.TestClass.test_method -v

# Add print statements or use debugger
import pdb; pdb.set_trace()  # In test code

# Check test output
python tests/run_tests.py --verbose
```

## Continuous Integration

To run tests in CI/CD pipelines:

```yaml
# Example GitHub Actions configuration
- name: Run tests
  run: |
    python -m pip install -r requirements.txt
    python -m pip install -r tests/test_requirements.txt
    python tests/run_tests.py --coverage
```

## Best Practices

1. **Test Naming**: Use descriptive test method names
2. **Test Structure**: Follow Arrange-Act-Assert pattern
3. **Mocking**: Mock at the boundary of the unit under test
4. **Data**: Use realistic but minimal test data
5. **Coverage**: Aim for high coverage but focus on critical paths
6. **Performance**: Keep tests fast by using mocks and in-memory databases
7. **Independence**: Each test should be independent and idempotent

## Metrics and Goals

- **Coverage Target**: >90% line coverage
- **Test Speed**: Full test suite should complete in <30 seconds
- **Test Count**: Aim for 3-5 tests per public method/function
- **Integration Coverage**: Test all major user workflows

## Support

For questions about the test suite:
1. Check this documentation
2. Review existing test examples
3. Run tests with verbose output for debugging
4. Check the test output and error messages