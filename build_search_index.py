import os
import csv
import json
import re
import sys
from pypdf import PdfReader

PDF_DIR = r"G:\Shared drives\LincolnOralHistory\LOH Media\PDFs"
MANIFEST_CSV = r"C:\llcgs-tools\matching_manifest.csv"
OUTPUT_JSON = r"C:\llcgs-tools\search_index.json"

def clean_text(text):
    """Aggressively normalizes whitespace and strips out OCR artifact noise."""
    if not text:
        return ""
    
    # Remove repeated scanner noise symbols (e.g., ~~~, ###, ---, ^^^)
    text = re.sub(r'[~#\^_]{2,}', ' ', text)
    
    # Remove isolated corrupted short tokens (e.g., single-letter/symbol garbage like )pSt—)
    text = re.sub(r'\b[^\w\s]{1,3}\b', ' ', text)
    
    # Strip words corrupted by internal hashes or weird OCR marker characters
    text = re.sub(r'\b\w*#+\w*\b', ' ', text)
    
    # Fix hyphenated words broken across line wraps
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    
    # Collapse multiple spaces, tabs, and line breaks into a single clean space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()
    
def build_index():
    # Parse command-line parameters
    verbose = any(arg in sys.argv for arg in ["-verbose", "-v"])
    quiet = any(arg in sys.argv for arg in ["-quiet", "-q"])
    
    if not quiet:
        print("Starting search index build process...")

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
        
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        
        full_text = ""
        narrator_name = "Unknown"
        date_of_interview = "Unknown"

        if os.path.exists(pdf_path):
            try:
                reader = PdfReader(pdf_path)
                pages_text = []
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        pages_text.append(extracted)
                
                full_text = clean_text(" ".join(pages_text))
                
                # Attempt to extract Narrator Name
                name_match = re.search(r'Narrator[\s\']s\s+name[:\s]+([^\n\r]+)', full_text, re.IGNORECASE)
                if name_match:
                    narrator_name = name_match.group(1).strip()

                # Attempt to extract Interview Date
                date_match = re.search(r'Date\s+of\s+interview[:\s]+([^\n\r]+)', full_text, re.IGNORECASE)
                if date_match:
                    date_of_interview = date_match.group(1).strip()

            except Exception as e:
                print(f"  [Error] Could not read {pdf_filename}: {e}", file=sys.stderr)
        else:
            print(f"  [Error] PDF missing on disk: {pdf_filename}", file=sys.stderr)

        record = {
            "id": index,
            "pdf_filename": pdf_filename,
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
                print(f"[{index}/{total_files}] File: {pdf_filename} | Narrator: {narrator_name}")
                print(f"--- Full Text Snippet ---\n{full_text}\n-------------------------")
            else:
                # Default behavior: progress counter and file name
                print(f"[{index}/{total_files}] Indexed: {pdf_filename}")

    with open(OUTPUT_JSON, mode="w", encoding="utf-8") as json_file:
        json.dump(search_entries, json_file, ensure_ascii=False, indent=2)

    if not quiet:
        print(f"\nSearch index successfully built and saved to: {OUTPUT_JSON}")
        print(f"Total searchable transcripts compiled: {len(search_entries)}")

if __name__ == "__main__":
    build_index()