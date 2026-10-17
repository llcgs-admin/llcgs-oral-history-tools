let searchIndex = [];

async function loadIndex() {
    const startTime = performance.now();
    try {
        document.getElementById('stats').textContent = 'Loading search index (large file, please wait)...';
        const response = await fetch('search_index.json');
        if (!response.ok) throw new Error('Failed to load search index.');
        
        searchIndex = await response.json();
        
        const endTime = performance.now();
        const elapsedMs = Math.round(endTime - startTime);
        
        document.getElementById('stats').textContent = `Index loaded successfully in ${elapsedMs} ms. ${searchIndex.length} transcripts available. Press Enter to search.`;
    } catch (error) {
        console.error(error);
        document.getElementById('stats').textContent = 'Error loading search index. Please ensure search_index.json is present.';
    }
}

// Strict snippet extraction with hard character caps
function findAllSnippets(fullText, queryTerms) {
    if (!fullText) return [];
    
    const snippets = [];
    const lowerText = fullText.toLowerCase();
    
    // Convert queryTerms into clean lowercase search targets (handling quoted phrases)
    const targets = queryTerms.map(term => {
        const clean = term.replace(/^"|"$/g, "").trim().toLowerCase();
        return clean;
    }).filter(t => t.length > 0 && t !== 'and' && t !== 'or');

    // Find all occurrences for each target term/phrase
    targets.forEach(target => {
        let pos = 0;
        while ((pos = lowerText.indexOf(target, pos)) !== -1) {
            // Extract a window around the match
            const start = Math.max(0, pos - 60);
            const end = Math.min(fullText.length, pos + target.length + 140);
            
            let snippetText = fullText.slice(start, end);
            if (start > 0) snippetText = "..." + snippetText;
            if (end < fullText.length) snippetText = snippetText + "...";

            // Highlight the exact match term inside the snippet
            const highlighted = highlightMatch(snippetText, target);
            
            // Prevent duplicate overlapping snippet windows
            if (!snippets.includes(highlighted)) {
                snippets.push(highlighted);
            }
            
            pos += target.length; // Move forward to find subsequent occurrences
        }
    });

    // Fallback if no specific matches found
    if (snippets.length === 0) {
        snippets.push(fullText.slice(0, 200) + "...");
    }

    return snippets;
}

