"""
Telegram bot to automatically upload files from a telegram group to google drive
"""
import logging
import os
from datetime import datetime
from datetime import timedelta
import json
import re

from googleapiclient.errors import HttpError

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes
from telegram.error import BadRequest

# pylint: disable=import-error
import pytz
import helper
from enums import Media
import drive
import maps

with open("config/config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.getLevelName(config["LogLevel"])
)

def _escape(pattern:str) -> None:
    pattern = re.escape(pattern)
    pattern = pattern.replace("_", r"\_")
    return pattern

def _get_date(update: Update) -> datetime:
    tzinfo = pytz.timezone(config["TIMEZONE"])
    date = update.effective_message.date.replace(tzinfo=tzinfo).astimezone()
    date = date + timedelta(minutes=5)
    if helper.is_dst(tzinfo):
        date = date + timedelta(hours=1)
    return date

async def _send_cloud_not_download(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, ex : Exception, media_type: Media
    ) -> None:
    try:
        await context.bot.send_message(
                chat_id=config["ERROR_MESSAGE_CHAT_ID"],
                text=fr"Cloud not *download* {media_type} \
from https://t\.me/{_escape(update.effective_user.username)} \
\({_escape(update.effective_user.first_name)} \
{_escape(update.effective_user.last_name)}\) \
    because {ex}\.",
            parse_mode="MarkdownV2"
            )
    except BadRequest as error:
        logging.exception(error)
        await context.bot.send_message(
                chat_id=config["ERROR_MESSAGE_CHAT_ID"],
                text=fr"Cloud not *download* {media_type} \
because {ex}\.",
            parse_mode="MarkdownV2"
            )

async def _send_could_not_save(
        update: Update, context: ContextTypes.DEFAULT_TYPE, 
        ex: Exception, media_type: Media
    ) -> None:
    try:
        await context.bot.send_message(
                chat_id=config["ERROR_MESSAGE_CHAT_ID"],
                text=fr"Cloud not *save* {media_type} \
from https://t\.me/{_escape(update.effective_user.username)} \
\({_escape(update.effective_user.first_name)} \
{_escape(update.effective_user.last_name)}\) \
because {ex}\.",
            parse_mode="MarkdownV2"
        )
    except BadRequest as error:
        logging.exception(error)
        await context.bot.send_message(
                chat_id=config["ERROR_MESSAGE_CHAT_ID"],
                text=fr"Cloud not *save* {media_type} \
because {ex}\.",
            parse_mode="MarkdownV2"
            )
    

async def _send_no_protest_folder(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=config["ERROR_MESSAGE_CHAT_ID"],
        text="Bot received document file but could not create protest folders."
    )

def _get_username(update: Update)-> str:
    username = update.effective_message.from_user.username
    if username is None:
        username = update.effective_message.from_user.first_name
    return username

async def _download_video(update: Update, _: ContextTypes.DEFAULT_TYPE) -> bytes:
    logging.info("Start downloading video %s", update.effective_message.video.file_name)
    video_file = await update.effective_message.video.get_file(read_timeout=600)
    with open(video_file.file_path, "rb") as video_stream:
        downloaded_file = video_stream.read()
    logging.info("Downloaded video")
    return downloaded_file

async def _download_document_file(update: Update) -> bytes:
    logging.info("Start downloading document %s", update.effective_message.document.file_name)
    document_file = await update.effective_message.document.get_file(read_timeout=600)
    with open(document_file.file_path, "rb") as document_stream:
        downloaded_file = document_stream.read()
    logging.info("Downloaded document")
    return downloaded_file


