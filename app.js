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

// Optimized snippet extraction around matches
function findAllSnippets(fullText, queryTerms, maxSnippets = 10) {
    if (!fullText) return ["No preview available."];
    
    const lowerText = fullText.toLowerCase();
    const snippets = [];
    const windowSize = 180; 
    let searchStartIndex = 0;
    
    while (snippets.length < maxSnippets && searchStartIndex < fullText.length) {
        let earliestMatchIdx = -1;
        let matchedTermLength = 0;

        for (const term of queryTerms) {
            const idx = lowerText.indexOf(term, searchStartIndex);
            if (idx !== -1 && (earliestMatchIdx === -1 || idx < earliestMatchIdx)) {
                earliestMatchIdx = idx;
                matchedTermLength = term.length;
            }
        }

        if (earliestMatchIdx === -1) break;

        const start = Math.max(0, earliestMatchIdx - windowSize);
        const end = Math.min(fullText.length, earliestMatchIdx + matchedTermLength + windowSize);

        let snippet = fullText.substring(start, end);
        if (start > 0) snippet = '...' + snippet;
        if (end < fullText.length) snippet = snippet + '...';

        snippets.push(highlightTerms(snippet, queryTerms));
        searchStartIndex = earliestMatchIdx + matchedTermLength;
    }

    if (snippets.length === 0) {
        return [highlightTerms(fullText.substring(0, 300) + '...', queryTerms)];
    }

    return snippets;
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

        const allSnippets = findAllSnippets(item.full_text, queryTerms);
        const maxInitialDisplay = 3;

        // Build header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'result-header';
        headerDiv.innerHTML = `<h2 class="narrator-title">${escapeHtml(narrator)}</h2><span class="badge">${escapeHtml(neighborhood)}</span>`;
        card.appendChild(headerDiv);

        // Build metadata
        const metaDiv = document.createElement('div');
        metaDiv.className = 'meta-info';
        metaDiv.innerHTML = `<strong>Interview Date:</strong> ${escapeHtml(interviewDate)} &bull; <strong>File:</strong> ${escapeHtml(item.pdf_filename)} &bull; <span style="color: var(--accent-color); font-weight: 600;">${allSnippets.length} match(es) in file</span>`;
        card.appendChild(metaDiv);

        // Snippet container
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

        // "See All" button if more than 3 matches
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

        // Actions footer
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'actions';
        let actionsHtml = `<a href="PDFs/${encodeURIComponent(item.pdf_filename)}" target="_blank">📄 View Full PDF Transcript</a>`;
        if (item.audio_filenames) {
            actionsHtml += ` <span style="color:#888;">|</span> 🎧 Audio Parts: ${escapeHtml(item.audio_filenames)}`;
        }
        actionsDiv.innerHTML = actionsHtml;
        card.appendChild(actionsDiv);

        container.appendChild(card);
    });
}

function handleSearch(e) {
    if (e.key !== 'Enter') return;

    const query = e.target.value.toLowerCase().trim();
    
    if (!query) {
        document.getElementById('resultsContainer').innerHTML = '';
        document.getElementById('stats').textContent = `Index loaded. ${searchIndex.length} transcripts available.`;
        return;
    }

    const startTime = performance.now();
    const terms = query.split(/\s+/).filter(t => t.length > 0);
    
    const filtered = searchIndex.filter(item => {
        const searchableBlob = `${item.narrator_name} ${item.neighborhood} ${item.pdf_filename} ${item.full_text}`.toLowerCase();
        return terms.every(term => searchableBlob.includes(term));
    });

    const endTime = performance.now();
    const elapsedMs = Math.round(endTime - startTime);

    document.getElementById('stats').textContent = `Found ${filtered.length} matching transcript(s) in ${elapsedMs} ms.`;
    renderResults(filtered, terms);
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