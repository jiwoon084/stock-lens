from fastapi import APIRouter, HTTPException

from app.schemas.checklist import ChecklistResponse
from app.services import checklist_service, market_data_service

router = APIRouter(prefix="/api/v1/stocks", tags=["checklist"])


@router.get("/{ticker}/checklist", response_model=ChecklistResponse)
def get_checklist(ticker: str) -> ChecklistResponse:
    if market_data_service.get_stock(ticker) is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    return checklist_service.get_today_checklist(ticker)