async def _upload_video(
        protest_folders,
        file_bytes: bytes,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
    logging.info("Start uploading video.")
    try:
        # Handle error while creating or searching protest folder.
        if protest_folders is None:
            logging.error("Could not find or create protest folders.")
            await _send_no_protest_folder(context)
        else:
            date = _get_date(update)
            username = _get_username(update)
            video_filename = update.effective_message.video.file_name
            file_name = f"{date.isoformat()}_{username}_{video_filename}_COMPRESSED"
            drive.upload_file_to_folder(file_name, file_bytes, protest_folders, Media.VIDEO)
            logging.info("Finished upload video %s process", file_name)
    except HttpError as error:
        logging.exception(error)
        await _send_could_not_save(update, context, error, Media.VIDEO)

async def _upload_document_file(
        protest_folders,
        file_bytes: bytes,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        media_type: Media
    ):
    logging.info("Start uploading document.")
    try:
        # Handle error while creating or searching protest folder.
        if protest_folders is None:
            logging.error("Could not find or create protest folders.")
            await _send_no_protest_folder(context)
        else:
            date = _get_date(update)
            username = _get_username(update)
            document_filename = update.effective_message.document.file_name
            file_name = f"{date.isoformat()}_{username}_{document_filename}"
            drive.upload_file_to_folder(file_name, file_bytes, protest_folders, media_type)
            logging.info("Finished upload document %s process", file_name)
    except HttpError as ex:
        logging.debug(ex)
        logging.error("An connection error occurred: %s", ex)
        await _send_could_not_save(update, context, ex, media_type)
    except TypeError as ex:
        logging.debug(ex)
        logging.error("An type error occurred: %s", ex)
        await _send_could_not_save(update, context, ex, media_type)

async def document_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """An uncompressed image is received as attachment. Upload the image to google drive."""
    username = _get_username(update)
    logging.info("Received document image from %s", username)
    try:
        file_bytes = await _download_document_file(update)
    except TimeoutError as error:
        logging.exception(error)
        await _send_cloud_not_download(update, context, error, Media.IMAGE)
        return
    date = update.effective_message.date
    try:
        protest_folders = drive.manage_folder(date, username)
    except HttpError as error:
        logging.debug(error)
        logging.error("A connection error occured %s", error)
        await _send_no_protest_folder(context)
    else:
        # Upload image to drive
        await _upload_document_file(protest_folders, file_bytes, update, context, Media.IMAGE)

async def document_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    An uncompressed video is received as attachment. 
    Upload the video to google drive.
    """
    username = _get_username(update)
    logging.info("Received document video from %s", username)
    try:
        file_bytes = await _download_document_file(update)
    except TimeoutError as error:
        logging.exception(error)
        await _send_cloud_not_download(update, context, error, Media.VIDEO)
        return
    date = update.effective_message.date
    try:
        protest_folders = drive.manage_folder(date, username)
    except HttpError as ex:
        logging.debug(ex)
        logging.error("A connection error occured %s", ex)
        await _send_no_protest_folder(context)
    else:
    # Upload video to drive
        await _upload_document_file(protest_folders, file_bytes, update, context, Media.VIDEO)

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    A compressed photo is received. 
    Send a message back to the sender.
    """
    username = _get_username(update)
    logging.info("Received photo from %s", username)
    try:
        await context.bot.send_message(
            chat_id=config["ERROR_MESSAGE_CHAT_ID"],
            text=fr"Cloud not save *photo* \
from https://t\.me/{_escape(update.effective_user.username)} \
\({_escape(update.effective_user.first_name)} \
{_escape(update.effective_user.last_name)}\) \
because it is compressed\.",
            parse_mode="MarkdownV2"
        )
    except BadRequest as error:
        logging.exception(error)
        await context.bot.send_message(
            chat_id=config["ERROR_MESSAGE_CHAT_ID"],
            text=r"Cloud not save *photo* \
because it is compressed\.",
            parse_mode="MarkdownV2"
        )

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    A compressed video is received as attachment. 
    Upload the video to google drive.
    """
    username = _get_username(update)
    logging.info("Received video from %s", username)
    try:
        file_bytes = await _download_video(update, context)
    except TimeoutError as error:
        logging.exception(error)
        if error == "File is too big":
            await context.bot.send_message(
                chat_id=config["ERROR_MESSAGE_CHAT_ID"],
                text="bot received video file but could not save the video \
                    because the file is too big."
            )
        return
    date = update.effective_message.date
    try:
        protest_folders = drive.manage_folder(date, username)
    except HttpError as ex:
        logging.debug(ex)
        logging.error("A connection error occured %s", ex)
        await _send_no_protest_folder(context)
    else:
        # Upload video to drive
        await _upload_video(protest_folders, file_bytes, update, context)


async def location(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
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
    app = ApplicationBuilder()\
        .token(os.environ['TELEGRAM_API_TOKEN'])\
            .local_mode(True).base_url(f"http://{os.environ['BASE_URL']}/bot")\
                .base_file_url(f"http://{os.environ['BASE_URL']}/bot").build()

    document_image_handler = MessageHandler(filters.Document.IMAGE, document_image)
    document_video_handler = MessageHandler(filters.Document.VIDEO, document_video)
    photo_handler = MessageHandler(filters.PHOTO, photo)
    video_hanlder = MessageHandler(filters.VIDEO, video)
    #location_hanlder = MessageHandler(filters.LOCATION, location)

    app.add_handler(document_image_handler)
    app.add_handler(document_video_handler)
    app.add_handler(photo_handler)
    app.add_handler(video_hanlder)

    app.run_polling(
        allowed_updates=Update.ALL_TYPES, 
        timeout=600, 
        read_timeout=600, 
        connect_timeout=600, 
        write_timeout=600, 
        pool_timeout=600
    )

if __name__ == '__main__':
    main()
