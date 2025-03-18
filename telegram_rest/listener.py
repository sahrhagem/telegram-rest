from telethon.sync import TelegramClient
from telethon import events, sync
import os
from os import listdir
from os.path import isfile, join
import re
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
name="listener"
#name="session_read"

client = TelegramClient(name, API_ID, API_HASH)

client.connect()
client.start()
dialogs = client.get_dialogs()

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
#    if(text.lower()=="placeholder"):
#        await client.send_file('API channel', 'helper/placeholder.jpg',clear_draft = True)
    if(text=="edit"):
        os.system("python3 /home/malte/repos/telegramapi/edit_messages.py")
        await event.message.delete()

    if(re.search("send", text)):
        words = text.split()
        date_word = words[1].strip()
        info = "Transforming Diary data for: " + date_word
        print(info)
        await client.send_message('Helper API', info)

        try:
            os.system("bash /home/malte/repos/telegramapi/transform.sh " + date_word)
            await client.send_file('Extra API', 'data.txt',caption = date_word)     
        except: 
            info = "Transformation failed"
            print(info)       
            await client.send_message('Helper API', info)
        await event.message.delete()

    if(re.search("spendings", text)):
        info = "Spendings"
        print(info)
        await client.send_message('Helper API', info)

        try:
            os.system("python3 /home/malte/repos/telegramapi/scripts/test.py")
            os.system("python3 /home/malte/repos/telegramapi/scripts/visualize_spendings.py")

            await client.send_file('Helper API', 'spendings_pie_charts.pdf',caption = "Spendings")     
        except: 
            info = "Transformation failed"
            print(info)       
            await client.send_message('Helper API', info)
        await event.message.delete()



    if(text in send_templates_pictured.keys() or text in send_templates_raw.keys()):
        print("Using templates")
        try:
            if(text in send_templates_pictured.keys()):
                t = send_templates_pictured[text]
                await client.send_file('API channel', 'helper/placeholder.jpg',caption = t.text)
                await trigger_templates(t)
                await event.message.delete()
            if(text in send_templates_raw.keys()):
                t = send_templates_raw[text]
                await client.send_message('API channel', t.text)
                await trigger_templates(t)
                await event.message.delete()
        except:
            client.connect()
            client.start()
            dialogs = client.get_dialogs()
            await client.send_message('API channel', text)

    if(text=="update templates"):
        #await event.message.delete()
        await update_templates()
        print("Templates")
        print(send_templates_pictured)
        await event.message.delete()



    #
# Clear all drafts


#client.connect()
for draft in client.get_drafts():
    draft.delete()

#asyncio.run(update_templates())
print(send_templates_pictured.keys())



client.run_until_disconnected()
#client.send_message('API channel', "update templates")


#client.loop.run_until_complete(main())
