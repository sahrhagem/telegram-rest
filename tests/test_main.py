import pytest
from telegram_rest.main import app

@pytest.fixture
def client():
    return app.test_client()

def test_receive_log(client):
    response = client.post('/log', json={"message": "Test log"})
    assert response.status_code == 200
    assert response.get_json() == {"status": "Message sent"}
