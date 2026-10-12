Updated Project Spec (v1.1)
Core Architecture & Components
Storage & Hosting:

PDFs stored in Google Drive folders organized by neighborhood (Public view links enabled).

MP3 files stored in Google Drive (Public view links enabled).

Static web front-end hosted on GitHub Pages (such as your LLCGS Search UI repository).

Data Mapping Layer (mapping_table.csv / Google Sheet):

Bridges each PDF transcript to its corresponding MP3 audio file.

Enhanced with AI Matching: Populated via an automated Python/LLM script that parses messy PDF cover text and audio metadata to match interviewees, then verified via Google Sheets.

Fields: pdf_filename, neighborhood, audio_filename, interviewee_name, drive_pdf_id, drive_mp3_id.

Batch Indexing Pipeline (Python):

Reads PDFs and MP3 links via the mapping table, extracts full-text search tokens, and outputs search_index.json.

Client Application (app.js + index.html):

Client-side search engine querying search_index.json.

Neighborhood filtering.

Snippet rendering with inline PDF links and HTML5 audio player controls.