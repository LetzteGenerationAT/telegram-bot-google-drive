"""
Call the Google Drive API
"""
from __future__ import print_function

import logging


import os.path
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# pylint: disable=import-error
import pytz
import config
from enums import Media
import helper
from datetime import timedelta


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
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
            tickerbienen_bilder_folder_id = "",
            tickerbienen_videos_folder_id = ""
        ):
        self.parent_folder_id = parent_folder_id
        self.bilder_folder_id = bilder_folder_id
        self.videos_folder_id = videos_folder_id
        self.tickerbienen_folder_id = tickerbienen_folder_id
        self.tickerbienen_bilder_folder_id = tickerbienen_bilder_folder_id
        self.tickerbienen_videos_folder_id = tickerbienen_videos_folder_id

def _get_credentials() -> Credentials:
    """
    Create credentials. If a token exists use the existing token.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w', encoding="utf8") as token:
            token.write(creds.to_json())
    return creds

def upload_image_to_folder(name: str, path: str, protest_folders: ProtestFolder, media_type: Media):
    """Upload a file to the specified folder and prints file ID, folder ID
    Args: Id of the folder
    Returns: ID of the file uploaded
    """
    creds = _get_credentials()

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        if media_type is Media.IMAGE:
            # Upload to Bilder
            file_metadata = {
                'name': name,
                'parents': [protest_folders.bilder_folder_id]
            }
        elif media_type is Media.VIDEO:
            # Upload to Videos
            file_metadata = {
                'name': name,
                'parents': [protest_folders.videos_folder_id]
            }
        else: raise TypeError('Cloud not find Media type', media_type)

        media = MediaFileUpload(path,
                                mimetype='image/jpeg', resumable=True)
        # pylint: disable=maybe-no-member
        bilder_file = service.files().create(
            body=file_metadata, 
            media_body=media,
            fields='id',
            supportsAllDrives=True
            ).execute()
        bilder_image_id = bilder_file.get('id')
        logging.debug('File ID: "%s".' , bilder_image_id)

        # Upload to Tickerbienen
        if media_type is Media.IMAGE:
            # Upload to Bilder
            file_metadata = {
                'name': name,
                'parents': [protest_folders.tickerbienen_bilder_folder_id]
            }
        elif media_type is Media.VIDEO:
            # Upload to Videos
            file_metadata = {
                'name': name,
                'parents': [protest_folders.tickerbienen_videos_folder_id]
            }
        else: raise TypeError('Cloud not find Media type', media_type)
        media = MediaFileUpload(path,
                                mimetype='image/jpeg', resumable=True)
        # pylint: disable=maybe-no-member
        ticker_file = service.files().create(
            body=file_metadata, 
            media_body=media,
            fields='id',
            supportsAllDrives=True
            ).execute()
        ticker_image_id = ticker_file.get('id')
        logging.debug('File ID: "%s".' , ticker_image_id)

        return bilder_image_id, ticker_image_id

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None
    except TypeError as error:
        print(F'An error occurred: {error}')
        return None

def create_folder(name: str) -> ProtestFolder:
    """ Create a folder and prints the folder ID
    Returns : Folder Id
    """
    creds = _get_credentials()

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)
        # create parent folder
        if config.PROTEST_FOLDER_ID:
            file_metadata = {
                'name': name,
                'parents': [f'{config.PROTEST_FOLDER_ID}'],
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

        #create subfolder Tickerbienen/Bilder
        file_metadata = {
            'name': 'Bilder',
            'parents': [ticker_folder_id],
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
            'parents': [ticker_folder_id],
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

        return ProtestFolder(
            parent_folder_id,
            image_folder_id,
            videos_folder_id,
            ticker_folder_id,
            ticker_image_folder_id,
            ticker_videos_folder_id
        )

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None

def search_protest_folder(parent_id)-> ProtestFolder:
    """
    Search for the protest folder's subfolders of the current date.
    """

    protest_folder = ProtestFolder(parent_id)

    creds = _get_credentials()

    try:
        service = build('drive', 'v3', credentials=creds)

        # pylint: disable=maybe-no-member
        results = service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and \
                ('{parent_id}' in parents) and \
                trashed=false",
            pageSize=10, fields="nextPageToken, files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            ).execute()
        folders = results.get('files', [])
        
        for folder in folders:
            logging.debug("%s (%s)", folder['name'],folder['id'])
            if folder['name'] == BILDER:
                protest_folder.bilder_folder_id = folder['id']
            if folder['name'] == VIDEOS:
                protest_folder.videos_folder_id = folder['id']
            if folder['name'] == TICKERBIENEN:
                protest_folder.tickerbienen_folder_id = folder['id']

        results = service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and \
                ('{protest_folder.tickerbienen_folder_id}' in parents) and \
                trashed=false",
            pageSize=10, fields="nextPageToken, files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            ).execute()
        folders = results.get('files', [])
        for folder in folders:
            logging.debug("%s (%s)", folder['name'],folder['id'])
            if folder['name'] == BILDER:
                protest_folder.tickerbienen_bilder_folder_id = folder['id']
            if folder['name'] == VIDEOS:
                protest_folder.tickerbienen_videos_folder_id = folder['id']

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        logging.error('An error occurred: %s',error)
    return protest_folder

def manage_folder(date: datetime, location: str = None) -> ProtestFolder:
    """
    Get a list for all folders in the shared drive of the Presse Ag 
    in the Subfolder ./Pressemitteilungen/Protest
    Returns : Folder Id
    """
    creds = _get_credentials()
    try:
        service = build('drive', 'v3', credentials=creds)

        # pylint: disable=maybe-no-member
        if config.PROTEST_FOLDER_ID:
            query = f"mimeType='application/vnd.google-apps.folder' and \
                ('{config.PROTEST_FOLDER_ID}' in parents) and \
                trashed=false"
        else:
            query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            pageSize=10, fields="nextPageToken, files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True).execute()
        folders = results.get('files', [])

        tz_date = date.replace(tzinfo=pytz.timezone(config.TIMEZONE)).astimezone()
        if helper.is_dst(pytz.timezone(config.TIMEZONE)):
            tz_date = tz_date + timedelta(hours=1)

        logging.debug('Files:')
        for folder in folders:
            logging.debug("%s (%s)", folder['name'],folder['id'])
            fodler_name_date = folder['name'].split(' ')[0]
            if fodler_name_date == tz_date.date().isoformat():
                return search_protest_folder(folder['id'])
        if location is None:
            name = tz_date.date().isoformat()
        else:
            name = f"{tz_date.date().isoformat()} {location}"
        protest_folder = create_folder(name)

        return protest_folder
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        logging.error('An error occurred: %s',error)


if __name__ == '__main__':
    creds_main = _get_credentials()
    try:
        service_main = build('drive', 'v3', credentials=creds_main)

        # pylint: disable=maybe-no-member
        results_main = service_main.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=10, fields="nextPageToken, files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True, ).execute()
        folders_main = results_main.get('files', [])

        if not folders_main:
            logging.warning('No folder found.')
        logging.info('Files:')
        for folder_main in folders_main:
            logging.info("%s (%s)", folder_main['name'],folder_main['id'])
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        logging.error('An error occurred: %s',error)