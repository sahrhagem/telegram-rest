from flask import Flask, request, jsonify
from telethon import TelegramClient
import asyncio
import os
import pytz
from dotenv import load_dotenv
import sqlite3
import json
import base64
import re
from datetime import datetime


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


async def send_log(message):
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

async def send_message_func(chat_id,message):
    async with client:
        try:
            dialogs = await client.get_dialogs()
            # Print chats
            for chat in dialogs:
                if chat.id==chat_id:
                    print("Found")
            entity = await client.get_entity(chat_id)  # Force fetching the entity
            if not message["media"]:
                message = await client.send_message(entity, str(message["message"]))
            else:
                image_path = "tmp_media.jpg"
                base64_to_image(message["media"]["base64"], image_path)
                message = await client.send_file(entity, image_path,caption = message["message"])
            print(f"Message sent successfully! ({message.id} in {message.chat_id})")
        except ValueError as e:
            print(f"Error: {e}")

def file_to_base64(file_path):
    """Convert a file to a base64-encoded string."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def base64_to_image(base64_string, output_filename):
    """Converts a Base64 string to an image file."""
    try:
        image_data = base64.b64decode(base64_string)  # Decode Base64 to binary
        with open(output_filename, "wb") as file:
            file.write(image_data)
        print(f"Image saved as {output_filename}")
        return True
    except Exception as e:
        print(f"Image save failed for {output_filename}")
        return False
def check_date(message):
    date = message.date
    
    # Extract and convert timestamp
    utc_time = datetime.strptime(date.isoformat(), "%Y-%m-%dT%H:%M:%S+00:00")

    utc = pytz.utc
    berlin_tz = pytz.timezone('Europe/Berlin')
    utc_time = utc.localize(utc_time)
    date = utc_time.astimezone(berlin_tz)
    

    if message.message:
        msg_text = message.message
        if re.search("Date",msg_text):
            lines = msg_text.splitlines()
            for line in lines:
                if re.search("^Date",line):
                    date_string=line
                    date_string = re.sub("^Date:","",date_string).strip()
                    date_info = date_string.split("-")
                    date = date.replace(year=int(date_info[0]),month=int(date_info[1]),day=int(date_info[2]))
    date = date.strftime('%Y-%m-%dT%H:%M:%S')    
    return(date)

def check_mid(message):
    mid = message.id

    if message.message:
        msg_text = message.message
        if re.search("MID",msg_text):
            lines = msg_text.splitlines()
            for line in lines:
                if re.search("^MID",line):
                    mid = re.sub("^MID:","",line).strip()
                    return(mid)
    return(mid)


def check_chat_id(message):
    cid = message.peer_id.channel_id if message.peer_id else None

    if message.message:
        msg_text = message.message
        if re.search("CID",msg_text):
            lines = msg_text.splitlines()
            for line in lines:
                if re.search("^CID",line):
                    cid = re.sub("^CID:","",line).strip()
                    return(cid)
    return(cid)


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
            if(message):
                print(f"Message received successfully! ({message.id} in {message.chat_id})")

            message.id = check_mid(message)
            if message:
                msg_dict = {
                    "id": message.id,
                    "date_original": message.date.isoformat(),
                    "date": check_date(message),
                    "message": message.message,
                    "out": message.out,
                    "mentioned": message.mentioned,
                    "media": None,  # Convert media to string or handle separately
                    "sender_id": message.from_id.user_id if message.from_id else None,
                    "chat_id": check_chat_id(message),
                    "reply_to": message.reply_to.reply_to_message_id if message.reply_to else None
                }

                # Check if the message contains media
                if message.media:
                    media_path = await message.download_media(file="temp_media.jpg")
                    
                    # Convert to Base64
                    media_base64 = file_to_base64(media_path)
                    base64_to_image(media_base64, "output_image.jpg")                    
                    # Store media as Base64 in JSON
                    msg_dict["media"] = {
                        "type": type(message.media).__name__,  # Get media type (Photo, Document, etc.)
                        "media_string": str(message.media),
                        "base64": media_base64
                    }             


                json_msg = msg_dict
                return json_msg
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
            async for message in client.iter_messages(entity,reverse=False, limit=200):
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

async def check_channel(chat_id):
    counter = 0
    async with client:
        try:
            dialogs = await client.get_dialogs()
            # Print chats
            for chat in dialogs:
                if chat.id==chat_id:
                    chat_id = chat.id
            entity = await client.get_entity(chat_id)  # Force fetching the entity
            print(f"Testing Date and Time for: {chat_id}")
            async for message in client.iter_messages(entity,reverse=False, limit=100):
                if message.message and ("Time" not in message.message or "Date" not in message.message):
                    print(f"No Date found for: {message.id}")
                    date = check_date(message)
                    date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')

                    msg = message.message
                    if not "Date:" in message.message:
                        date_str = date.strftime('%Y-%m-%d')
                        msg = msg + f"\nDate: {date_str}"
                    if not "Time:" in message.message:
                        time = date.strftime('%H:%M')
                        msg = msg + f"\nTime: {time}"
                    #print(f"Changed msesage to: {msg}")                        
                    await client.edit_message(chat_id,message.id,msg)
                    counter = counter+1
            
        except ValueError as e:
            print(f"Error: {e}")
        return(counter)

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

async def delete_message_func(channel_id,message_id):
    async with client:
        try:
            dialogs = await client.get_dialogs()
            # Print chats
            for chat in dialogs:
                if chat.id==channel_id:
                    channel_id = chat.id
            entity = await client.get_entity(channel_id)  # Force fetching the entity
            await client.delete_messages(entity, message_id)
            print(f"Message deleted successfully! ({message_id} in {channel_id})")
        except ValueError as e:
            print(f"Error: {e}")



@app.route('/log', methods=['POST'])
def receive_log():
    """API endpoint to receive logs and forward to Telegram."""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request"}), 400

    log_message = data['message']

    loop.run_until_complete(send_log(log_message))

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

    return jsonify({"status": "Message received", "time_stamp": datetime.now(pytz.timezone('Europe/Berlin')).isoformat(),"message": message}), 200

@app.route('/delete_message', methods=['POST'])
def delete_message():
    """API endpoint to receive logs and forward to Telegram."""
    data = request.get_json()
    
    if not data or 'chat_id' not in data or 'message_id' not in data:
        return jsonify({"error": "Invalid request"}), 400

    channel_id = int(data['chat_id'])
    message_id = int(data['message_id'])
    print(channel_id)
    print(message_id)

    loop.run_until_complete(delete_message_func(channel_id,message_id))

    return jsonify({"status": "Message deleted", "time_stamp": datetime.now(pytz.timezone('Europe/Berlin')).isoformat()}), 200


@app.route('/get_messages_reaction', methods=['POST'])
def get_messages_reaction():
    """API endpoint to receive logs and forward to Telegram.
    POST input: chat_id (int)
    """
    data = request.get_json()
    
    if not data or 'chat_id' not in data:
        return jsonify({"error": "Invalid request"}), 400

    channel_id = int(data['chat_id'])
    print(channel_id)

    message_ids = loop.run_until_complete(get_messages_from_reaction(channel_id, "👍"))
    #message_ids = loop.run_until_complete(get_messages_from_reaction(channel_id, "🔥"))

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



@app.route('/send_message', methods=['POST'])
def send_message():
    """API endpoint to receive logs and forward to Telegram."""
    data = request.get_json()
    
    if not data or 'chat_id' not in data or 'message' not in data:
        return jsonify({"error": "Invalid request"}), 400

    channel_id = int(data['chat_id'])
    message = json.loads(data['message'])
    message_text = message['message']['message']
    message_id = message['message']['id']
    chat_id = message['message']['chat_id']
    if not "MID" in message_text:
        message["message"]["message"] = f"{message_text}\nMID: {message_id}"
    if not "CID" in message_text:
        message["message"]["message"] = f"{message["message"]["message"]}\nCID: {chat_id}"
    print(channel_id)


    message = loop.run_until_complete(send_message_func(channel_id,message["message"]))
    return jsonify({"status": "Message sent", "time_stamp": datetime.now(pytz.timezone('Europe/Berlin')).isoformat(),"message": message}), 200

@app.route('/check', methods=['POST'])
def check():
    """API endpoint to receive logs and forward to Telegram."""
    data = request.get_json()
    
    if not data or 'chat_id' not in data:
        return jsonify({"error": "Invalid request"}), 400

    chat_id = int(data['chat_id'])

    counter = loop.run_until_complete(check_channel(chat_id))

    return jsonify({"status": f"Date and Time added: {counter} messages"}), 200


if __name__ == '__main__':
    client.start()
    app.run(host='0.0.0.0', port=5000, use_reloader=False)
    client.disconnect()