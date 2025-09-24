from fastapi import APIRouter, HTTPException, Request, Response,BackgroundTasks
from app.agent.campaign_agent import CampaignAgent
from app.agent.tools.db_tool import DBTool
import logging
import asyncio

db_tool = DBTool()
agent = CampaignAgent()
logger = logging.getLogger(__name__)
router = APIRouter(tags=["CampaignAgent"])

@router.post("/campaign-agent-suggestions/")
async def campaign_agent_trigger(request: Request, background_tasks: BackgroundTasks):
    request_data = await request.json()
    if not all(key in request_data for key in ["company_name", "campaign_goal", "email"]):
        raise HTTPException(status_code=400, detail="Missing required fields: company_name, campaign_goal, email")
    background_tasks.add_task(db_tool.load_job, request_data['company_name'])
    background_tasks.add_task(agent.orchestrator, request_data)
    logger.info("Campaign agent triggered successfully.")
    return Response(content="Request Accepted.",status_code=202)

@router.post("/suggestions/retrieve/")
async def retrieve_suggestions(request: Request):
    try:
        suggestions = db_tool.get_campaign_suggestions((await request.json())['company_name'])
        return suggestions
    except Exception as e:
        logger.error(f"Error retrieving suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/suggestions/status/")
async def get_campaign_status(request: Request):
    try:
        status = db_tool.extract_latest_status((await request.json())['company_name'])
        return {"status": status}
    except Exception as e:
        logger.error(f"Error retrieving company status: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")