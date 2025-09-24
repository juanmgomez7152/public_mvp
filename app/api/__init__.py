from fastapi import APIRouter

from app.api import campaign_planner

router = APIRouter()
router.include_router(campaign_planner.router,prefix="/campaign-planner")