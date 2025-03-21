from telethon.sync import TelegramClient
from telethon import events, sync
import os
from os import listdir
from os.path import isfile, join
import re
import asyncio
from dotenv import load_dotenv
import pytz
import logging
from datetime import datetime

# Load environment variables
load_dotenv()
timezone = pytz.timezone("Europe/Berlin")

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
name="listener"
#name="session_read"

logging.basicConfig(filename='/home/malte/telegram-listener-debug.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')

client = TelegramClient(name, API_ID, API_HASH)

client.connect()
client.start()
dialogs = client.get_dialogs()


def get_date_and_time(message):

    timezone = pytz.timezone("Europe/Berlin")

# Get the current time in that timezone
    date = datetime.now(timezone)    
    
    # if message.message:
    #     msg_text = message.message
    #     if re.search("Date",msg_text):
    #         lines = msg_text.splitlines()
    #         for line in lines:
    #             if re.search("^Date",line):
    #                 date_string=line
    #                 date_string = re.sub("^Date:","",date_string).strip()
    #                 date_info = date_string.split("-")
    #                 date = date.replace(year=int(date_info[0]),month=int(date_info[1]),day=int(date_info[2]))
    #             if re.search("^Time",line):
    #                 date_string=line
    #                 date_string = re.sub("^Time:","",date_string).strip()
    #                 date_info = date_string.split(":")
    #                 date = date.replace(hour=int(date_info[0]),minute=int(date_info[1]))

    date = f"Date: {date.strftime('%Y-%m-%d')}\nTime: {date.strftime('%H:%M')}"    
    return(date)


class Template:
    id = ""
    text = ""
    triggers = []
    pictured = False

    def __init__(self,message):
        self.id = ""
        self.text = ""
        self.triggers = []
        self.pictured = False
        self.template_from_message(message)

    def template_from_message(self,message):
        text = ""
        lines = str(message.text).splitlines()
        for line in lines:
            line = line.strip()
            if re.search("^-",line.lower()):
                self.id = re.sub("^-","",line).strip()
            elif re.search("^pictured",line.lower()):
                self.pictured = True
            elif re.search("^trigger:",line.lower()):
                trigger = re.sub("^trigger:","",line).strip()
                self.triggers.append(trigger)
            else:
                text = text + line + "\n"
        self.text = text

send_templates_pictured = {}
send_templates_raw = {}

async def update_templates():
    async for message in client.iter_messages("Templates API",reverse=True, limit=10000000):
        t = Template(message)
        if(t.pictured):
            print(t.id)
            #print(t.text)
            send_templates_pictured[t.id] = t
        else:
            send_templates_raw[t.id] = t



#template_path_pictured = "helper/send_templates/pictured/"
#send_templates_pictured = [f for f in listdir(template_path_pictured) if isfile(join(template_path_pictured, f))]

#template_path_raw = "helper/send_templates/raw/"
#send_templates_raw = [f for f in listdir(template_path_raw) if isfile(join(template_path_raw, f))]


async def trigger_templates(t):
    if(len(t.triggers)>0):
        for trigger in t.triggers:
            if(trigger in send_templates_pictured.keys()):
                t = send_templates_pictured[trigger]
                await client.send_file('API channel', 'helper/placeholder.jpg',caption = t.text)
            if(trigger in send_templates_raw.keys()):
                t = send_templates_raw[trigger]
                await client.send_message('API channel', t.text)


# @client.on(events.NewMessage)
# async def my_event_handler(event):
#     print('{}'.format(event))
@client.on(events.NewMessage(chats = ["API channel"]))
async def handler(event):
    #await update_templates()
    #await event.reply('Hey!')
    text = event.message.text.lower()
    print(text)

    if(re.search("send", text)):
        words = text.split()
        date_word = words[1].strip()
        info = "Transforming Diary data for: " + date_word
        print(info)
        await client.send_message('Helper API', info)

    if(text in send_templates_pictured.keys() or text in send_templates_raw.keys()):
        print("Using templates")

        try:
                dialogs = await client.get_dialogs()
                # Print chats
                for chat in dialogs:
                    if chat.name=="API channel":
                        CHANNEL_ID = chat.id
                        print("Hallo")
                entity = await client.get_entity(CHANNEL_ID)  # Force fetching the entity
        except ValueError as e:
            print(f"Error: {e}")
            
        try:
            if(text in send_templates_pictured.keys()):
                t = send_templates_pictured[text]
                caption = t.text + get_date_and_time(event.message)
                await client.send_file('API channel', 'helper/placeholder.jpg',caption = caption)
                await trigger_templates(t)
                await event.message.delete()
            if(text in send_templates_raw.keys()):
                t = send_templates_raw[text]
                caption = t.text + get_date_and_time(event.message)
                if not event.message.media:
                    await client.send_message('API channel', caption)
                    await trigger_templates(t)
                    await event.message.delete()
        except Exception as e:
            client.connect()
            client.start()
            dialogs = client.get_dialogs()
            await client.send_message('API channel', e)

    if(text=="update templates"):
        #await event.message.delete()
        await update_templates()
        print("Templates")
        print(send_templates_pictured)
        await event.message.delete()

# Clear all drafts
#client.connect()
for draft in client.get_drafts():
    draft.delete()

#asyncio.run(update_templates())
print(send_templates_pictured.keys())



client.run_until_disconnected()
