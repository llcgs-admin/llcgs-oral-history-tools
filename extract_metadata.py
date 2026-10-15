import os
from pypdf import PdfReader
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

# Define your local folder paths (update these to match your actual folders)
PDF_DIR = r"G:\Shared drives\LincolnOralHistory\LOH Media\PDFs"
AUDIO_DIR = r"G:\Shared drives\LincolnOralHistory\LOH Media\Audio"

def extract_pdf_cover_text(pdf_path, max_pages=3):
    """Extracts text from the first few pages of a PDF to identify names/dates."""
    text_content = ""
    try:
        reader = PdfReader(pdf_path)
        num_pages_to_read = min(len(reader.pages), max_pages)
        for i in range(num_pages_to_read):
            text_content += f"--- Page {i+1} ---\n" + reader.pages[i].extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text_content

def get_audio_metadata(mp3_path):
    """Extracts ID3 tags or basic info from an MP3 file."""
    metadata = {"filename": os.path.basename(mp3_path), "title": "", "artist": ""}
    try:
        audio = MP3(mp3_path, ID3=EasyID3)
        if audio.tags:
            metadata["title"] = audio.tags.get("title", [""])[0]
            metadata["artist"] = audio.tags.get("artist", [""])[0]
    except Exception:
        # Fallback if ID3 tags aren't present
        pass
    return metadata

def main():
    print("Scanning directories for preliminary matching analysis...")
    
    # Ensure directories exist before scanning
    if not os.path.exists(PDF_DIR) or not os.path.exists(AUDIO_DIR):
        print("Note: Please ensure 'pdfs' and 'audio' folders are created in your directory with sample files.")
        return

    print("\n--- Sample PDF Cover Text Extraction ---")
    for filename in os.listdir(PDF_DIR):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(PDF_DIR, filename)
            snippet = extract_pdf_cover_text(path, max_pages=2)
            print(f"\nFile: {filename}\nSnippet preview:\n{snippet[:300]}...\n")
            break  # Just show the first one as a test

    print("\n--- Sample Audio Metadata Scan ---")
    for filename in os.listdir(AUDIO_DIR):
        if filename.lower().endswith(".mp3"):
            path = os.path.join(AUDIO_DIR, filename)
            meta = get_audio_metadata(path)
            print(f"Audio File: {meta['filename']} | Title Tag: {meta['title']} | Artist Tag: {meta['artist']}")
            break  # Just show the first one as a test

if __name__ == "__main__":
    main()