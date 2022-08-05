import os.path
from PIL import Image
import pandas as pd
from io import BytesIO
from typing import List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload


def credentials() -> Credentials:
    SCOPES = ["https://www.googleapis.com/auth/drive.readonly", 'https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/drive.metadata.readonly']   
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(os.path.join("support_files", "token.json")):
        creds = Credentials.from_authorized_user_file(os.path.join("support_files", "token.json"), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(os.path.join("support_files", "credentials.json"), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(os.path.join("support_files", "token.json"), 'w') as token:
            token.write(creds.to_json())
    return creds


def search_file(creds: Credentials, query: str = "mimeType='text/csv'") -> List[dict]:
    """Search file in drive location
    """

    try:
        # create gmail api client
        service = build('drive', 'v3', credentials=creds)
        files = []
        page_token = None
        while True:
            # pylint: disable=maybe-no-member
            response = service.files().list(q=query,
                                            spaces='drive',
                                            fields='nextPageToken, '
                                                   'files(id, name)',
                                            pageToken=page_token).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

    except HttpError as error:
        print(F'An error occurred: {error}')
        files = None

    return files


def download_dataframe(creds: Credentials, id:str = None, filename: str = None, parse_dates=None, index_col=None) -> pd.DataFrame:
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    if not filename is None:
        found_file = search_file(creds, query=f"name = '{filename}'")[0]
        id, filename = found_file['id'], found_file['name']
    request = service.files().get_media(fileId=id)
    file = BytesIO()
    downloader = MediaIoBaseDownload(file,request)
    done = False
    while done is False:
        _,done = downloader.next_chunk()
    file.seek(0)
    
    df = pd.read_csv(file, parse_dates=parse_dates, index_col=index_col) if 'csv' in filename else pd.read_excel(file, parse_dates=parse_dates)
    
    return df


def download_image(creds: Credentials, id:str = None, filename: str = None) -> pd.DataFrame:
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    if not filename is None:
        found_file = search_file(creds, query=f"name = '{filename}'")[0]
        id, filename = found_file['id'], found_file['name']
    request = service.files().get_media(fileId=id)
    file = BytesIO()
    downloader = MediaIoBaseDownload(file,request)
    done = False
    while done is False:
        _,done = downloader.next_chunk()
    file.seek(0)
    
    # df = pd.read_csv(file) if 'csv' in filename else pd.read_excel(file, parse_dates=parse_dates)
    png = Image.open(file)
    return png


def upload_file(creds: Credentials, filename: str) -> None:
    creds = credentials()
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': filename}
    media = MediaFileUpload(filename)
    file = service.files().create(body=file_metadata, media_body=media, fields='id')
    file.execute()


def print_filenames(creds: Credentials, pageSize: int=10) -> None:
    """
    Prints the names and ids of the first files the user has access to.
    """
    try:
        service = build('drive', 'v3', credentials=creds)
        # Call the Drive v3 API
        results = service.files().list(pageSize=pageSize, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')    
        

def main():
    creds = credentials()
    # print(download_dataframe(creds=creds, filename='australia_weather.csv', parse_dates=['date']))


if __name__ == '__main__':
    main()
