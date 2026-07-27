import pytest

from app.core import rate_limit


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """All tests share TestClient's fixed client host, so hits would otherwise accumulate
    across every test in the session and eventually 429 unrelated tests once enough of them
    hit a rate-limited route.
    """
    rate_limit.reset()
    yield
    rate_limit.reset()
