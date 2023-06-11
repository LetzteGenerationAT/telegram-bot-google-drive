'''
Telegram bot to automatically upload files from a telegram group to google drive
'''
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Doc for hello
    '''
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!"
    )


app = ApplicationBuilder().token(config.API_TOKEN).build()

start_handler = CommandHandler('start', start)
app.add_handler(start_handler)

app.run_polling()
