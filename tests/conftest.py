from __future__ import annotations

from unittest.mock import patch

import fakeredis.aioredis
import httpx
import pytest
from httpx import ASGITransport

from krx_fundamentals_api.main import app


@pytest.fixture(autouse=True)
async def mock_redis():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await fake.flushall()

    async def fake_get_redis():
        return fake

    with (
        patch("krx_fundamentals_api.services.cache._redis", fake),
        patch("krx_fundamentals_api.services.cache.get_redis", fake_get_redis),
    ):
        yield fake
        await fake.aclose()


@pytest.fixture(autouse=True)
def mock_scheduler():
    with (
        patch("krx_fundamentals_api.main.start_scheduler"),
        patch("krx_fundamentals_api.main.stop_scheduler"),
        patch("krx_fundamentals_api.main.close_redis", return_value=None),
        patch("krx_fundamentals_api.services.scheduler.start_scheduler"),
        patch("krx_fundamentals_api.services.scheduler.stop_scheduler"),
    ):
        yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
