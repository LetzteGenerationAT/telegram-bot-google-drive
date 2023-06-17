'''
Telegram bot to automatically upload files from a telegram group to google drive
'''
import logging
import os
from datetime import timedelta
import helper
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes
# pylint: disable=import-error
import pytz
from enums import Media
import config
import drive
import maps


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def _download_document_file(update: Update) -> str:
    try:
        file = await update.effective_message.document.get_file()
        return await file.download_to_drive()
    except Exception as error:
        # TODO(developer) - Handle errors.
        logging.error('An error occurred: %s',error) 

async def _upload_document_file(
        protest_folders,
        path: str,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        media_type: Media
    ):
    try:
        # Handle error while creating or searching protest folder.
        if protest_folders is None:
            logging.error("Could not find or create protest folders.")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="bot received document file but could not create protest folders. \
                Please try again. If the error persits contact it@letztegeneration.at."
            )
            return
        else:
            date = update.effective_message.date.replace(tzinfo=pytz.timezone(config.TIMEZONE)).astimezone()
            if helper.is_dst(pytz.timezone(config.TIMEZONE)):
                date = date + timedelta(hours=1)
            username = update.effective_message.from_user.username
            document_filename = update.effective_message.document.file_name
            file_name = f"{date.isoformat()}_{username}_{document_filename}"
            drive.upload_file_to_folder(file_name, path, protest_folders, media_type)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="bot received document file"
            )
    except Exception as error:
        # TODO(developer) - Handle errors.
        logging.error('An error occurred: %s',error) 

async def document_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """An uncompressed image is received as attachment. Upload the image to google drive."""
    image_path = await _download_document_file(update)
    protest_folders = drive.manage_folder(update.effective_message.date)
    # Upload image to drive
    await _upload_document_file(protest_folders, image_path, update, context, Media.IMAGE)
    # Delete local file 
    os.remove(image_path)
    

async def document_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """An uncompressed video is received as attachment. Upload the video to google drive."""
    video_path = await _download_document_file(update)
    protest_folders = drive.manage_folder(update.effective_message.date)
    # Upload video to drive
    await _upload_document_file(protest_folders, video_path, update, context, Media.VIDEO)
    os.remove(video_path)

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A compressed photo is received. Send a message back to the sender."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""Please send the photo as attachment.
 This can be done by uncheking the \"Compress the photo\" 
 checkbox before sending the message."""
    )

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A compressed video is received. Send a message back to the sender."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""Please send the video as attachment.
 This can be done by uncheking the \"Compress the video\" 
 checkbox before sending the message."""
    )

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Demo for locaiton service.
    """
    message_location = maps.get_location(
        update.effective_message.location.latitude, 
        update.effective_message.location.longitude
    )
    print(message_location)

if __name__ == '__main__':
    app = ApplicationBuilder().token(config.TELEGRAM_API_TOKEN).build()

    document_image_handler = MessageHandler(filters.Document.IMAGE, document_image)
    document_video_handler = MessageHandler(filters.Document.VIDEO, document_video)
    photo_handler = MessageHandler(filters.PHOTO, photo)
    video_hanlder = MessageHandler(filters.VIDEO, video)
    #location_hanlder = MessageHandler(filters.LOCATION, location)

    app.add_handler(document_image_handler)
    app.add_handler(document_video_handler)
    app.add_handler(photo_handler)
    app.add_handler(video_hanlder)

    app.run_polling(allowed_updates=Update.ALL_TYPES)
