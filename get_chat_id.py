from telethon.sync import TelegramClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_FILE = os.getenv('SESSION_FILE', 'log_sender.session')

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def get_my_chats():
    async with client:
        dialogs = await client.get_dialogs()
        for chat in dialogs:
            print(f"Chat Name: {chat.name} | ID: {chat.id}")

client.loop.run_until_complete(get_my_chats())