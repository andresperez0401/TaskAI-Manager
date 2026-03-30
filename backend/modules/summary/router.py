from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from modules.summary.schemas import TodaySummaryResponse
from modules.summary.service import SummaryService

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("/today", response_model=TodaySummaryResponse)
async def summary_today(session: AsyncSession = Depends(get_db_session)) -> TodaySummaryResponse:
    service = SummaryService(session)
    return await service.get_today_summary()
