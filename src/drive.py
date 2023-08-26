"""
Call the Google Drive API
"""
from __future__ import print_function

import logging
import os.path
import datetime
from datetime import timedelta
import json

# pylint: disable=import-error
from worker import process

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as SaCredentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaInMemoryUpload

# pylint: disable=import-error
import pytz
from enums import Media
import helper

with open("config/config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.getLevelName(config["LogLevel"])
)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']
BILDER = "Bilder"
VIDEOS = "Videos"
TICKERBIENEN = "Tickerbienen"

class ProtestFolder:
    """
    Class holding the folder ids of a protest folder for a certain date.
    """
    def __init__(
            self,
            parent_folder_id,
            bilder_folder_id = "",
            videos_folder_id = "",
            tickerbienen_folder_id = "",
            tickerbiene_folder_id = "",
            tickerbiene_bilder_folder_id = "",
            tickerbiene_videos_folder_id = ""
        ):
        self.parent_folder_id = parent_folder_id
        self.bilder_folder_id = bilder_folder_id
        self.videos_folder_id = videos_folder_id
        self.tickerbienen_folder_id = tickerbienen_folder_id
        self.tickerbiene_folder_id = tickerbiene_folder_id
        self.tickerbiene_bilder_folder_id = tickerbiene_bilder_folder_id
        self.tickerbiene_videos_folder_id = tickerbiene_videos_folder_id

def _get_credentials() -> Credentials:
    """
    Create credentials. If a token exists use the existing token.
    """
    creds = None
    if config["USE_SERVICE_ACCOUNT"]:
        if os.path.exists('config/sa.json'):
            creds = SaCredentials.from_service_account_file('config/sa.json', scopes=SCOPES)
    else:
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('config/token.json'):
            creds = Credentials.from_authorized_user_file('config/token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'config/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('config/token.json', 'w', encoding="utf8") as token:
                token.write(creds.to_json())
    return creds

def _loop_query(query: str) -> any:
    creds = _get_credentials()

    service = build('drive', 'v3', credentials=creds)

    # pylint: disable=maybe-no-member
    results = service.files().list(
        q=query,
        pageSize=100, fields="nextPageToken, files(id, name)",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
    ).execute()
    next_page_token = results.get("nextPageToken", None)
    logging.debug(next_page_token)
    folders = results.get('files', [])

    while next_page_token is not None:
        results = service.files().list(
            q=query,
            pageToken=next_page_token, fields="nextPageToken, files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()
        next_page_token = results.get("nextPageToken", None)
        folders.extend(results.get('files', []))
    return folders

@process
def upload_file_to_folder(
        name: str, file_bytes: bytes,
        protest_folders: ProtestFolder,
        media_type: Media
    ):
    """Upload a file to the specified folder and prints file ID, folder ID
    Args: Id of the folder
    Returns: ID of the file uploaded
    :raises:
    HttpError: if a connection error occured.
    TypeError: if media type is not found.
    """
    creds = _get_credentials()
    # create drive api client
    service = build('drive', 'v3', credentials=creds)

    if media_type is Media.IMAGE:
        # Upload to Bilder
        file_format = name.rsplit('.',1)[-1]
        if file_format == name or name == "None":
            file_format="jpg"
            name = f"{name}.{file_format}"
        file_metadata = {
            'name': name,
            'parents': [protest_folders.bilder_folder_id]
        }
        media = MediaInMemoryUpload(file_bytes,
                                mimetype=f'image/{file_format}', resumable=True)
    elif media_type is Media.VIDEO:
        # Upload to Videos
        file_format = name.rsplit('.',1)[-1]
        if file_format == name or name == "None":
            file_format="mp4"
            name = f"{name}.{file_format}"
        file_metadata = {
            'name': name,
            'parents': [protest_folders.videos_folder_id]
        }
        media = MediaInMemoryUpload(file_bytes,
                    mimetype=f'video/{file_format}', resumable=True)
    else: raise TypeError('Cloud not find Media type', media_type)

    # pylint: disable=maybe-no-member
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True
        ).execute()
    uploaded_file_id = uploaded_file.get('id')
    logging.debug('File ID: "%s".' , uploaded_file_id)

    # Upload to Tickerbienen
    if media_type is Media.IMAGE:
        # Upload to Bilder
        file_metadata['parents'] = [protest_folders.tickerbiene_bilder_folder_id]
        media = MediaInMemoryUpload(file_bytes,
            mimetype=f'image/{file_format}', resumable=True)
    elif media_type is Media.VIDEO:
        # Upload to Videos
        file_metadata['parents'] = [protest_folders.tickerbiene_videos_folder_id]
        media = MediaInMemoryUpload(file_bytes,
            mimetype=f'video/{file_format}', resumable=True)
    else: raise TypeError('Cloud not find Media type', media_type)

    # pylint: disable=maybe-no-member
    uploaded_ticker_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True
        ).execute()
    uploaded_ticker_file_id = uploaded_ticker_file.get('id')

    logging.debug('File ID: "%s".' , uploaded_ticker_file_id)
    logging.info("Finished upload  %s ", name)

    return uploaded_file_id, uploaded_ticker_file_id

