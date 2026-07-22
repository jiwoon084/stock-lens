from fastapi import APIRouter, HTTPException

from app.schemas.stock_analysis import StockAnalysisRequest, StockAnalysisResponse
from app.services import stock_analysis_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/date", response_model=StockAnalysisResponse)
def analyze_date(request: StockAnalysisRequest) -> StockAnalysisResponse:
    try:
        return stock_analysis_service.analyze_date(request.ticker, request.selected_date)
    except stock_analysis_service.UnknownTickerError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except stock_analysis_service.UnknownDateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
