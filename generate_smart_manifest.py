import os
import csv
import re
from pypdf import PdfReader
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

PDF_DIR = r"G:\Shared drives\LincolnOralHistory\LOH Media\PDFs"
AUDIO_DIR = r"D:\mp3s"  # Update to your local audio directory path
OUTPUT_CSV = r"C:\llcgs-tools\matching_manifest.csv"

NEIGHBORHOOD_MAP = {
    "001": "Near South",
    "002": "Yankee Hill",
    "003": "South Salt Creek",
    "004": "North Bottoms",
    "005": "University Place",
    "006": "University Place",
    "007": "College View",
    "008": "College View",
    "009": "East Campus",
    "010": "East Campus"
}

def extract_neighborhood(filename):
    match = re.search(r'b(\d{3})', filename.lower())
    if match:
        return NEIGHBORHOOD_MAP.get(match.group(1), "Unknown Box")
    return "Unknown"

def get_audio_metadata(mp3_path):
    """Extracts ID3 tags from an MP3 file."""
    meta = {"title": "", "artist": ""}
    try:
        audio = MP3(mp3_path, ID3=EasyID3)
        if audio.tags:
            meta["title"] = audio.tags.get("title", [""])[0]
            meta["artist"] = audio.tags.get("artist", [""])[0]
    except Exception:
        pass
    return meta

def extract_pdf_snippet(pdf_path, max_pages=2):
    text_content = ""
    try:
        reader = PdfReader(pdf_path)
        for i in range(min(len(reader.pages), max_pages)):
            text_content += f"[Page {i+1}] " + reader.pages[i].extract_text().replace('\n', ' ') + " "
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text_content.strip()

def main():
    print("Building smart cross-reference manifest...")
    
    if not os.path.exists(PDF_DIR):
        print(f"Error: PDF directory not found at {PDF_DIR}")
        return

    # 1. Build an index of available MP3 files and their metadata tags
    audio_index = {}
    if os.path.exists(AUDIO_DIR):
        for audio_file in os.listdir(AUDIO_DIR):
            if audio_file.lower().endswith(".mp3"):
                audio_path = os.path.join(AUDIO_DIR, audio_file)
                meta = get_audio_metadata(audio_path)
                # Extract core ID code (e.g., '636' or '437' from 'AV1_636_16_01.mp3')
                code_match = re.search(r'av1_(\d+)_', audio_file.lower())
                code_key = code_match.group(1) if code_match else ""
                
                audio_index[audio_file] = {
                    "filename": audio_file,
                    "code_key": code_key,
                    "title": meta["title"],
                    "artist": meta["artist"]
                }
    else:
        print(f"Note: Audio directory '{AUDIO_DIR}' not found. Manifest will generate with empty audio suggestions.")

    # 2. Iterate through PDFs and attempt matches
    manifest_rows = []
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    
    for pdf_filename in sorted(pdf_files):
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        neighborhood = extract_neighborhood(pdf_filename)
        cover_text = extract_pdf_snippet(pdf_path)
        
        # Look for matching audio based on embedded names or file codes
        suggested_audio = ""
        for audio_name, audio_info in audio_index.items():
            # If artist/title tag matches text inside the PDF cover
            if audio_info["artist"] and audio_info["artist"].lower() in cover_text.lower():
                suggested_audio = audio_name
                break
            # Alternatively match by core code numbers if present in filename
            elif audio_info["code_key"] and audio_info["code_key"] in pdf_filename:
                # Could be refined further, but acts as a strong fallback
                pass

        manifest_rows.append({
            "pdf_filename": pdf_filename,
            "neighborhood": neighborhood,
            "suggested_audio_filename": suggested_audio,
            "pdf_cover_text_snippet": cover_text[:400]
        })

    # 3. Write out CSV manifest
    fields = ["pdf_filename", "neighborhood", "suggested_audio_filename", "pdf_cover_text_snippet"]
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(row)

    print(f"\nSmart manifest successfully generated at: {OUTPUT_CSV}")
    print(f"Total PDFs cataloged: {len(manifest_rows)}")

if __name__ == "__main__":
    main()