def _create_tickerbiene_folder(username: str, ticker_folder_id):
    #create subfolder for Tickerbiene
    file_metadata = {
        'name': username,
        'parents': [ticker_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }

    creds = _get_credentials()
    service = build('drive', 'v3', credentials=creds)

    # pylint: disable=maybe-no-member
    ticker_biene_folder = service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    ticker_biene_folder_id = ticker_biene_folder.get('id')
    logging.debug('ticker biene folder ID: "%s".', ticker_biene_folder_id)

    #create subfolder Tickerbienen/Bilder
    file_metadata = {
        'name': 'Bilder',
        'parents': [ticker_biene_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    # pylint: disable=maybe-no-member
    ticker_image_folder = service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    ticker_image_folder_id = ticker_image_folder.get('id')
    logging.debug('ticker image folder ID: "%s".', ticker_image_folder_id)

    #create subfolder Tickerbienen/Videos
    file_metadata = {
        'name': 'Videos',
        'parents': [ticker_biene_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    # pylint: disable=maybe-no-member
    ticker_videos_folder = service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    ticker_videos_folder_id = ticker_videos_folder.get('id')
    logging.debug('ticker videos folder ID: "%s".', ticker_videos_folder_id)

    return ticker_biene_folder_id, ticker_image_folder_id, ticker_videos_folder_id

def create_parent_folder(name: str, username: str) -> ProtestFolder:
    """ Create the parent folder and prints the folder ID.
    This folder is used for the protest of a day on a location.
    The location is dependend on the telegram channel the message was posted,
    Returns : Folder Id
    :raises:
    HttpError: if a connection error occured.
    """
    creds = _get_credentials()

    # create drive api client
    service = build('drive', 'v3', credentials=creds)
    # create parent folder
    if config["PROTEST_FOLDER_ID"]:
        file_metadata = {
            'name': name,
            'parents': [f"{config['PROTEST_FOLDER_ID']}"],
            'mimeType': 'application/vnd.google-apps.folder'
        }
    else:
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }


    # pylint: disable=maybe-no-member
    parent_folder = service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    parent_folder_id = parent_folder.get('id')
    logging.debug('parent folder ID: "%s".' , parent_folder_id)

    #create subfolder Bilder
    file_metadata = {
        'name': BILDER,
        'parents': [parent_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    # pylint: disable=maybe-no-member
    image_folder = service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    image_folder_id = image_folder.get('id')
    logging.debug('image folder ID: "%s".', image_folder_id)

    #create subfolder Videos
    file_metadata = {
        'name': VIDEOS,
        'parents': [parent_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    # pylint: disable=maybe-no-member
    videos_folder = service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    videos_folder_id = videos_folder.get('id')
    logging.debug('videos folder ID: "%s".', videos_folder_id)

    #create subfolder Tickerbienen
    file_metadata = {
        'name': 'Tickerbienen',
        'parents': [parent_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    # pylint: disable=maybe-no-member
    ticker_folder = service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    ticker_folder_id = ticker_folder.get('id')
    logging.debug('ticker folder ID: "%s".', ticker_folder_id)

    tb_folder_id, ti_folder_id, tv_folder_id =_create_tickerbiene_folder(
        username, 
        ticker_folder_id
    )

    return ProtestFolder(
        parent_folder_id,
        image_folder_id,
        videos_folder_id,
        ticker_folder_id,
        tb_folder_id,
        ti_folder_id,
        tv_folder_id
    )

def search_protest_folder(parent_id, username: str)-> ProtestFolder:
    """
    Search for the protest folder's subfolders of the current date.
    """

    protest_folder = ProtestFolder(parent_id)

    query = f"mimeType='application/vnd.google-apps.folder' and \
            ('{parent_id}' in parents) and \
            trashed=false"
    folders = _loop_query(query)
    
    for folder in folders:
        logging.debug("%s (%s)", folder['name'],folder['id'])
        if folder['name'] == BILDER:
            protest_folder.bilder_folder_id = folder['id']
        if folder['name'] == VIDEOS:
            protest_folder.videos_folder_id = folder['id']
        if folder['name'] == TICKERBIENEN:
            protest_folder.tickerbienen_folder_id = folder['id']

    query = f"mimeType='application/vnd.google-apps.folder' and \
            ('{protest_folder.tickerbienen_folder_id}' in parents) and \
            trashed=false"
    folders = _loop_query(query)

    for folder in folders:
        logging.debug("%s (%s)", folder['name'],folder['id'])
        if folder['name'] == username:
            protest_folder.tickerbiene_folder_id = folder['id']
    if protest_folder.tickerbiene_folder_id  == "":
        tb_folder_id, ti_folder_id, tv_folder_id = _create_tickerbiene_folder(
            username, 
            protest_folder.tickerbienen_folder_id
        )
        protest_folder.tickerbiene_folder_id = tb_folder_id
        protest_folder.tickerbiene_bilder_folder_id = ti_folder_id
        protest_folder.tickerbiene_videos_folder_id = tv_folder_id
    else:
        query = f"mimeType='application/vnd.google-apps.folder' and \
                ('{protest_folder.tickerbiene_folder_id}' in parents) and \
                trashed=false"
        folders = _loop_query(query)

        for folder in folders:
            logging.debug("%s (%s)", folder['name'],folder['id'])
            if folder['name'] == BILDER:
                protest_folder.tickerbiene_bilder_folder_id = folder['id']
            if folder['name'] == VIDEOS:
                protest_folder.tickerbiene_videos_folder_id = folder['id']

    return protest_folder

def manage_folder(date: datetime, username: str, channel_name: str = None, location: str = None) -> ProtestFolder:
    """
    Get a list for all folders in the shared drive of the Presse Ag 
    in the Subfolder ./Pressemitteilungen/Protest
    Returns : Folder Id
    :raises:
    HttpError: if a connection error occured.
    """
    # pylint: disable=maybe-no-member
    if config["PROTEST_FOLDER_ID"]:
        query = f"mimeType='application/vnd.google-apps.folder' and \
            ('{config['PROTEST_FOLDER_ID']}' in parents) and \
            trashed=false"
    else:
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"

    folders = _loop_query(query)


    tz_date = date.replace(tzinfo=pytz.timezone(config["TIMEZONE"])).astimezone()
    date = date + timedelta(minutes=5)
    if helper.is_dst(pytz.timezone(config["TIMEZONE"])):
        tz_date = tz_date + timedelta(hours=1)

    logging.debug('Files:')
    for folder in folders:
        logging.debug("%s (%s)", folder['name'], folder['id'])
        folder_name_split = folder['name'].split(' ')
        fodler_name_date = folder_name_split[0]
        # Check if the folder was created by the bot.
        # If the folder has no name assume the folder was not created by the bot
        logging.debug("folder name split %s", folder_name_split)
        logging.debug("folder name date %s", fodler_name_date)
        if len(folder_name_split) > 1:
            folder_name_bot = folder_name_split[1]
        else:
            folder_name_bot = ""
        if len(folder_name_split) > 2:
            folder_name_channel_name = ' '.join(folder_name_split[2:])
        else:
            folder_name_bot = ""
        logging.debug("channel_name %s", folder_name_channel_name)
        logging.debug("folder name channel name %s", folder_name_channel_name)
        if fodler_name_date == tz_date.date().isoformat() \
        and folder_name_bot == "Bot" \
        and (channel_name is None or folder_name_channel_name == channel_name):
            return search_protest_folder(folder['id'], username)
    if location is not None:
        parent_folder_name = f"{tz_date.date().isoformat()} Bot {location}"
    elif channel_name is not None: 
        parent_folder_name = f"{tz_date.date().isoformat()} Bot {channel_name}"
    else:
        parent_folder_name = f"{tz_date.date().isoformat()} Bot  "
    parent_folder = create_parent_folder(parent_folder_name, username)

    return parent_folder

QUERRY_MAIN = "mimeType='application/vnd.google-apps.folder' and trashed=false"
if __name__ == '__main__':
    try:

        # pylint: disable=maybe-no-member
        folders_main = _loop_query(QUERRY_MAIN)

        if not folders_main:
            logging.warning('No folder found.')
        logging.info('Files:')
        for folder_main in folders_main:
            logging.info("%s (%s)", folder_main['name'],folder_main['id'])
    except HttpError as main_http_error:
        # TODO(developer) - Handle errors from drive API.
        logging.error('An error occurred: %s',main_http_error)
