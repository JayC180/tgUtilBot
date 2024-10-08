import json
import os
from typing import Final
from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from responses import handle_response
from file_transfer import handle_file_transfer

config_file = json.load(open("config.json"))
BOT_USERNAME: Final = config_file["botName"]
TOKEN = config_file["apiKey"]
default_downloads_folder = config_file["defaultDownloadsFolder"]

# State keys
STATE_AWAIT_FOLDER = "await_folder"
STATE_AWAIT_DOCUMENT = "await_document"
STATE_AWAIT_FOLDER_CREATION = "await_create_folder"

# Commands

async def start_command(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is response to the /start command. See /help for command options.')

async def help_command(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('The only commands I have now are "/start", "/help", and /sendfile. More will be updated in the future.')
    
async def sendfile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = STATE_AWAIT_FOLDER
    await update.message.reply_text('Please specify the path you wish to store the file to. Reply \'default\' or \'d\' for default folder.')

# files handling
async def handle_folder(update: Update, context: CallbackContext):
    if context.user_data.get('state') == STATE_AWAIT_FOLDER:
        folder_path = update.message.text
        if (folder_path.lower() == "default" or folder_path.lower() == "d"):
            folder_path = default_downloads_folder
            
        if not os.path.exists(folder_path):
            await update.message.reply_text(f'The folder path "{folder_path}" does not exist. Would you like to create it? (y/n)')
            context.user_data['folder_path'] = folder_path
            context.user_data['state'] = STATE_AWAIT_FOLDER_CREATION
        else:
            await update.message.reply_text(f'Folder path set as "{folder_path}". Please send the document now.')
            context.user_data['folder_path'] = folder_path
            context.user_data['state'] = STATE_AWAIT_DOCUMENT
            
async def handle_folder_creation(update: Update, context: CallbackContext):
    if context.user_data.get('state') == STATE_AWAIT_FOLDER_CREATION:
        resp = update.message.text.lower()
        folder_path = context.user_data['folder_path']
        
        if resp == 'y':
            try:
                print('making dir')
                os.makedirs(folder_path)
                print('dir made')
                context.user_data['state'] = STATE_AWAIT_DOCUMENT
            except OSError as e:
                print('Directory creation fail. Please start over.')
                context.user_data['state'] = STATE_AWAIT_FOLDER
                return
            await update.message.reply_text(f'Folder created at "{folder_path}". Please send the document now.')
            context.user_data['state'] = STATE_AWAIT_DOCUMENT
        else:
            await update.message.reply_text('Invalid folder path. File not saved.')
            context.user_data['state'] = ''
            
async def handle_document(update: Update, context: CallbackContext):
    if context.user_data.get('state') == STATE_AWAIT_DOCUMENT:
        folder_path = context.user_data['folder_path']
        # get media type
        media = None
        file_type = None

        if update.message.document:
            media = update.message.document
            file_type = 'document'
        elif update.message.photo:
            media = update.message.photo[-1]
            file_type = 'photo'
        elif update.message.video:
            media = update.message.video
            file_type = 'video'
        elif update.message.audio:
            media = update.message.audio
            file_type = 'audio'
        elif update.message.voice:
            media = update.message.voice
            file_type = 'voice'

        if media:
            file_name = media.file_name if hasattr(media, 'file_name') else f"{media.file_unique_id}.{file_type}"
            ext = get_extension(file_type)
            file_name += ext
            print(f'User ({update.message.chat.id}) sent a media: ({file_name})')
            
            resp = await handle_file_transfer(media, folder_path, file_type, file_name)
            await update.message.reply_text(resp)
        else:
            await update.message.reply_text("File type not supported")
        context.user_data['state'] = ''
    else:
        await update.message.reply_text('Please specify the path first.')

def get_extension(file_type: str) -> str:
    if file_type == 'photo':
        return '.jpg'
    elif file_type == 'video':
        return '.mp4'
    elif file_type == 'audio':
        return '.mp3'
    elif file_type == 'voice':
        return '.ogg'
    else:
        return ''
    
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type = update.message.chat.type
    text = update.message.text
    
    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    
    if (message_type in ['group', 'supergroup']):
        if (BOT_USERNAME in text):
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
        
    print('Bot: ' + response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (str(context.error) != "cannot access local variable 'folder_path' where it is not associated with a value"):
        print(f'Update {update} caused error {context.error}')
    
    
# Main
if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('sendfile', sendfile_command))

    # Messages
    app.add_handler(MessageHandler(filters.ALL & ~filters.TEXT  & ~filters.COMMAND, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_folder), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_folder_creation), group=0)

    # Errors
    app.add_error_handler(error)
    
    print('Polling...')
    app.run_polling(poll_interval=3)

