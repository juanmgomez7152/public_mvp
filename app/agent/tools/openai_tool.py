import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel
from app.db.sqlite_conn import CompanyProfile,CampaignSuggestions

load_dotenv()
class CampaignLLMResponse(BaseModel):
    company_name: str
    suggestions: List[str]

class OpenAITool:
    def __init__(self):
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = OpenAI(api_key=self.OPENAI_API_KEY)
        self.MODEL_NAME = "gpt-5-mini"


    def _openai_call(self, prompt: str,text_structure: BaseModel = CampaignLLMResponse, temperature: int = 1, seed: int = 42, top_p: int = 1) -> BaseModel:
        reponse = self.client.responses.parse(
            model=self.MODEL_NAME,
            input=[
                {
                    "role": "system",
                    "content": "You are an expert consultant that helps Companies achieve their desired campaign goals by generating marketing campaign ideas based on company profiles and the goal the company provides."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            text_format=text_structure
        )
        
        event = reponse.output_parsed
        return event
    
    def generate_campaign_ideas(self, company_profile: CompanyProfile, goal:str) -> str:
        prompt = f"""
        Generate campaign ideas for the following campaign goal: {goal}
        Based on the following company profile:
        Company Name: {company_profile.company_name}
        brand_voice: {company_profile.brand_voice}
        target_audience: {company_profile.target_audience}
        product_category: {company_profile.product_category}
        style_guide: {company_profile.style_guide}
        recent_campaign_metrics: {company_profile.recent_campaign_metrics}
        """
        response = self._openai_call(prompt)
        campaign_suggestions = CampaignSuggestions(
            company_name=response.company_name,
            suggested_campaign={"suggestions": response.suggestions}
        )
        return campaign_suggestions