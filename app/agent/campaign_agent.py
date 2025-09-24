import logging
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.agent.tools.db_tool import DBTool
from app.agent.tools.openai_tool import OpenAITool
from app.db.sqlite_conn import CompanyProfile, CampaignSuggestions
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
class CampaignAgent:
    def __init__(self, db: Session):
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_APP_PASSWORD")
        self.email_server = os.getenv("EMAIL_SERVER", "smtp.gmail.com")
        self.email_port = int(os.getenv("EMAIL_PORT", "587"))
        self.db_tool = DBTool(db)
        self.llm_toolkit = OpenAITool()

    async def _extract_profile(self, company:str) -> CompanyProfile:
        profile = await self.db_tool.get_company_profile(company)
        return profile
        
    
    async def _generate_suggestions(self, profile: CompanyProfile, goal: str) -> CampaignSuggestions:
        suggestion_results = self.llm_toolkit.generate_campaign_ideas(profile, goal)
        return suggestion_results

    async def _store_suggestions(self, company:str,suggestion_results:CampaignSuggestions, email:str) -> None:
        await self.db_tool.save_campaign_suggestion(suggestion_results)
        await self.db_tool.update_job_status(company, "completed")
        if not self._alert_completion(company, email):
            raise Exception("Failed to send email notification.")

    def _alert_completion(self,company:str, email:str) -> None:
        try:
            # Check if credentials are available
            if not self.email_user or not self.email_password or not email:
                logger.error("Email credentials not configured. Cannot send notification.")
                return False
                
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Your Campaign Suggestions are Ready!"
            message["From"] = self.email_user
            message["To"] = email

            body = f"Your campaign suggestions for {company} are ready. Please check your dashboard. Thank you!"
            message.attach(MIMEText(body, "plain"))
            
            # Connect to server and send
            with smtplib.SMTP(self.email_server, self.email_port) as server:
                server.starttls()  # Secure the connection
                server.login(self.email_user, self.email_password)
                server.send_message(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
        
    async def get_campaign_suggestions(self, company_name: str) -> CampaignSuggestions:
        suggestions = await self.db_tool.get_campaign_suggestions(company_name)
        if not suggestions:
            raise Exception(f"No suggestions found for company: {company_name}")
        return suggestions.suggested_campaign
        
    async def orchestrator(self, campaign_request: json) -> None:
        logger.info(f"Orchestrating campaign for company: {campaign_request['company_name']}")
        await self.db_tool.load_job(campaign_request['company_name'])
        company = (campaign_request['company_name']).lower()
        campaign_goal = campaign_request['campaign_goal']
        email = (campaign_request['email']).lower()
        profile = await self._extract_profile(company)
        results = await self._generate_suggestions(profile, campaign_goal)
        await self._store_suggestions(company, results, email)
        