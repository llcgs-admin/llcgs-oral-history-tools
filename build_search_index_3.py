import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
PARENT_FOLDER_ID = '1gjMohkycv4-1s_ZmsPFopbkZd4Or4nQy'  # Your PDFs Folder ID

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def fetch_drive_file_map(service, folder_id):
    """Walks the specified Google Drive shared folder handling pagination."""
    file_map = {}
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"
    
    print("Querying Google Drive files...")
    while True:
        results = service.files().list(
            q=query,
            corpora='allDrives',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            spaces='drive',
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, webViewLink)",
            pageToken=page_token
        ).execute()
        
        items = results.get('files', [])
        for item in items:
            file_map[item['name']] = item['webViewLink']
            
        page_token = results.get('nextPageToken', None)
        if not page_token:
            break
            
    print(f"Mapped {len(file_map)} files from Google Drive.")
    return file_map

def build_index():
    # 1. Fetch live web view links from Google Drive
    drive_service = get_drive_service()
    drive_links = fetch_drive_file_map(drive_service, PARENT_FOLDER_ID)

    index_data = []
    
    # 2. Iterate through your local source files (or wherever your text/metadata comes from)
    # Ensure this points to your local directory containing the PDF files or text transcripts
    pdf_directory = "PDFs" 
    
    if os.path.exists(pdf_directory):
        print("Processing local files and building index records...")
        for filename in os.listdir(pdf_directory):
            if not filename.endswith('.pdf'):
                continue
                
            # Grab the secure Google Drive web link mapped from Drive
            pdf_link = drive_links.get(filename, '#')
            
            # TODO: Plug in your existing extraction logic for these fields
            # item = {
            #     "pdf_filename": filename,
            #     "pdf_link": pdf_link,
            #     "narrator_name": extract_narrator(filename),
            #     "neighborhood": extract_neighborhood(filename),
            #     "date_of_interview": extract_date(filename),
            #     "audio_filenames": extract_audio(filename),
            #     "full_text": extract_full_text(filename)
            # }
            # index_data.append(item)
            
    # 3. Write out the final index.json file
    with open('index.json', 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated index.json with {len(index_data)} records!")

if __name__ == '__main__':
    build_index()