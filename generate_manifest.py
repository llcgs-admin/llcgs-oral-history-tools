import os
import csv
import re
from pypdf import PdfReader

PDF_DIR = r"G:\Shared drives\LincolnOralHistory\LOH Media\PDFs"
OUTPUT_CSV = r"C:\llcgs-tools\matching_manifest.csv"

# Neighborhood mapping dictionary based on box numbers
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

def extract_neighborhood_from_filename(filename):
    """Searches for pattern like 'b001' or 'b010' to determine neighborhood."""
    match = re.search(r'b(\d{3})', filename.lower())
    if match:
        box_num = match.group(1)
        return NEIGHBORHOOD_MAP.get(box_num, "Unknown Box")
    return "Unknown"

def extract_pdf_cover_text(pdf_path, max_pages=3):
    """Extracts text from the first few pages to identify interviewee names/dates."""
    text_content = ""
    try:
        reader = PdfReader(pdf_path)
        num_pages_to_read = min(len(reader.pages), max_pages)
        for i in range(num_pages_to_read):
            text_content += f"[Page {i+1}] " + reader.pages[i].extract_text().replace('\n', ' ') + " "
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text_content.strip()

def main():
    print("Scanning PDF directory and mapping neighborhoods...")
    
    if not os.path.exists(PDF_DIR):
        print(f"Error: The directory '{PDF_DIR}' does not exist.")
        return

    manifest_rows = []
    
    for filename in sorted(os.listdir(PDF_DIR)):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(PDF_DIR, filename)
            neighborhood = extract_neighborhood_from_filename(filename)
            cover_snippet = extract_pdf_cover_text(path, max_pages=3)
            
            manifest_rows.append({
                "pdf_filename": filename,
                "neighborhood": neighborhood,
                "suggested_audio_filename": "", # Ready for your MP3 match mapping
                "pdf_cover_text_snippet": cover_snippet[:500]
            })

    keys = ["pdf_filename", "neighborhood", "suggested_audio_filename", "pdf_cover_text_snippet"]
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(row)

    print(f"\nManifest successfully generated at: {OUTPUT_CSV}")
    print(f"Total PDFs processed: {len(manifest_rows)}")

if __name__ == "__main__":
    main()