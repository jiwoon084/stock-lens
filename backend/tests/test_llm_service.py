from app.services import llm_service


def test_few_sources_routes_to_gemini_first():
    providers = llm_service._providers_for(0)
    assert [p.name for p in providers] == ["gemini", "solar"]

    providers = llm_service._providers_for(llm_service._SIMPLE_SOURCE_THRESHOLD)
    assert [p.name for p in providers] == ["gemini", "solar"]


def test_many_sources_routes_to_solar_first():
    providers = llm_service._providers_for(llm_service._SIMPLE_SOURCE_THRESHOLD + 1)
    assert [p.name for p in providers] == ["solar", "gemini"]

    providers = llm_service._providers_for(5)
    assert [p.name for p in providers] == ["solar", "gemini"]
