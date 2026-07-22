from app.schemas.explanation import MovementExplanationRequest, MovementExplanationResponse
from app.services import llm_service, market_data_service, retrieval_service


class UnknownTickerError(ValueError):
    pass


class UnknownDateError(ValueError):
    pass


def explain_movement(request: MovementExplanationRequest) -> MovementExplanationResponse:
    stock = market_data_service.get_stock(request.ticker)
    if stock is None:
        raise UnknownTickerError(f"Unknown ticker: {request.ticker}")

    prices = market_data_service.get_price_series(request.ticker)
    point = next((p for p in prices if p.time == request.selected_date), None)
    if point is None:
        raise UnknownDateError(f"No price data for {request.ticker} on {request.selected_date}")

    direction = "up" if point.change_percent > 0 else "down" if point.change_percent < 0 else "flat"

    sources = retrieval_service.get_related_documents(
        ticker=request.ticker,
        selected_date=request.selected_date,
        direction=direction,
    )

    analysis = llm_service.generate_movement_explanation(
        ticker=request.ticker,
        selected_date=request.selected_date,
        price=point.close,
        change_percent=point.change_percent,
        volume_change_percent=point.volume_change_percent,
        direction=direction,
        sources=sources,
        provider=request.llm_provider,
    )

    source_summaries = analysis.get("source_summaries", {})
    for source in sources:
        lines = source_summaries.get(source.id)
        if lines:
            source.summary_lines = lines

    return MovementExplanationResponse(
        ticker=request.ticker,
        selected_date=request.selected_date,
        price=point.close,
        change_percent=point.change_percent,
        volume_change_percent=point.volume_change_percent,
        direction=direction,
        headline=analysis["headline"],
        summary=analysis["summary"],
        confidence=analysis["confidence"],
        factors=analysis["factors"],
        sources=sources,
        limitations=analysis["limitations"],
    )
