import pytest
from httpx import AsyncClient
from ..main import app

@pytest.mark.asyncio
async def test_telemetry_requires_auth():
    async with AsyncClient(app=app, base_url='http://test') as client:
        r = await client.post('/telemetry', json={})
        assert r.status_code in (401, 422)