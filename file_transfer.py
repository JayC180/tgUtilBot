import os
import json
from telegram import Document, Bot
from telegram.error import BadRequest
import requests

config_file = json.load(open("config.json"))
TOKEN = config_file["apiKey"]
chat_id = config_file["chatID"]
default_downloads_folder = config_file["defaultDownloadsFolder"]

async def handle_file_transfer(document: Document, folder_path: str) -> str:
    if not os.path.exists(folder_path):
        ans = input('Invalid folder path. Would you like to create it? (y/n)')
        if ans == 'y':
            os.makedirs(folder_path)
        if ans == 'n':
            return 'Invalid folder path. File not saved.'
        else:
            return 'Invalid input. File not saved.'
        
    file_id = document.file_id
    bot = Bot(TOKEN)
    file = await bot.get_file(file_id)
    url = file.file_path
    print(f'file path: {url}')
    local_file_path = os.path.join(folder_path, document.file_name)
    
    try:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with open(local_file_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024): 
                if chunk: 
                    f.write(chunk)
        return f'File successfully saved to {local_file_path}'
    except BadRequest:  
        print("File too big")
        return "File too big. File not saved."
    except Exception as e:
        return f'Failed to save file: {e}'