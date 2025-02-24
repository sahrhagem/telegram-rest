from flask import Flask, request, jsonify
from telethon import TelegramClient
import asyncio
import os
from dotenv import load_dotenv
import sqlite3
import json

# Load environment variables
load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_FILE = os.getenv('SESSION_FILE', 'log_sender.session')  # Default session file name
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Enable WAL mode
def enable_wal():
    conn = sqlite3.connect(SESSION_FILE)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.commit()
    conn.close()

enable_wal()

# Initialize Flask app
app = Flask(__name__)

# Ensure a single event loop exists
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Initialize Telethon client
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)


async def send_message(message):
    async with client:
        try:
            dialogs = await client.get_dialogs()
            # Print chats
            for chat in dialogs:
                if chat.name=="logs_api":
                    CHANNEL_ID = chat.id
                    print("Hallo")
            entity = await client.get_entity(CHANNEL_ID)  # Force fetching the entity
            message = await client.send_message(entity, message)
            print(f"Message sent successfully! ({message.id} in {message.chat_id})")
        except ValueError as e:
            print(f"Error: {e}")


async def get_message_func(channel_id,message_id):
    async with client:
        try:
            dialogs = await client.get_dialogs()
            # Print chats
            for chat in dialogs:
                if chat.id==channel_id:
                    channel_id = chat.id
                    print("Hallo")
            entity = await client.get_entity(channel_id)  # Force fetching the entity
            message = await client.get_messages(entity, ids=message_id)
            print(f"Message received successfully! ({message.id} in {message.chat_id})")

            if message:
                print(f"Message ID: {message.id}")
                print(f"Date: {message.date}")
                print(f"Text: {message.message}")
                print(f"Sender ID: {message.sender_id}")

                return {"message_id": message.id, "date": message.date.isoformat(), "text": message.message}
            else:
                print("Message not found.")
        except ValueError as e:
            print(f"Error: {e}")


async def get_messages_from_reaction(channel_id,reaction):
    async with client:
        try:
            dialogs = await client.get_dialogs()
            # Print chats
            for chat in dialogs:
                if chat.id==channel_id:
                    channel_id = chat.id
                    print("Hallo")
            entity = await client.get_entity(channel_id)  # Force fetching the entity


            message_array = []
            async for message in client.iter_messages(entity,reverse=False, limit=50):
                if message.reactions:
                    for reaction_instance in message.reactions.results:                          
                        if reaction_instance.reaction.emoticon == reaction:
                            message_array.insert(0,message.id)

                            print(f"Message ID: {message.id}")
                            print(f"Date: {message.date}")
                            print(f"Text: {message.message}")
                            print(f"Sender ID: {message.sender_id}")
                            print(f"Reactions: {reaction_instance.reaction.emoticon}\n")

            return message_array
        except ValueError as e:
            print(f"Error: {e}")


async def get_chat_id_from_name_func(channel_name):
    async with client:
        try:
            dialogs = await client.get_dialogs()
            # Print chats
            for chat in dialogs:
                if chat.name==channel_name:
                    return chat.id
            return(None)
        except ValueError as e:
            print(f"Error: {e}")



@app.route('/log', methods=['POST'])
def receive_log():
    """API endpoint to receive logs and forward to Telegram."""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request"}), 400

    log_message = data['message']

    loop.run_until_complete(send_message(log_message))

    return jsonify({"status": "Message sent"}), 200


@app.route('/get_message', methods=['POST'])
def get_message():
    """API endpoint to receive logs and forward to Telegram."""
    data = request.get_json()
    
    if not data or 'chat_id' not in data or 'message_id' not in data:
        return jsonify({"error": "Invalid request"}), 400

    channel_id = int(data['chat_id'])
    message_id = int(data['message_id'])
    print(channel_id)
    print(message_id)

    message = loop.run_until_complete(get_message_func(channel_id,message_id))

    return jsonify({"status": "Message received", "message": message}), 200

@app.route('/get_messages_reaction', methods=['POST'])
def get_messages_reaction():
    """API endpoint to receive logs and forward to Telegram."""
    data = request.get_json()
    
    if not data or 'chat_id' not in data:
        return jsonify({"error": "Invalid request"}), 400

    channel_id = int(data['chat_id'])
    print(channel_id)

    message_ids = loop.run_until_complete(get_messages_from_reaction(channel_id, "👍"))

    return jsonify({"status": "Messages found", "message_ids": message_ids}), 200

@app.route('/get_chat_id_from_name', methods=['POST'])
def get_chat_id_from_name():
    """API endpoint to get Chat ID from channel name."""
    data = request.get_json()
    
    if not data or 'chat_name' not in data:
        return jsonify({"error": "Invalid request"}), 400

    channel_name = data['chat_name']
    print(channel_name)

    chat_id = loop.run_until_complete(get_chat_id_from_name_func(channel_name))
    if chat_id:
        return jsonify({"status": "ID found", "chat_id": chat_id}), 200
    else:
        return jsonify({"status": "ID not found", "chat_id": None}), 200



if __name__ == '__main__':
    client.start()
    app.run(host='0.0.0.0', port=5000, use_reloader=False)
    client.disconnect()