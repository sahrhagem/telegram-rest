import pytest
import boto3
from telegram_rest.main import app
import json
import os
from dotenv import load_dotenv
from datetime import datetime


# Load environment variables
load_dotenv()
CHANNEL_ID=os.getenv('CHANNEL_ID') 
DIARY_CHANNEL=os.getenv('DIARY_CHANNEL') 
OUTPUT_DIR = os.getenv('OUTPUT_DIR')

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')


# Connect to MinIO
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)



@pytest.fixture
def client():
    return app.test_client()

def test_get_messages_from_reaction(client):
    response = client.post('/get_messages_reaction', json={"chat_id": DIARY_CHANNEL})
    response_json = response.get_json()
    assert response.status_code == 200
    reaction_ids_api = response_json["message_ids"]
    print(f"{reaction_ids_api} ({len(reaction_ids_api)})")


    response = client.post('/get_messages_reaction', json={"chat_id": CHANNEL_ID})
    response_json = response.get_json()
    assert response.status_code == 200
    reaction_ids_logs = response_json["message_ids"]
    print(f"{reaction_ids_logs} ({len(reaction_ids_logs)})")

    reaction_ids = [] 
    reaction_ids.append(reaction_ids_api)
    reaction_ids.append(reaction_ids_logs)
    reaction_ids = sum(reaction_ids, [])
    print(f"REACTION IDs: {reaction_ids}")
    

    for reaction_id in reaction_ids:
        if(reaction_id in reaction_ids_api):
            channel = DIARY_CHANNEL
        else:
            channel = CHANNEL_ID

        response = client.post('/get_message', json={"chat_id": channel, "message_id": reaction_id})
        assert response.status_code == 200
        message = response.get_json()



        time_stamp = message['message']['date']
        time_stamp = datetime.strptime(time_stamp,'%Y-%m-%dT%H:%M:%S')
        # Get current timestamp for folder structure
        year, month, day, hour = time_stamp.strftime("%Y"), time_stamp.strftime("%m"), time_stamp.strftime("%d"), time_stamp.strftime("%H")
        minio_path = f"messages/raw/year={year}/month={month}/day={day}/{message["message"]["chat_id"]}_{message["message"]["id"]}.json"


        # with open(tmp.name, 'w', encoding='utf-8') as f:
        #     json.dump(message, f, ensure_ascii=False, indent=2)

        # with open(tmp.name, "rb") as file_data:
        s3.put_object(Bucket=BUCKET_NAME, Key=minio_path, Body=json.dumps(message,indent=2), ContentType="application/json")
        print(f"Uploaded: → {minio_path}")
        if message["message"]["id"]:
            response = client.post('/delete_message', json={"chat_id": DIARY_CHANNEL, "message_id": reaction_id})
            response_json = response.get_json()
            assert response.status_code == 200
            print(f"Deleted: → {message["message"]["id"]}")
            
            response = client.post('/send_message', json={"chat_id": CHANNEL_ID, "message": json.dumps(message)})
            response_json = response.get_json()
            assert response.status_code == 200
            print(f"SENT: → {message["message"]["id"]}")

