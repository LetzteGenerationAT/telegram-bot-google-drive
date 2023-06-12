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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

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
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def upload_to_folder(name: str, image_path: str, folder_id: str):
    """Upload a file to the specified folder and prints file ID, folder ID
    Args: Id of the folder
    Returns: ID of the file uploaded
    """
    creds = _get_credentials()

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(image_path,
                                mimetype='image/jpeg', resumable=True)
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media,
                                      fields='id').execute()
        print(F'File ID: "{file.get("id")}".')
        return file.get('id')

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None

def create_folder(name: str):
    """ Create a folder and prints the folder ID
    Returns : Folder Id
    """
    creds = _get_credentials()

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {
            'name': name,
            # 'parents': '19nJVk6IIK58lq4eX4K-_ynJ4jrJjg9uZ',
            'mimeType': 'application/vnd.google-apps.folder'
        }

        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, fields='id'
                                      ).execute()
        print(F'Folder ID: "{file.get("id")}".')
        return file.get('id')

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None


def manage_folder(date: datetime, location: str):
    """
    Get a list for all folders in the shared drive of the Presse Ag 
    in the Subfolder ./Pressemitteilungen/Protest
    Returns : Folder Id
    """
    creds = _get_credentials()
    try:
        service = build('drive', 'v3', credentials=creds)

        # list all folders in the parent folder ./Pressemitteilungen/Protest
        # with the id 19nJVk6IIK58lq4eX4K-_ynJ4jrJjg9uZ
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            pageSize=10, fields="nextPageToken, files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True, ).execute()
        #  and ('19nJVk6IIK58lq4eX4K-_ynJ4jrJjg9uZ' in parents)
        items = results.get('files', [])

        if not items:
            logging.warning('No files found.')
            return
        logging.debug('Files:')
        for item in items:
            logging.debug(f"{item['name'],} ({item['id']})")
            fodler_name_date = item['name'].split(' ')[0]
            if fodler_name_date == date.date().isoformat():
                return item['id']
        if location == None:
            name = date.date().isoformat()
        else:
            name = f"{date.date().isoformat()} {location}"
        id = create_folder(name)

        return id
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        logging.error(f'An error occurred: {error}')
