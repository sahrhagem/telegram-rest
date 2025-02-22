from flask import Flask, request, jsonify
from telethon import TelegramClient
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_FILE = os.getenv('SESSION_FILE', 'log_sender.session')  # Default session file name
CHANNEL_ID = os.getenv('CHANNEL_ID')

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
            await client.send_message(entity, message)
            print("Message sent successfully!")
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

if __name__ == '__main__':
    client.start()
    app.run(host='0.0.0.0', port=5000, use_reloader=False)