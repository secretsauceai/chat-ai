
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ApplicationBuilder, CallbackQueryHandler
import requests
import toml
import os
import json

# Define the Telegram bot token
try:
    TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    PORT = os.environ['PORT']
    TEXT_GENERATION_HOST = os.environ['TEXT_GENERATION_HOST']
    config = {'telegram_bot_token': TELEGRAM_BOT_TOKEN, 'port': PORT, 'text_generation_host': TEXT_GENERATION_HOST}

except:
    config = toml.load('../config/config.toml')
    TELEGRAM_BOT_TOKEN = config['telegram_bot_token']
    TEXT_GENERATION_HOST = config['text_generation_host']
    PORT = config['port']

SERVICE_URI = f"http://{TEXT_GENERATION_HOST}:{PORT}"

# Define the handler function for the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hi! Send me a message and I'll generate some text for you.")

async def generate_text(update: Update, context) -> None:
    input_prompt = update.message.text
    headers = {'Content-type': 'application/json'}
    await context.bot.sendChatAction(chat_id=update.message.chat_id, action=constants.ChatAction.TYPING)
    response = requests.post(f'{SERVICE_URI}/generate_text', json={'input_prompt': input_prompt}, headers=headers).json()
    generated_text = response['generated_text']
    #TODO: How do I pass the response_id to the button_click function?
    response_id = response['response_id']

    upvote_data = json.dumps({"action": "upvote", "id": response_id, "chat_id": update.message.chat_id })
    downvote_data = json.dumps({"action": "downvote", "id": response_id, "chat_id": update.message.chat_id })
    
    # Create an InlineKeyboardMarkup with upvote and downvote buttons
    keyboard = [[
        InlineKeyboardButton("👍", callback_data=upvote_data), 
        InlineKeyboardButton("👎", callback_data=downvote_data)
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the generated text with the InlineKeyboardMarkup
    await update.message.reply_text(generated_text, reply_markup=reply_markup)

# Define a handler function for button clicks
async def button_click(update: Update, context) -> None:
    query = update.callback_query
    data = json.loads(query.data)

    # Update the upvote or downvote count based on the button that was clicked
    if data['action'] == "upvote":
        vote = 1
    elif data['action'] == "downvote":
        vote = -1

    # Send a request to the API with the vote count
    headers = {'Content-type': 'application/json'}
    payload = {'response_id': data['id'], 'vote': vote}
    requests.post(f'{SERVICE_URI}/vote', json=payload, headers=headers)

    await context.bot.sendMessage(chat_id=data['chat_id'], text='Thanks for your vote.') # removed: reply_markup=[]

application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

application.add_handler(CommandHandler('start', start))
application.add_handler(MessageHandler(filters.TEXT, generate_text))
application.add_handler(CallbackQueryHandler(button_click))

application.run_polling()
