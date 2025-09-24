from fastapi import APIRouter, HTTPException, Request, Response,BackgroundTasks,Depends
from app.agent.campaign_agent import CampaignAgent
from app.db.sqlite_conn import get_session
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["CampaignAgent"])

@router.post("/campaign-agent-suggestions/")
async def campaign_agent_trigger(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_session)):
    request_data = await request.json()
    if not all(key in request_data for key in ["company_name", "campaign_goal", "email"]):
        raise HTTPException(status_code=400, detail="Missing required fields: company_name, campaign_goal, email")
    agent = CampaignAgent(db)
    background_tasks.add_task(agent.orchestrator, request_data)
    logger.info("Campaign agent triggered successfully.")
    return Response(content="Request Accepted.",status_code=202)