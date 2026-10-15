# LLCGS Oral History Search Project: Design Spec (v1.1)

## Core Architecture & Components
1. **Storage & Hosting:** 
   * PDFs stored in Google Drive folders organized by neighborhood (Public view links enabled).
   * MP3 files stored in Google Drive (Public view links enabled).
   * Static web front-end hosted on GitHub Pages (e.g., [LLCGS Search UI repository](https://llcgs-admin.github.io/llcgs-search-ui/)).
2. **Data Mapping Layer (`matching_manifest.csv` / Google Sheet):**
   * Bridges each PDF transcript to its corresponding MP3 audio file.
   * **Neighborhood Convention:** PDF filenames include a lower-case `b` followed by a 3-digit box number (e.g., `b001` through `b010`) which automatically determines the neighborhood based on the historical archive box contents:
     * **b001:** Near South
     * **b002:** Yankee Hill
     * **b003:** South Salt Creek
     * **b004:** North Bottoms
     * **b005 & b006:** University Place
     * **b007 & b008:** College View
     * **b009 & b010:** East Campus
   * **AI-Assisted Matching:** Populated via a Python script parsing messy PDF cover text snippets alongside audio metadata sequences to build the cross-reference manifest, verified via Google Sheets.
   * Fields: `pdf_filename`, `neighborhood`, `suggested_audio_filename`, `pdf_cover_text_snippet`, `drive_pdf_id`, `drive_mp3_id`.
3. **Batch Indexing Pipeline (Python):**
   * Reads PDFs and MP3 links via the mapping table, extracts full-text search tokens, and outputs `search_index.json`.
4. **Client Application (`app.js` + `index.html`):**
   * Client-side search engine querying `search_index.json`.
   * Neighborhood filtering.
   * Snippet rendering with inline PDF links and HTML5 audio player controls.