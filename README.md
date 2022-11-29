# Australia Weather Charts
Python app creating a weekly weather summary

## Installation
 1. Install a dashboard library [Streamlit](https://streamlit.io/)
    ```
    $ pip install streamlit
    ```
 2. Install the packages according to the configuration file requirements.txt
     ```
     $ pip install -r requirements.txt
      ```
 3. Create a Google Drive account & complete the [quickstart steps](https://developers.google.com/drive/api/quickstart/python)
 4. Get the GDrive API's token by making the following request:
      ```python
        def credentials() -> Credentials:
            SCOPES = ["https://www.googleapis.com/auth/drive.readonly", 'https://www.googleapis.com/auth/drive',
                      'https://www.googleapis.com/auth/drive.metadata.readonly']   
            creds = None
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", 'w') as token:
                    token.write(creds.to_json())
            return creds
## Update & Run:
 1. Get the historical weekly & monthly normal weather variables by running "main.py"
 
 2. Launch the app
    ```
    streamlit run Hello.py
    ```
