'''
Telegram bot to automatically upload files from a telegram group to google drive
'''
import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes
import config
import drive

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def document_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """An uncompressed image is received as attachment. Upload the image to google drive."""
    drive.manage_folder(update.effective_message.date)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="bot received document image"
    )

async def document_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """An uncompressed video is received as attachment. Upload the video to google drive."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="bot received document video"
    )

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A compressed photo is received. Send a message back to the sender."""
    await context.bot.send_message(
        chat_id=update.effective_message.from_user.id,
        text="""Please send the photo as attachment.
 This can be done by uncheking the \"Compress the photo\" 
 checkbox before sending the message."""
    )

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A compressed video is received. Send a message back to the sender."""
    await context.bot.send_message(
        chat_id=update.effective_message.from_user.id,
        text="""Please send the video as attachment.
 This can be done by uncheking the \"Compress the video\" 
 checkbox before sending the message."""
    )



if __name__ == '__main__':
    app = ApplicationBuilder().token(config.TELEGRAM_API_TOKEN).build()

    document_image_handler = MessageHandler(filters.Document.IMAGE, document_image)
    document_video_handler = MessageHandler(filters.Document.VIDEO, document_video)
    photo_handler = MessageHandler(filters.PHOTO, photo)
    video_hanlder = MessageHandler(filters.VIDEO, video)

    app.add_handler(document_image_handler)
    app.add_handler(document_video_handler)
    app.add_handler(photo_handler)
    app.add_handler(video_hanlder)

    app.run_polling(allowed_updates=Update.ALL_TYPES)
