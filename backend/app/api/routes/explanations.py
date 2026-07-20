from fastapi import APIRouter, HTTPException

from app.schemas.explanation import MovementExplanationRequest, MovementExplanationResponse
from app.services import explanation_service

router = APIRouter(prefix="/api/v1/explanations", tags=["explanations"])


@router.post("", response_model=MovementExplanationResponse)
def create_explanation(request: MovementExplanationRequest) -> MovementExplanationResponse:
    try:
        return explanation_service.explain_movement(request)
    except explanation_service.UnknownTickerError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except explanation_service.UnknownDateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
