import pytest
import sys
import os
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.sqlite_conn import Base, get_session
from main import app

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_campaigns.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_campaigns.db"):
        os.remove("./test_campaigns.db")

@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def test_client(test_session):
    """Create a test client with dependency override"""
    def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_company_profile():
    """Sample company profile for testing"""
    return {
        "company_name": "test_company",
        "brand_voice": "Professional and innovative",
        "target_audience": "Tech enthusiasts aged 25-45",
        "product_category": "Technology",
        "style_guide": "Modern, clean, minimalist design",
        "recent_campaign_metrics": {"ctr": 0.05, "conversion_rate": 0.02}
    }

@pytest.fixture
def sample_campaign_request():
    """Sample campaign request for testing"""
    return {
        "company_name": "test_company",
        "campaign_goal": "Increase brand awareness",
        "email": "test@example.com"
    }

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI response for testing"""
    return {
        "company_name": "test_company",
        "suggestions": [
            "Social media campaign focusing on innovation",
            "Influencer partnerships with tech reviewers",
            "Interactive product demos at tech conferences"
        ]
    }

@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing"""
    env_vars = {
        "OPENAI_API_KEY": "test-api-key",
        "EMAIL_USER": "test@example.com",
        "EMAIL_APP_PASSWORD": "test-password",
        "EMAIL_SERVER": "smtp.gmail.com",
        "EMAIL_PORT": "587"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars