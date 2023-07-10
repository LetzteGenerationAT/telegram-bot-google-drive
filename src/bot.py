"""
Telegram bot to automatically upload files from a telegram group to google drive
"""
import logging
import os
from datetime import timedelta
import json

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes

# pylint: disable=import-error
import pytz
import helper
from enums import Media
import drive
import maps

with open("config/config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def _get_username(update: Update)-> str:
    username = update.effective_message.from_user.username
    if username is None:
        username = update.effective_message.from_user.first_name
    return username

async def _download_document_file(update: Update) -> bytes:
    try:
        file = await update.effective_message.document.get_file()
        downloaded_file = await file.download_as_bytearray()
        return bytes(downloaded_file)
    except Exception as error:
        # TODO(developer) - Handle errors.
        logging.error('An error occurred: %s',error)

async def _upload_document_file(
        protest_folders,
        file_bytes: bytes,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        media_type: Media
    ):
    try:
        # Handle error while creating or searching protest folder.
        if protest_folders is None:
            logging.error("Could not find or create protest folders.")
            await context.bot.send_message(
                chat_id=config["ERROR_MESSAGE_CHAT_ID"],
                reply_to_message_id=update.effective_message.id,
                text="bot received document file but could not create protest folders. \
                Please try again. If the error persits contact it@letztegeneration.at."
            )
        else:
            tzinfo = pytz.timezone(config["TIMEZONE"])
            date = update.effective_message.date.replace(tzinfo=tzinfo).astimezone()
            date = date + timedelta(minutes=5)
            if helper.is_dst(tzinfo):
                date = date + timedelta(hours=1)
            username = _get_username(update)
            document_filename = update.effective_message.document.file_name
            file_name = f"{date.isoformat()}_{username}_{document_filename}"
            drive.upload_file_to_folder(file_name, file_bytes, protest_folders, media_type)
    except Exception as error:
        # TODO(developer) - Handle errors.
        logging.error('An error occurred: %s',error)
        await context.bot.send_message(
            chat_id=config["ERROR_MESSAGE_CHAT_ID"],
            text=f"Cloud not save *{media_type}* \
from https://t.me/{update.effective_user.username} \
({update.effective_user.first_name} \
{update.effective_user.last_name}) \
because {error}.",
        parse_mode="markdown"
        )

async def document_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """An uncompressed image is received as attachment. Upload the image to google drive."""
    file_bytes = await _download_document_file(update)
    username = _get_username(update)
    date = update.effective_message.date
    protest_folders = drive.manage_folder(date, username)
    # Upload image to drive
    await _upload_document_file(protest_folders, file_bytes, update, context, Media.IMAGE)

async def document_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    An uncompressed video is received as attachment. 
    Upload the video to google drive.
    """
    file_bytes = await _download_document_file(update)
    username = _get_username(update)
    date = update.effective_message.date
    protest_folders = drive.manage_folder(date, username)
    # Upload video to drive
    await _upload_document_file(protest_folders, file_bytes, update, context, Media.VIDEO)

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    A compressed photo is received. 
    Send a message back to the sender.
    """
    await context.bot.send_message(
        chat_id=config["ERROR_MESSAGE_CHAT_ID"],
        text=f"Cloud not save *photo* \
from https://t.me/{update.effective_user.username} \
({update.effective_user.first_name} \
{update.effective_user.last_name}) \
because it is compressed.",
        parse_mode="markdown"
    )

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    A compressed video is received. 
    Send a message back to the sender.
    """
    await context.bot.send_message(
        chat_id=config["ERROR_MESSAGE_CHAT_ID"],
        text=f"Cloud not save *video* \
from https://t.me/{update.effective_user.username} \
({update.effective_user.first_name} \
{update.effective_user.last_name}) \
because it is compressed.",
        parse_mode="markdown"
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

def main():
    """
    Create Telegram bot, add handler and run polling.
    """
    app = ApplicationBuilder().token(os.environ['TELEGRAM_API_TOKEN']).build()

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

if __name__ == '__main__':
    main()
