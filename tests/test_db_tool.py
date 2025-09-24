import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.tools.db_tool import DBTool
from app.db.sqlite_conn import CompanyProfile, CampaignSuggestions, JobQueue


class TestDBTool(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.db_tool = DBTool(self.mock_session)
        
        # Sample data
        self.sample_company = CompanyProfile(
            id="test-id",
            company_name="test_company",
            brand_voice="Professional",
            target_audience="Tech enthusiasts",
            product_category="Technology",
            style_guide="Modern design",
            recent_campaign_metrics={"ctr": 0.05}
        )
        
        self.sample_suggestion = CampaignSuggestions(
            id=1,
            company_name="test_company",
            suggested_campaign={"suggestions": ["Campaign 1", "Campaign 2"]},
            last_updated=datetime.now()
        )
        
        self.sample_job = JobQueue(
            id=1,
            company_name="test_company",
            status="working",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7)
        )
    
    async def test_get_company_profile_success(self):
        """Test successful company profile retrieval"""
        # Setup
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = self.sample_company
        
        # Execute
        result = await self.db_tool.get_company_profile("test_company")
        
        # Assert
        self.assertEqual(result, self.sample_company)
        self.mock_session.query.assert_called_once_with(CompanyProfile)
        self.mock_session.query.return_value.filter_by.assert_called_once_with(company_name="test_company")
    
    async def test_get_company_profile_not_found(self):
        """Test company profile retrieval when not found"""
        # Setup
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Execute
        result = await self.db_tool.get_company_profile("nonexistent_company")
        
        # Assert
        self.assertIsNone(result)
    
    async def test_save_campaign_suggestion_with_custom_time(self):
        """Test saving campaign suggestion with custom timestamp"""
        # Setup
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        
        # Execute
        await self.db_tool.save_campaign_suggestion(self.sample_suggestion, custom_time)
        
        # Assert
        self.assertEqual(self.sample_suggestion.last_updated, custom_time)
        self.mock_session.add.assert_called_once_with(self.sample_suggestion)
        self.mock_session.commit.assert_called_once()
    
    async def test_save_campaign_suggestion_with_default_time(self):
        """Test saving campaign suggestion with default timestamp"""
        # Setup
        original_time = self.sample_suggestion.last_updated
        
        # Execute
        with patch('app.agent.tools.db_tool.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            await self.db_tool.save_campaign_suggestion(self.sample_suggestion)
        
        # Assert
        self.assertEqual(self.sample_suggestion.last_updated, mock_now)
        self.mock_session.add.assert_called_once_with(self.sample_suggestion)
        self.mock_session.commit.assert_called_once()
    
    async def test_get_campaign_suggestions_success(self):
        """Test successful campaign suggestions retrieval"""
        # Setup
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = self.sample_suggestion
        
        # Execute
        result = await self.db_tool.get_campaign_suggestions("test_company")
        
        # Assert
        self.assertEqual(result, self.sample_suggestion)
        self.mock_session.query.assert_called_once_with(CampaignSuggestions)
        self.mock_session.query.return_value.filter_by.assert_called_once_with(company_name="test_company")
    
    async def test_get_campaign_suggestions_not_found(self):
        """Test campaign suggestions retrieval when not found"""
        # Setup
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
        
        # Execute
        result = await self.db_tool.get_campaign_suggestions("nonexistent_company")
        
        # Assert
        self.assertIsNone(result)
    
    async def test_load_job(self):
        """Test loading a new job"""
        # Execute
        with patch('app.agent.tools.db_tool.datetime') as mock_datetime, \
             patch('app.agent.tools.db_tool.timedelta') as mock_timedelta, \
             patch('app.agent.tools.db_tool.JobQueue') as mock_job_queue:
            
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_expires = datetime(2023, 1, 8, 12, 0, 0)
            mock_delta = timedelta(days=7)
            
            mock_datetime.now.return_value = mock_now
            mock_timedelta.return_value = mock_delta
            mock_job_instance = Mock()
            mock_job_queue.return_value = mock_job_instance
            
            await self.db_tool.load_job("test_company")
            
            # Assert
            mock_job_queue.assert_called_once_with(
                company_name="test_company",
                status="working",
                created_at=mock_now,
                expires_at=mock_now + mock_delta
            )
            self.mock_session.add.assert_called_once_with(mock_job_instance)
            self.mock_session.commit.assert_called_once()
    
    async def test_update_job_status_success(self):
        """Test successful job status update"""
        # Setup
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = self.sample_job
        
        # Execute
        with patch('app.agent.tools.db_tool.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            await self.db_tool.update_job_status("test_company", "completed")
            
            # Assert
            self.assertEqual(self.sample_job.status, "completed")
            self.assertEqual(self.sample_job.updated_at, mock_now)
            self.mock_session.commit.assert_called_once()
    
    async def test_update_job_status_job_not_found(self):
        """Test job status update when job not found"""
        # Setup
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
        
        # Execute
        await self.db_tool.update_job_status("nonexistent_company", "completed")
        
        # Assert
        self.mock_session.commit.assert_not_called()
    
    async def test_extract_latest_status_success(self):
        """Test successful latest status extraction"""
        # Setup
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = self.sample_job
        
        # Execute
        result = await self.db_tool.extract_latest_status("test_company")
        
        # Assert
        self.assertEqual(result, self.sample_job.status)
        self.mock_session.query.assert_called_once_with(JobQueue)
        self.mock_session.query.return_value.filter_by.assert_called_once_with(company_name="test_company")
    
    def test_session_management_with_provided_session(self):
        """Test that provided session is used and not closed"""
        # Setup
        provided_session = Mock()
        db_tool = DBTool(provided_session)
        
        # Assert
        self.assertTrue(db_tool.session_provided)
        self.assertEqual(db_tool.session, provided_session)
    
    @patch('app.agent.tools.db_tool.sessionmaker')
    @patch('app.agent.tools.db_tool.engine')
    def test_session_management_without_provided_session(self, mock_engine, mock_sessionmaker):
        """Test that new session is created when none provided"""
        # Setup
        mock_session_instance = Mock()
        mock_sessionmaker.return_value.return_value = mock_session_instance
        
        # Execute
        db_tool = DBTool()
        
        # Assert
        self.assertFalse(db_tool.session_provided)
        mock_sessionmaker.assert_called_once_with(autocommit=False, autoflush=False, bind=mock_engine)


if __name__ == '__main__':
    unittest.main()