// Helper to wrap matched phrases in a highlight tag
function highlightMatch(text, term) {
    const escapedTerm = term.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    const regex = new RegExp(`(${escapedTerm})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}
function highlightTerms(text, queryTerms) {
    let safeText = escapeHtml(text);
    queryTerms.forEach(term => {
        if (!term) return;
        const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi');
        safeText = safeText.replace(regex, '<mark style="background-color: #fce881; padding: 0.1em 0.2em; border-radius: 2px;">$1</mark>');
    });
    return safeText;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function renderResults(results, queryTerms) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';

    if (results.length === 0) {
        container.innerHTML = '<div class="result-card"><p>No matching oral history records found.</p></div>';
        return;
    }

    results.forEach((item) => {
        const card = document.createElement('div');
        card.className = 'result-card';

        const narrator = item.narrator_name !== "Unknown" ? item.narrator_name : item.pdf_filename.replace('.pdf', '');
        const neighborhood = item.neighborhood || "General Collection";
        const interviewDate = item.date_of_interview !== "Unknown" ? item.date_of_interview : "Date unrecorded";

        // Generate the targeted snippets
        const allSnippets = findAllSnippets(item.full_text, queryTerms);
        const maxInitialDisplay = 3;

        // 1. Header (Narrator & Neighborhood Badge)
        const headerDiv = document.createElement('div');
        headerDiv.className = 'result-header';
        headerDiv.innerHTML = `<h2 class="narrator-title">${escapeHtml(narrator)}</h2><span class="badge">${escapeHtml(neighborhood)}</span>`;
        card.appendChild(headerDiv);

        // 2. Metadata Line (Date, File Name, Match Count)
        const metaDiv = document.createElement('div');
        metaDiv.className = 'meta-info';
        metaDiv.innerHTML = `<strong>Interview Date:</strong> ${escapeHtml(interviewDate)} &bull; <strong>File:</strong> ${escapeHtml(item.pdf_filename)} &bull; <span style="color: var(--accent-color); font-weight: 600;">${allSnippets.length} match(es) in file</span>`;
        card.appendChild(metaDiv);

        // 3. Snippet Container (Only holds the targeted preview blocks)
        const snippetContainer = document.createElement('div');
        snippetContainer.className = 'snippet-container';
        
        const renderSnippetList = (snippetsToRender) => {
            snippetContainer.innerHTML = '';
            snippetsToRender.forEach(snip => {
                const snipDiv = document.createElement('div');
                snipDiv.className = 'snippet';
                snipDiv.style.marginBottom = '0.75rem';
                snipDiv.innerHTML = snip;
                snippetContainer.appendChild(snipDiv);
            });
        };

        renderSnippetList(allSnippets.slice(0, maxInitialDisplay));
        card.appendChild(snippetContainer);

        // 4. "See All" Button if more than 3 matches
        if (allSnippets.length > maxInitialDisplay) {
            const btnContainer = document.createElement('div');
            btnContainer.style.marginBottom = '1rem';
            
            const btn = document.createElement('button');
            btn.textContent = `See All (${allSnippets.length} matches)`;
            btn.style.cssText = 'background: none; border: 1px solid var(--primary-color); color: var(--primary-color); padding: 0.35rem 0.75rem; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 0.85rem;';
            
            btn.onclick = () => {
                renderSnippetList(allSnippets);
                btn.style.display = 'none';
            };
            
            btnContainer.appendChild(btn);
            card.appendChild(btnContainer);
        }

        // 5. Actions Footer (View PDF & Audio Links)
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'actions';
        let actionsHtml = `<a href="PDFs/${encodeURIComponent(item.pdf_filename)}" target="_blank">📄 View Full PDF Transcript</a>`;
        if (item.audio_filenames) {
            actionsHtml += ` <span style="color:#888;">|</span> 🎧 Audio Parts: ${escapeHtml(item.audio_filenames)}`;
        }
        actionsDiv.innerHTML = actionsHtml;
        card.appendChild(actionsDiv);

        // Append final built card
        container.appendChild(card);
    });
}
// Helper to evaluate complex search syntax ("phrases", OR, and AND)
function matchesQuery(text, queryStr) {
    if (!queryStr || !queryStr.trim()) return true;
    
    const lowerText = text.toLowerCase();
    const trimmedQuery = queryStr.trim();
    
    // 1. Handle explicit "OR" logic
    if (/\bOR\b/i.test(trimmedQuery)) {
        const parts = trimmedQuery.split(/\s+OR\s+/i);
        return parts.some(part => matchesQuery(text, part.replace(/[()]/g, "")));
    }
    
    // 2. Handle explicit "AND" logic
    if (/\bAND\b/i.test(trimmedQuery)) {
        const parts = trimmedQuery.split(/\s+AND\s+/i);
        return parts.every(part => matchesQuery(text, part.replace(/[()]/g, "")));
    }
    
    // 3. Handle outer parentheses removal if wrapping a group
    if (trimmedQuery.startsWith('(') && trimmedQuery.endsWith(')')) {
        return matchesQuery(text, trimmedQuery.slice(1, -1));
    }
    
    // 4. Handle exact phrase matching (e.g., "black smith")
    if (trimmedQuery.startsWith('"') && trimmedQuery.endsWith('"')) {
        const phrase = trimmedQuery.slice(1, -1).toLowerCase();
        return lowerText.includes(phrase);
    }
    
    // 5. Handle space-separated terms (implicit AND)
    const subTerms = trimmedQuery.match(/("[^"]+"|[^\s()]+)/g) || [];
    
    return subTerms.every(term => {
        const cleanedTerm = term.replace(/[()]/g, "").trim();
        if (!cleanedTerm || cleanedTerm.toUpperCase() === 'AND' || cleanedTerm.toUpperCase() === 'OR') return true;
        
        if (cleanedTerm.startsWith('"') && cleanedTerm.endsWith('"')) {
            return lowerText.includes(cleanedTerm.slice(1, -1).toLowerCase());
        }
        return lowerText.includes(cleanedTerm.toLowerCase());
    });
}
function handleSearch(e) {
    // If it's triggered by an Enter key or a button/input change event
    if (e.type === 'keydown' && e.key !== 'Enter') return;

    const rawQuery = e.target.value.trim();
    
    if (!rawQuery) {
        document.getElementById('resultsContainer').innerHTML = '';
        document.getElementById('stats').textContent = `Index loaded. ${searchIndex.length} transcripts available.`;
        return;
    }

    const startTime = performance.now();
    
    const filtered = searchIndex.filter(item => {
        const searchableBlob = `${item.narrator_name} ${item.neighborhood} ${item.pdf_filename} ${item.full_text}`;
        return matchesQuery(searchableBlob, rawQuery);
    });

    const endTime = performance.now();
    const elapsedMs = Math.round(endTime - startTime);

    document.getElementById('stats').textContent = `Found ${filtered.length} matching transcript(s) in ${elapsedMs} ms.`;
    
// Extract proper terms for highlighting, dropping literal operators
    let highlightTerms = rawQuery.split(/\s+(?:OR|AND)\s+/i).flatMap(part => 
        part.match(/("[^"]+"|[^\s()]+)/g) || []
    ).filter(t => {
        const upper = t.toUpperCase();
        return upper !== 'OR' && upper !== 'AND' && t.replace(/[()]/g, "").trim().length > 0;
    });
    
    if (highlightTerms.length === 0) highlightTerms = [rawQuery];
	
    renderResults(filtered, highlightTerms);
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
}

document.getElementById('searchInput').addEventListener('keydown', handleSearch);

loadIndex();