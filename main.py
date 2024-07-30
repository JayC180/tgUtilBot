import json
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from responses import handle_response
from file_transfer import handle_file_transfer

BOT_USERNAME: Final = '' # add bot name

config_file = json.load(open("config.json"))
TOKEN = config_file["apiKey"]
chat_id = config_file["chatID"]
default_downloads_folder = config_file["defaultDownloadsFolder"]

# State keys
STATE_AWAIT_FOLDER = "await_folder"
STATE_AWAIT_DOCUMENT = "await_document"

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
        if folder_path.lower() == "default" or "d":
            folder_path = default_downloads_folder
    context.user_data['folder_path'] = folder_path
    context.user_data['state'] = STATE_AWAIT_DOCUMENT
    await update.message.reply_text(f'Folder path set as "{folder_path}". Please send the document now.')
            
async def handle_document(update: Update, context: CallbackContext):
    if context.user_data.get('state') == STATE_AWAIT_DOCUMENT:
        print(f'User ({update.message.chat.id}) sent a document: ({update.message.document.file_name})')
        document = update.message.document
        folder_path = context.user_data['folder_path']
        resp = await handle_file_transfer(document, folder_path)
        await update.message.reply_text(resp)
        context.user_data['state'] = ''
    else:
        await update.message.reply_text('Please specify the path first.')
        
# messaging
    
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
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_folder))

    # Errors
    app.add_error_handler(error)
    
    print('Polling...')
    app.run_polling(poll_interval=3)









