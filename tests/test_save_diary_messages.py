import pytest
from telegram_rest.main import app
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DIARY_CHANNEL=os.getenv('DIARY_CHANNEL') 
OUTPUT_DIR = os.getenv('OUTPUT_DIR')

@pytest.fixture
def client():
    return app.test_client()

def test_get_messages_from_reaction(client):
    response = client.post('/get_messages_reaction', json={"chat_id": DIARY_CHANNEL})
    response_json = response.get_json()
    assert response.status_code == 200
    reaction_ids = response_json["message_ids"]
    print(f"{reaction_ids} ({len(reaction_ids)})")

    for reaction_id in reaction_ids:
        response = client.post('/get_message', json={"chat_id": DIARY_CHANNEL, "message_id": reaction_id})
        assert response.status_code == 200

        with open(os.path.join(OUTPUT_DIR,f"{reaction_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(response.get_json()["message"], f, ensure_ascii=False, indent=4)

