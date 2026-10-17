import os
import csv
import re
from pypdf import PdfReader
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

PDF_DIR = r"G:\Shared drives\LincolnOralHistory\LOH Media\PDFs"
AUDIO_DIR = r"D:\mp3s"
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
    print("Building multi-part audio cross-reference manifest...")
    
    if not os.path.exists(PDF_DIR):
        print(f"Error: PDF directory not found at {PDF_DIR}")
        return

    # 1. Index all audio files and extract metadata tags
    audio_list = []
    if os.path.exists(AUDIO_DIR):
        for audio_file in os.listdir(AUDIO_DIR):
            if audio_file.lower().endswith(".mp3"):
                audio_path = os.path.join(AUDIO_DIR, audio_file)
                meta = get_audio_metadata(audio_path)
                
                # Extract core interview tracking codes (e.g., '437' from 'AV1_437_01_01.mp3')
                code_match = re.search(r'av1_(\d+)_', audio_file.lower())
                core_code = code_match.group(1) if code_match else ""
                
                audio_list.append({
                    "filename": audio_file,
                    "core_code": core_code,
                    "title": meta["title"],
                    "artist": meta["artist"]
                })
    else:
        print(f"Note: Audio directory '{AUDIO_DIR}' not found.")

    # 2. Process PDFs and group multiple matching audio parts
    manifest_rows = []
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    
    for pdf_filename in sorted(pdf_files):
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        neighborhood = extract_neighborhood(pdf_filename)
        cover_text = extract_pdf_snippet(pdf_path)
        
        matched_audios = []
        
        # Check every audio file for a match against this specific PDF
        for audio in audio_list:
            is_match = False
            
            # Match 1: Artist ID3 tag is found inside the PDF cover text (e.g., "Mrs. Luther Allen")
            if audio["artist"] and audio["artist"].lower() in cover_text.lower():
                is_match = True
            
            # Match 2: Core file sequence code matches numbers embedded in the PDF filename or text
            elif audio["core_code"] and audio["core_code"] in pdf_filename:
                is_match = True
                
            if is_match and audio["filename"] not in matched_audios:
                matched_audios.append(audio["filename"])

        # Join multiple parts with a comma (e.g., "AV1_437_01_01.mp3, AV1_437_01_02.mp3")
        suggested_audio_str = ", ".join(sorted(matched_audios))

        manifest_rows.append({
            "pdf_filename": pdf_filename,
            "neighborhood": neighborhood,
            "suggested_audio_filename": suggested_audio_str,
            "pdf_cover_text_snippet": cover_text[:400]
        })

    # 3. Output CSV manifest
    fields = ["pdf_filename", "neighborhood", "suggested_audio_filename", "pdf_cover_text_snippet"]
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(row)

    print(f"\nMulti-part manifest successfully generated at: {OUTPUT_CSV}")
    print(f"Total PDFs processed: {len(manifest_rows)}")

if __name__ == "__main__":
    main()