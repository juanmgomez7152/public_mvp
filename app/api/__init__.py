from fastapi import APIRouter

from app.api import campaign_agent,campaign

router = APIRouter()
router.include_router(campaign_agent.router,prefix="/campaign-agent")
router.include_router(campaign.router,prefix="/campaign")