import pytest
from httpx import AsyncClient
from ..main import app

@pytest.mark.asyncio
async def test_ticket_flow():
    async with AsyncClient(app=app, base_url='http://test') as client:
        # register tech and user
        await client.post('/auth/register', json={'username':'tech1','password':'pass','role':'technician','email':'tech@example.com'})
        await client.post('/auth/register', json={'username':'user1','password':'pass','role':'driver'})
        r = await client.post('/auth/token', data={'username':'user1','password':'pass'})
        token = r.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        # create ticket
        tr = await client.post('/tickets', json={'title':'Test','description':'desc'}, headers=headers)
        assert tr.status_code == 200
        data = tr.json()
        assert 'ticket_id' in data