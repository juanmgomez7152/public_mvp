from fastapi import APIRouter, HTTPException, Request, Response, Depends
from app.agent.campaign_agent import CampaignAgent
from app.db.sqlite_conn import get_session
from sqlalchemy.orm import Session
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Campaign"])

@router.post("/suggestions/retrieve/")
async def retrieve_suggestions(request: Request, db: Session = Depends(get_session)):
    try:
        agent = CampaignAgent(db)
        suggestions = await agent.get_campaign_suggestions((await request.json())['company_name'])
        return Response(content=json.dumps(suggestions), media_type="application/json", status_code=200)
    except Exception as e:
        logger.error(f"Error retrieving suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")