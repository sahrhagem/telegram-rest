import pytest
from telegram_rest.main import app
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CHANNEL_ID = os.getenv('CHANNEL_ID')
DIARY_CHANNEL=os.getenv('DIARY_CHANNEL')
DIARY_CHANNEL_NAME=os.getenv('DIARY_CHANNEL_NAME')


@pytest.fixture
def client():
    return app.test_client()

# def test_receive_log(client):
#     response = client.post('/log', json={"message": "Test log"})
#     assert response.status_code == 200
#     assert response.get_json() == {"status": "Message sent"}
#     print(response.get_json())

def test_get_message(client):
    response = client.post('/get_message', json={"chat_id": CHANNEL_ID, "message_id": "57"})
    assert response.status_code == 200
    print(response.get_json())    

def test_get_messages_from_reaction(client):
    response = client.post('/get_messages_reaction', json={"chat_id": CHANNEL_ID})
    assert response.status_code == 200
    print(response.get_json())    

def test_get_messages_from_reaction(client):
    response = client.post('/get_messages_reaction', json={"chat_id": CHANNEL_ID})
    assert response.status_code == 200
    print(response.get_json())    
    response_json = response.get_json()
    reaction_ids = response_json["message_ids"]
    print(f"{reaction_ids} ({len(reaction_ids)})")

    response = client.post('/get_message', json={"chat_id": CHANNEL_ID, "message_id": reaction_ids[0]})
    assert response.status_code == 200
    print(response.get_json())

    OUTPUT_DIR = os.getenv('OUTPUT_DIR')

    with open(os.path.join(OUTPUT_DIR,'reaction_messages.json'), 'w', encoding='utf-8') as f:
        json.dump(response.get_json()["message"], f, ensure_ascii=False, indent=4)

def test_get_messages_from_reaction(client):
    response = client.post('/get_chat_id_from_name', json={"chat_name": DIARY_CHANNEL_NAME})
    assert response.status_code == 200
    response_json = response.get_json()
    chat_id = response_json["chat_id"]
    print(f"Chat ID: {chat_id}")

def test_check_channel(client):
    response = client.post('/check', json={"chat_id": DIARY_CHANNEL})
    assert response.status_code == 200
    print(response.get_json())    

