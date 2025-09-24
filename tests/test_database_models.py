import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.sqlite_conn import Base, CompanyProfile, CampaignSuggestions, JobQueue, get_session


class TestSQLiteConnection(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        cls.test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=cls.test_engine)
        cls.TestSession = sessionmaker(bind=cls.test_engine)
    
    def setUp(self):
        """Set up test session"""
        self.session = self.TestSession()
    
    def tearDown(self):
        """Clean up test session"""
        self.session.rollback()
        self.session.close()
    
    def test_company_profile_creation(self):
        """Test creating a CompanyProfile instance"""
        # Execute
        company = CompanyProfile(
            company_name="test_company",
            brand_voice="Professional and innovative",
            target_audience="Tech enthusiasts",
            product_category="Technology",
            style_guide="Modern design",
            recent_campaign_metrics={"ctr": 0.05, "conversion_rate": 0.02}
        )
        
        # Assert
        self.assertIsNotNone(company.id)  # Should have auto-generated UUID
        self.assertEqual(company.company_name, "test_company")
        self.assertEqual(company.brand_voice, "Professional and innovative")
        self.assertEqual(company.target_audience, "Tech enthusiasts")
        self.assertEqual(company.product_category, "Technology")
        self.assertEqual(company.style_guide, "Modern design")
        self.assertEqual(company.recent_campaign_metrics, {"ctr": 0.05, "conversion_rate": 0.02})
    
    def test_company_profile_database_operations(self):
        """Test CompanyProfile database operations"""
        # Create
        company = CompanyProfile(
            company_name="db_test_company",
            brand_voice="Friendly",
            target_audience="General public",
            product_category="Consumer goods",
            style_guide="Colorful and fun",
            recent_campaign_metrics={"impressions": 10000}
        )
        
        self.session.add(company)
        self.session.commit()
        
        # Read
        retrieved_company = self.session.query(CompanyProfile).filter_by(
            company_name="db_test_company"
        ).first()
        
        # Assert
        self.assertIsNotNone(retrieved_company)
        self.assertEqual(retrieved_company.company_name, "db_test_company")
        self.assertEqual(retrieved_company.brand_voice, "Friendly")
        self.assertEqual(retrieved_company.recent_campaign_metrics, {"impressions": 10000})
        
        # Update
        retrieved_company.brand_voice = "Updated voice"
        self.session.commit()
        
        updated_company = self.session.query(CompanyProfile).filter_by(
            company_name="db_test_company"
        ).first()
        self.assertEqual(updated_company.brand_voice, "Updated voice")
        
        # Delete
        self.session.delete(updated_company)
        self.session.commit()
        
        deleted_company = self.session.query(CompanyProfile).filter_by(
            company_name="db_test_company"
        ).first()
        self.assertIsNone(deleted_company)
    
    def test_campaign_suggestions_creation(self):
        """Test creating a CampaignSuggestions instance"""
        # Execute
        suggestions = CampaignSuggestions(
            company_name="test_company",
            suggested_campaign={
                "suggestions": ["Campaign 1", "Campaign 2"],
                "budget_range": "$10k-$50k"
            }
        )
        
        # Assert
        self.assertEqual(suggestions.company_name, "test_company")
        self.assertEqual(suggestions.suggested_campaign["suggestions"], ["Campaign 1", "Campaign 2"])
        self.assertEqual(suggestions.suggested_campaign["budget_range"], "$10k-$50k")
        self.assertIsNotNone(suggestions.last_updated)  # Should have default datetime
    
    def test_campaign_suggestions_database_operations(self):
        """Test CampaignSuggestions database operations"""
        # Create
        suggestions = CampaignSuggestions(
            company_name="suggestions_test_company",
            suggested_campaign={
                "suggestions": ["Social media campaign", "Email marketing"],
                "priority": "high"
            }
        )
        
        self.session.add(suggestions)
        self.session.commit()
        
        # Read
        retrieved_suggestions = self.session.query(CampaignSuggestions).filter_by(
            company_name="suggestions_test_company"
        ).first()
        
        # Assert
        self.assertIsNotNone(retrieved_suggestions)
        self.assertEqual(retrieved_suggestions.company_name, "suggestions_test_company")
        self.assertEqual(retrieved_suggestions.suggested_campaign["priority"], "high")
        self.assertIsInstance(retrieved_suggestions.last_updated, datetime)
        
        # Test ordering by last_updated
        newer_suggestions = CampaignSuggestions(
            company_name="suggestions_test_company",
            suggested_campaign={"suggestions": ["New campaign"]}
        )
        self.session.add(newer_suggestions)
        self.session.commit()
        
        latest_suggestions = self.session.query(CampaignSuggestions).filter_by(
            company_name="suggestions_test_company"
        ).order_by(CampaignSuggestions.last_updated.desc()).first()
        
        self.assertEqual(latest_suggestions.suggested_campaign["suggestions"], ["New campaign"])
    
    def test_job_queue_creation(self):
        """Test creating a JobQueue instance"""
        # Execute
        job = JobQueue(
            company_name="test_company",
            status="pending",
            created_at=datetime.now(),
            expires_at=datetime.now()
        )
        
        # Assert
        self.assertEqual(job.company_name, "test_company")
        self.assertEqual(job.status, "pending")
        self.assertIsInstance(job.created_at, datetime)
        self.assertIsInstance(job.expires_at, datetime)
    
    def test_job_queue_database_operations(self):
        """Test JobQueue database operations"""
        # Create
        now = datetime.now()
        job = JobQueue(
            company_name="job_test_company",
            status="in_progress",
            created_at=now,
            expires_at=now
        )
        
        self.session.add(job)
        self.session.commit()
        
        # Read
        retrieved_job = self.session.query(JobQueue).filter_by(
            company_name="job_test_company"
        ).first()
        
        # Assert
        self.assertIsNotNone(retrieved_job)
        self.assertEqual(retrieved_job.company_name, "job_test_company")
        self.assertEqual(retrieved_job.status, "in_progress")
        
        # Test status updates
        retrieved_job.status = "completed"
        self.session.commit()
        
        updated_job = self.session.query(JobQueue).filter_by(
            company_name="job_test_company"
        ).first()
        self.assertEqual(updated_job.status, "completed")
        
        # Test ordering by created_at
        newer_job = JobQueue(
            company_name="job_test_company",
            status="new_job",
            created_at=datetime.now(),
            expires_at=datetime.now()
        )
        self.session.add(newer_job)
        self.session.commit()
        
        latest_job = self.session.query(JobQueue).filter_by(
            company_name="job_test_company"
        ).order_by(JobQueue.created_at.desc()).first()
        
        self.assertEqual(latest_job.status, "new_job")
    
    def test_company_profile_unique_constraint(self):
        """Test that company_name has unique constraint"""
        # Create first company
        company1 = CompanyProfile(
            company_name="unique_test_company",
            brand_voice="Voice 1"
        )
        self.session.add(company1)
        self.session.commit()
        
        # Try to create second company with same name
        company2 = CompanyProfile(
            company_name="unique_test_company",
            brand_voice="Voice 2"
        )
        self.session.add(company2)
        
        # Should raise an integrity error
        with self.assertRaises(Exception):  # SQLAlchemy IntegrityError
            self.session.commit()
    
    def test_json_field_operations(self):
        """Test JSON field operations"""
        # Test complex JSON in CompanyProfile
        complex_metrics = {
            "campaigns": [
                {"name": "Summer 2023", "ctr": 0.05, "conversions": 150},
                {"name": "Fall 2023", "ctr": 0.07, "conversions": 200}
            ],
            "total_budget": 100000,
            "roi": 2.5,
            "demographics": {
                "age_groups": {"18-25": 30, "26-35": 45, "36-50": 25},
                "locations": ["US", "CA", "UK"]
            }
        }
        
        company = CompanyProfile(
            company_name="json_test_company",
            recent_campaign_metrics=complex_metrics
        )
        
        self.session.add(company)
        self.session.commit()
        
        # Retrieve and verify JSON integrity
        retrieved_company = self.session.query(CompanyProfile).filter_by(
            company_name="json_test_company"
        ).first()
        
        self.assertEqual(
            retrieved_company.recent_campaign_metrics["total_budget"], 
            100000
        )
        self.assertEqual(
            len(retrieved_company.recent_campaign_metrics["campaigns"]), 
            2
        )
        self.assertEqual(
            retrieved_company.recent_campaign_metrics["demographics"]["age_groups"]["26-35"], 
            45
        )
    
    def test_get_session_generator(self):
        """Test the get_session generator function"""
        # This test verifies that get_session works as expected
        session_generator = get_session()
        session = next(session_generator)
        
        # Should return a valid session
        self.assertIsNotNone(session)
        
        # Should be able to query
        result = session.query(CompanyProfile).all()
        self.assertIsInstance(result, list)
        
        # Clean up
        try:
            next(session_generator)  # Should close the session
        except StopIteration:
            pass  # Expected behavior


if __name__ == '__main__':
    unittest.main()