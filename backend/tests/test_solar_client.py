import json
from unittest.mock import Mock, patch

import pytest

from app.core.config import settings
from app.services import solar_client


@pytest.fixture(autouse=True)
def _reset_solar_key():
    original_key = settings.solar_api_key
    settings.solar_api_key = ""
    yield
    settings.solar_api_key = original_key


def _fake_success_response(payload: dict):
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(payload)}}],
    }
    return response


_VALID_PAYLOAD = {
    "headline": "실적 기대감에 상승",
    "summary": "공시 내용을 근거로 상승 요인을 정리했습니다.",
    "confidence": "medium",
    "factors": [
        {
            "title": "실적 기대",
            "impact": "positive",
            "description": "시장 전망치를 상회할 것이라는 기대감입니다.",
            "source_ids": ["source-1"],
        }
    ],
    "limitations": ["공시만으로 인과관계를 확정할 수 없습니다."],
    "source_summaries": [{"source_id": "source-1", "lines": ["실적 전망치를 상회할 것이라는 기대감이에요."]}],
}


def test_raises_without_key():
    with pytest.raises(solar_client.SolarApiError):
        solar_client.generate_movement_explanation("prompt")


def test_parses_valid_response():
    settings.solar_api_key = "test-key"

    with patch.object(solar_client.requests, "post", return_value=_fake_success_response(_VALID_PAYLOAD)):
        result = solar_client.generate_movement_explanation("prompt")

    assert result["headline"] == _VALID_PAYLOAD["headline"]
    assert result["confidence"] == "medium"
    assert len(result["factors"]) == 1
    assert result["factors"][0].title == "실적 기대"
    assert result["factors"][0].source_ids == ["source-1"]


def test_raises_on_network_error():
    settings.solar_api_key = "test-key"

    with patch.object(solar_client.requests, "post", side_effect=ConnectionError("boom")):
        with pytest.raises(solar_client.SolarApiError):
            solar_client.generate_movement_explanation("prompt")


def test_raises_on_malformed_json_content():
    settings.solar_api_key = "test-key"
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"choices": [{"message": {"content": "not json"}}]}

    with patch.object(solar_client.requests, "post", return_value=response):
        with pytest.raises(solar_client.SolarApiError):
            solar_client.generate_movement_explanation("prompt")


def test_raises_on_missing_field():
    settings.solar_api_key = "test-key"
    incomplete = {k: v for k, v in _VALID_PAYLOAD.items() if k != "limitations"}

    with patch.object(solar_client.requests, "post", return_value=_fake_success_response(incomplete)):
        with pytest.raises(solar_client.SolarApiError):
            solar_client.generate_movement_explanation("prompt")
