from unittest.mock import patch

import pytest

from app.core.config import settings
from app.schemas.explanation import Factor, Source
from app.services import gemini_client, llm_service, solar_client


@pytest.fixture(autouse=True)
def _reset_provider_keys():
    original_solar_key = settings.solar_api_key
    original_gemini_key = settings.gemini_api_key
    settings.solar_api_key = ""
    settings.gemini_api_key = ""
    yield
    settings.solar_api_key = original_solar_key
    settings.gemini_api_key = original_gemini_key


def _make_source(source_id="source-1"):
    return Source(
        id=source_id,
        type="disclosure",
        title="주요사항보고서",
        publisher="DART · 삼성전자",
        published_at="2026-07-15T00:00:00+09:00",
        url="https://dart.fss.or.kr",
        excerpt="내용 발췌",
    )


def _call(sources, provider="solar"):
    return llm_service.generate_movement_explanation(
        ticker="005930",
        selected_date="2026-07-17",
        price=84400.0,
        change_percent=-2.65,
        volume_change_percent=236.58,
        direction="down",
        sources=sources,
        provider=provider,
    )


def test_no_sources_short_circuits_before_any_provider_call():
    with patch.object(solar_client, "generate_movement_explanation") as mock_call:
        result = _call(sources=[])

    mock_call.assert_not_called()
    assert result["factors"] == []
    assert result["confidence"] == "low"


def test_falls_back_to_rule_based_without_solar_key():
    sources = [_make_source()]

    with patch.object(solar_client, "generate_movement_explanation") as mock_call:
        result = _call(sources)

    mock_call.assert_not_called()
    assert result["factors"][0].title == sources[0].title  # rule-based echoes the source title


def test_uses_solar_when_key_present_and_provider_is_solar():
    settings.solar_api_key = "test-key"
    sources = [_make_source()]
    solar_result = {
        "headline": "SOLAR 헤드라인",
        "summary": "SOLAR 요약",
        "confidence": "high",
        "factors": [Factor(title="SOLAR 요인", impact="positive", description="d", source_ids=["source-1"])],
        "limitations": ["l"],
    }

    with patch.object(solar_client, "generate_movement_explanation", return_value=solar_result) as mock_call:
        result = _call(sources)

    mock_call.assert_called_once()
    assert result["headline"] == "SOLAR 헤드라인"


def test_falls_back_to_rule_based_when_solar_raises():
    settings.solar_api_key = "test-key"
    sources = [_make_source()]

    with patch.object(
        solar_client, "generate_movement_explanation", side_effect=solar_client.SolarApiError("boom")
    ):
        result = _call(sources)

    assert result["factors"][0].title == sources[0].title  # back to the rule-based shape


def test_sanitizes_hallucinated_source_ids():
    settings.solar_api_key = "test-key"
    sources = [_make_source(source_id="source-1")]
    solar_result = {
        "headline": "h",
        "summary": "s",
        "confidence": "medium",
        "factors": [
            Factor(
                title="t",
                impact="positive",
                description="d",
                source_ids=["source-1", "hallucinated-id"],
            )
        ],
        "limitations": [],
    }

    with patch.object(solar_client, "generate_movement_explanation", return_value=solar_result):
        result = _call(sources)

    assert result["factors"][0].source_ids == ["source-1"]


def test_falls_back_to_rule_based_without_gemini_key():
    sources = [_make_source()]

    with patch.object(gemini_client, "generate_movement_explanation") as mock_call:
        result = _call(sources, provider="gemini")

    mock_call.assert_not_called()
    assert result["factors"][0].title == sources[0].title


def test_uses_gemini_when_key_present_and_provider_is_gemini():
    settings.gemini_api_key = "test-key"
    sources = [_make_source()]
    gemini_result = {
        "headline": "Gemini 헤드라인",
        "summary": "Gemini 요약",
        "confidence": "high",
        "factors": [Factor(title="Gemini 요인", impact="positive", description="d", source_ids=["source-1"])],
        "limitations": ["l"],
    }

    with patch.object(gemini_client, "generate_movement_explanation", return_value=gemini_result) as mock_call:
        result = _call(sources, provider="gemini")

    mock_call.assert_called_once()
    assert result["headline"] == "Gemini 헤드라인"


def test_falls_back_to_rule_based_when_gemini_raises():
    settings.gemini_api_key = "test-key"
    sources = [_make_source()]

    with patch.object(
        gemini_client, "generate_movement_explanation", side_effect=gemini_client.GeminiApiError("boom")
    ):
        result = _call(sources, provider="gemini")

    assert result["factors"][0].title == sources[0].title


def test_sanitizes_source_summaries_to_known_ids():
    settings.solar_api_key = "test-key"
    sources = [_make_source(source_id="source-1")]
    solar_result = {
        "headline": "h",
        "summary": "s",
        "confidence": "medium",
        "factors": [],
        "limitations": [],
        "source_summaries": [
            {"source_id": "source-1", "lines": ["첫 줄이에요.", "둘째 줄이에요.", "", "  "]},
            {"source_id": "hallucinated-id", "lines": ["보이면 안 되는 줄"]},
        ],
    }

    with patch.object(solar_client, "generate_movement_explanation", return_value=solar_result):
        result = _call(sources)

    assert result["source_summaries"] == {"source-1": ["첫 줄이에요.", "둘째 줄이에요."]}


def test_solar_and_gemini_do_not_cross_call_each_other():
    settings.solar_api_key = "test-key"
    sources = [_make_source()]

    with patch.object(solar_client, "generate_movement_explanation"), patch.object(
        gemini_client, "generate_movement_explanation"
    ) as mock_gemini:
        _call(sources, provider="solar")

    mock_gemini.assert_not_called()
