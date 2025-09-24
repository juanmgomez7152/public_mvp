from app.db.sqlite_conn import SessionLocal, CompanyProfile,CampaignSuggestions,JobQueue
from datetime import datetime, timedelta
class DBTool:
    def __init__(self):
        self.session = SessionLocal()

    def get_company_profile(self, company_name: str) -> dict:
        co_profile = self.session.query(CompanyProfile).filter_by(company_name=company_name).first()
        return co_profile

    def save_campaign_suggestion(self, campaign_suggestion: CampaignSuggestions, curr_time: datetime = None) -> None:
        if curr_time is None:
            curr_time = datetime.now()
        campaign_suggestion.last_updated = curr_time
        
        self.session.add(campaign_suggestion)
        self.session.commit()
    
    def get_campaign_suggestions(self, company_name: str) -> CampaignSuggestions:
        suggestions = self.session.query(CampaignSuggestions).filter_by(company_name=company_name).order_by(CampaignSuggestions.last_updated.desc()).first()
        return suggestions

    def load_job(self, company_name: str) -> None:
        job = JobQueue(
            company_name=company_name,
            status="working",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7)
        )
        self.session.add(job)
        self.session.commit()
        
    def update_job_status(self, company_name: str, status: str) -> None:
        job = self.session.query(JobQueue).filter_by(company_name=company_name).order_by(JobQueue.created_at.desc()).first()
        if job:
            job.status = status
            job.updated_at = datetime.now()
            self.session.commit()
        
    def extract_latest_status(self, company_name: str) -> JobQueue:
        job = self.session.query(JobQueue).filter_by(company_name=company_name).order_by(JobQueue.created_at.desc()).first()
        status = job.status
        return status

    def close(self):
        self.session.close()