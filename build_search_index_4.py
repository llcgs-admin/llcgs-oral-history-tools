import os
import csv
import json
import re
import sys
from pypdf import PdfReader
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration Constants
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
PARENT_FOLDER_ID = '1gjMohkycv4-1s_ZmsPFopbkZd4Or4nQy'  # Your Google Drive PDFs Folder ID

PDF_DIR = r"G:\Shared drives\LincolnOralHistory\LOH Media\PDFs"
MANIFEST_CSV = r"C:\llcgs-tools\matching_manifest.csv"
OUTPUT_JSON = r"C:\llcgs-tools\search_index.json"

def get_drive_service():
    """Handles OAuth authentication and returns an authorized Google Drive API service."""
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
    """Walks the specified Google Drive shared folder handling pagination to map filename -> webViewLink."""
    file_map = {}
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"
    
    print("Querying Google Drive files (with pagination)...")
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
            
    print(f"Successfully mapped {len(file_map)} files from Google Drive.")
    return file_map

def clean_text(text):
    """Aggressively normalizes whitespace, removes duplicate overlapping text streams, and strips OCR noise."""
    if not text:
        return ""
    
    # 1. Remove repeated scanner noise symbols (e.g., ~~~, ###, ---, ^^^)
    text = re.sub(r'[~#\^_]{2,}', ' ', text)
    
    # 2. Remove isolated corrupted short tokens (e.g., single-letter/symbol garbage)
    text = re.sub(r'\b[^\w\s]{1,3}\b', ' ', text)
    
    # 3. Strip words corrupted by internal hashes or weird OCR marker characters
    text = re.sub(r'\b\w*#+\w*\b', ' ', text)
    
    # 4. Fix hyphenated words broken across line wraps
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    
    # 5. Collapse multiple spaces, tabs, and line breaks into a single clean space
    text = re.sub(r'\s+', ' ', text)
    
    cleaned = text.strip()
    
    # 6. Deduplicate accidental double-dumped text streams from pypdf layers
    half_len = len(cleaned) // 2
    if half_len > 100:
        first_half = cleaned[:half_len].strip()
        second_half = cleaned[half_len:half_len*2].strip()
        if first_half == second_half or first_half[:200] == second_half[:200]:
            cleaned = first_half

    return cleaned
    
def build_index():
    # Parse command-line parameters
    verbose = any(arg in sys.argv for arg in ["-verbose", "-v"])
    quiet = any(arg in sys.argv for arg in ["-quiet", "-q"])
    
    if not quiet:
        print("Starting search index build process with Google Drive links...")

    # 1. Connect and fetch live shareable web view links from Google Drive
    try:
        drive_service = get_drive_service()
        drive_links = fetch_drive_file_map(drive_service, PARENT_FOLDER_ID)
    except Exception as e:
        print(f"[Error] Failed to connect or fetch from Google Drive: {e}", file=sys.stderr)
        return

    if not os.path.exists(MANIFEST_CSV):
        print(f"Error: Manifest file not found at {MANIFEST_CSV}. Please generate the manifest first.")
        return

    search_entries = []

    with open(MANIFEST_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        manifest_rows = list(reader)

    total_files = len(manifest_rows)
    if not quiet:
        print(f"Processing {total_files} transcripts from manifest into search index...")

    for index, row in enumerate(manifest_rows, start=1):
        pdf_filename = row["pdf_filename"]
        neighborhood = row["neighborhood"]
        audio_filenames = row["suggested_audio_filename"]
        
        # Pull narrator name and date of interview directly from CSV manifest columns
        narrator_name = (
            row.get("narrator_name", "").strip() or 
            row.get("narrator", "").strip() or 
            row.get("narrator_filename_match", "").strip() or 
            "Unknown"
        )
        
        date_of_interview = (
            row.get("date_of_interview", "").strip() or 
            row.get("date", "").strip() or 
            "Unknown"
        )
        
        # Fetch the live secure Google Drive web view link mapped from Drive, fallback to '#' if missing
        pdf_link = drive_links.get(pdf_filename, '#')
        
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        full_text = ""

        if os.path.exists(pdf_path):
            try:
                reader = PdfReader(pdf_path)
                pages_text = []
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        pages_text.append(extracted)
                
                raw_combined = " ".join(pages_text)
                full_text = clean_text(raw_combined)

            except Exception as e:
                print(f"  [Error] Could not read {pdf_filename}: {e}", file=sys.stderr)
        else:
            print(f"  [Error] PDF missing on disk: {pdf_filename}", file=sys.stderr)

        record = {
            "id": index,
            "pdf_filename": pdf_filename,
            "pdf_link": pdf_link,  # Secure Drive web view link included here
            "neighborhood": neighborhood,
            "audio_filenames": audio_filenames,
            "narrator_name": narrator_name,
            "date_of_interview": date_of_interview,
            "full_text": full_text
        }
        
        search_entries.append(record)
        
        # Display logic based on flags
        if not quiet:
            if verbose:
                print(f"[{index}/{total_files}] File: {pdf_filename} | Narrator: {narrator_name} | Link: {pdf_link}")
                print(f"--- Full Text Snippet ---\n{full_text[:300]}...\n-------------------------")
            else:
                print(f"[{index}/{total_files}] Indexed: {pdf_filename}")

    with open(OUTPUT_JSON, mode="w", encoding="utf-8") as json_file:
        json.dump(search_entries, json_file, ensure_ascii=False, indent=2)

    if not quiet:
        print(f"\nSearch index successfully built and saved to: {OUTPUT_JSON}")
        print(f"Total searchable transcripts compiled: {len(search_entries)}")

if __name__ == "__main__":
    build_index()