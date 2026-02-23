// Global state
let currentMindMapId = null;
let currentSequenceDiagramId = null;
let currentFlowchartId = null;
let currentPalette = 'professional';
let currentSeqDiagramStyle = 'colorful';
let currentFontFamily = 'Arial, sans-serif';
let network = null;
let mindmaps = [];
let sequenceDiagrams = [];
let flowcharts = [];
let appConfig = null;

// Layout constants - loaded from config
let LAYOUT_CONSTANTS = {
    NODE_MIN_WIDTH: 100,
    NODE_MIN_HEIGHT: 30,
    NODE_PADDING: 20,
    BASE_X_GAP: 400,
    BASE_Y_GAP: 80,
    ROOT_X: 0,
    ROOT_Y: 0,
    FAN_OUT_PX: 15
};

// Color constants - loaded from config
let COLOR_CONFIG = {
    rootDefault: '#E0E8F0',
    fallback: '#E5E5E5',
    edgeDefault: '#C0C0C0',
    siblingLightnessMin: 0.7,
    siblingLightnessMax: 0.9,
    siblingLightnessRange: 0.2,
    depth1Saturation: 0.3,
    depth2PlusSaturationMin: 0.15,
    depth2PlusSaturationReduce: 0.1,
    depthLightnessIncrease: 0.05,
    depthLightnessMax: 0.95,
    strokeDarknessMin: 0.08,
    strokeDarknessMax: 0.11,
    strokeLightnessMin: 0.6,
    edgeDesaturate: 0.1,
    edgeLightnessReduce: 0.1,
    edgeLightnessMin: 0.7
};

// Initialize
document.addEventListener('DOMContentLoaded', async function() {
    await loadConfig();
    loadMindMaps();
    loadSequenceDiagrams();
    loadFlowcharts();
    
    // Add resize listener to handle sidebar collapse/expand and window resize
    let resizeTimeout;
    const handleResize = function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            const container = document.getElementById('mindmap-container');
            if (container && container.querySelector('svg')) {
                const svg = container.querySelector('svg');
                const newWidth = container.clientWidth;
                const newHeight = container.clientHeight;
                
                if (svg && (parseInt(svg.getAttribute('width')) !== newWidth || parseInt(svg.getAttribute('height')) !== newHeight)) {
                    // Update SVG dimensions
                    d3.select(svg)
                        .attr('width', newWidth)
                        .attr('height', newHeight);
                    
                    // Reset zoom to fit new dimensions
                    if (window.d3ResetZoom) {
                        setTimeout(() => window.d3ResetZoom(), 50);
                    }
                }
            }
        }, 100);
    };
    
    window.addEventListener('resize', handleResize);
    
    // Also listen for custom resize events (triggered by sidebar toggle)
    window.addEventListener('resize', handleResize);
});

// Load configuration from server
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            appConfig = await response.json();
            // Update layout constants
            if (appConfig.layout) {
                LAYOUT_CONSTANTS = {
                    NODE_MIN_WIDTH: appConfig.layout.nodeMinWidth,
                    NODE_MIN_HEIGHT: appConfig.layout.nodeMinHeight,
                    NODE_PADDING: appConfig.layout.nodePadding,
                    BASE_X_GAP: appConfig.layout.baseXGap,
                    BASE_Y_GAP: appConfig.layout.baseYGap,
                    ROOT_X: appConfig.layout.rootX,
                    ROOT_Y: appConfig.layout.rootY,
                    FAN_OUT_PX: appConfig.layout.fanOutPx
                };
            }
            // Update color constants
            if (appConfig.color) {
                COLOR_CONFIG = appConfig.color;
            }
        }
    } catch (error) {
        console.warn('Failed to load config, using defaults:', error);
    }
}

// Load all mind maps
async function loadMindMaps() {
    try {
        const response = await fetch('/api/mindmaps');
        mindmaps = await response.json();
        renderMindMapList();
    } catch (error) {
        console.error('Error loading mind maps:', error);
    }
}

// Load all sequence diagrams
async function loadSequenceDiagrams() {
    try {
        const response = await fetch('/api/sequence-diagrams');
        const data = await response.json();
        sequenceDiagrams = Array.isArray(data) ? data : [];
        renderSequenceDiagramList();
    } catch (error) {
        console.error('Error loading sequence diagrams:', error);
        sequenceDiagrams = [];
        renderSequenceDiagramList();
    }
}

// Render sequence diagram list in sidebar (with rename & delete)
function renderSequenceDiagramList() {
    const listContainer = document.getElementById('sequence-diagram-list');
    if (!listContainer) return;
    if (sequenceDiagrams.length === 0) {
        listContainer.innerHTML = '<p class="empty-state">No sequence diagrams yet</p>';
        return;
    }
    listContainer.innerHTML = sequenceDiagrams.map(d => `
        <div class="mindmap-item ${d.id === currentSequenceDiagramId ? 'active' : ''}" data-id="${escapeHtml(d.id)}" onclick="loadSequenceDiagram('${escapeHtml(d.id)}')">
            <div class="mindmap-item-body">
                <span class="mindmap-item-title">${escapeHtml(d.title)}</span>
                <div class="mindmap-item-actions">
                    <button type="button" class="item-btn rename-btn" title="Rename" onclick="event.stopPropagation(); startRenameSequenceDiagram('${escapeHtml(d.id)}')">✎</button>
                    <button type="button" class="item-btn delete-btn" title="Delete" onclick="event.stopPropagation(); deleteSequenceDiagram('${escapeHtml(d.id)}')">🗑</button>
                </div>
            </div>
            <div class="mindmap-item-date">${new Date(d.created_at).toLocaleDateString()}</div>
        </div>
    `).join('');
}

// Load all flowcharts
async function loadFlowcharts() {
    try {
        const response = await fetch('/api/flowcharts');
        const data = await response.json();
        flowcharts = Array.isArray(data) ? data : [];
        renderFlowchartList();
    } catch (error) {
        console.error('Error loading flowcharts:', error);
        flowcharts = [];
        renderFlowchartList();
    }
}

// Render flowchart list in sidebar (with rename & delete)
function renderFlowchartList() {
    const listContainer = document.getElementById('flowchart-list');
    if (!listContainer) return;
    if (flowcharts.length === 0) {
        listContainer.innerHTML = '<p class="empty-state">No flowcharts yet</p>';
        return;
    }
    listContainer.innerHTML = flowcharts.map(d => `
        <div class="mindmap-item ${d.id === currentFlowchartId ? 'active' : ''}" data-id="${escapeHtml(d.id)}" onclick="loadFlowchart('${escapeHtml(d.id)}')">
            <div class="mindmap-item-body">
                <span class="mindmap-item-title">${escapeHtml(d.title)}</span>
                <div class="mindmap-item-actions">
                    <button type="button" class="item-btn rename-btn" title="Rename" onclick="event.stopPropagation(); startRenameFlowchart('${escapeHtml(d.id)}')">✎</button>
                    <button type="button" class="item-btn delete-btn" title="Delete" onclick="event.stopPropagation(); deleteFlowchart('${escapeHtml(d.id)}')">🗑</button>
                </div>
            </div>
            <div class="mindmap-item-date">${new Date(d.created_at).toLocaleDateString()}</div>
        </div>
    `).join('');
}

// Render mind map list (with rename & delete)
function renderMindMapList() {
    const listContainer = document.getElementById('mindmap-list');
    if (!listContainer) return;
    if (mindmaps.length === 0) {
        listContainer.innerHTML = '<p class="empty-state">No mind maps yet</p>';
        return;
    }
    listContainer.innerHTML = mindmaps.map(mm => `
        <div class="mindmap-item ${mm.id === currentMindMapId ? 'active' : ''}" data-id="${escapeHtml(mm.id)}" onclick="loadMindMap('${escapeHtml(mm.id)}')">
            <div class="mindmap-item-body">
                <span class="mindmap-item-title">${escapeHtml(mm.title)}</span>
                <div class="mindmap-item-actions">
                    <button type="button" class="item-btn rename-btn" title="Rename" onclick="event.stopPropagation(); startRenameMindMap('${escapeHtml(mm.id)}')">✎</button>
                    <button type="button" class="item-btn delete-btn" title="Delete" onclick="event.stopPropagation(); deleteMindMap('${escapeHtml(mm.id)}')">🗑</button>
                </div>
            </div>
            <div class="mindmap-item-date">${new Date(mm.created_at).toLocaleDateString()}</div>
        </div>
    `).join('');
}

// Show create dialog
function showCreateDialog() {
    document.getElementById('create-dialog').style.display = 'flex';
    document.getElementById('mindmap-text').focus();
}

// Hide create dialog
function hideCreateDialog() {
    document.getElementById('create-dialog').style.display = 'none';
    document.getElementById('mindmap-title').value = '';
    document.getElementById('mindmap-text').value = '';
}

// Show sequence diagram create dialog
function showSequenceDiagramDialog() {
    document.getElementById('sequence-diagram-dialog').style.display = 'flex';
    document.getElementById('seq-text').focus();
}

// Hide sequence diagram dialog
function hideSequenceDiagramDialog() {
    document.getElementById('sequence-diagram-dialog').style.display = 'none';
    document.getElementById('seq-title').value = '';
    document.getElementById('seq-text').value = '';
}

// Show flowchart create dialog
function showFlowchartDialog() {
    document.getElementById('flowchart-dialog').style.display = 'flex';
    document.getElementById('flowchart-text').focus();
}

// Hide flowchart dialog
function hideFlowchartDialog() {
    document.getElementById('flowchart-dialog').style.display = 'none';
    document.getElementById('flowchart-title').value = '';
    document.getElementById('flowchart-text').value = '';
}

// Create new sequence diagram
async function createSequenceDiagram() {
    const title = document.getElementById('seq-title').value.trim();
    const text = document.getElementById('seq-text').value.trim();
    if (!text) {
        alert('Please describe the flow or paste text');
        return;
    }
    hideSequenceDiagramDialog();
    showLoading();
    try {
        const response = await fetch('/api/sequence-diagrams', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, title: title || undefined })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to create sequence diagram');
        }
        const diagram = await response.json();
        if (!diagram || !diagram.id) {
            throw new Error('Invalid response: diagram not saved');
        }
        currentSequenceDiagramId = diagram.id;
        currentMindMapId = null;
        displaySequenceDiagram(diagram);
        hideLoading();
        await loadSequenceDiagrams();
        renderSequenceDiagramList();
        loadMindMaps();
        loadFlowcharts();
    } catch (error) {
        alert('Error: ' + error.message);
        hideLoading();
    }
}

// Load sequence diagram by id
async function loadSequenceDiagram(id) {
    showLoading();
    currentSequenceDiagramId = id;
    currentMindMapId = null;
    currentFlowchartId = null;
    try {
        const response = await fetch(`/api/sequence-diagrams/${id}`);
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || 'Failed to load sequence diagram');
        }
        const diagram = await response.json();
        displaySequenceDiagram(diagram);
        renderSequenceDiagramList();
        renderMindMapList();
        renderFlowchartList();
        showUpdatePromptSection();
    } catch (error) {
        alert('Error: ' + error.message);
        hideLoading();
    }
}

function showUpdatePromptSection() {
    const section = document.getElementById('update-prompt-section');
    if (section) section.style.display = (currentMindMapId || currentSequenceDiagramId || currentFlowchartId) ? 'block' : 'none';
    const input = document.getElementById('update-prompt-input');
    if (input) input.value = '';
}

function hideUpdatePromptSection() {
    const section = document.getElementById('update-prompt-section');
    if (section) section.style.display = 'none';
}

function showWelcome() {
    const container = document.getElementById('mindmap-container');
    if (!container) return;
    container.innerHTML = `
        <div class="welcome-message">
            <h2>👋 Welcome!</h2>
            <p>Click "New Mind Map" to get started</p>
            <p class="hint">Paste your text and let AI create a beautiful mind map</p>
        </div>
    `;
    hideBackButton();
}

// Rename mind map: show inline edit
function startRenameMindMap(id) {
    const mm = mindmaps.find(m => m.id === id);
    if (!mm) return;
    const item = document.querySelector(`#mindmap-list .mindmap-item[data-id="${id.replace(/"/g, '&quot;')}"]`);
    if (!item) return;
    const titleEl = item.querySelector('.mindmap-item-title');
    if (!titleEl) return;
    const orig = titleEl.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'item-rename-input';
    input.value = orig;
    input.dataset.id = id;
    input.dataset.kind = 'mindmap';
    titleEl.replaceWith(input);
    input.focus();
    input.select();
    input.onblur = () => commitRename(input);
    input.onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); input.blur(); } if (e.key === 'Escape') { input.value = orig; input.blur(); } };
}

function startRenameSequenceDiagram(id) {
    const d = sequenceDiagrams.find(x => x.id === id);
    if (!d) return;
    const item = document.querySelector(`#sequence-diagram-list .mindmap-item[data-id="${id.replace(/"/g, '&quot;')}"]`);
    if (!item) return;
    const titleEl = item.querySelector('.mindmap-item-title');
    if (!titleEl) return;
    const orig = titleEl.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'item-rename-input';
    input.value = orig;
    input.dataset.id = id;
    input.dataset.kind = 'sequence';
    titleEl.replaceWith(input);
    input.focus();
    input.select();
    input.onblur = () => commitRename(input);
    input.onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); input.blur(); } if (e.key === 'Escape') { input.value = orig; input.blur(); } };
}

async function commitRename(input) {
    const id = input.dataset.id;
    const kind = input.dataset.kind;
    const newTitle = (input.value || '').trim();
    const parent = input.closest('.mindmap-item');
    const titleSpan = document.createElement('span');
    titleSpan.className = 'mindmap-item-title';
    if (kind === 'mindmap') {
        const mm = mindmaps.find(m => m.id === id);
        titleSpan.textContent = mm ? mm.title : newTitle || 'Untitled';
    } else if (kind === 'sequence') {
        const d = sequenceDiagrams.find(x => x.id === id);
        titleSpan.textContent = d ? d.title : newTitle || 'Sequence Diagram';
    } else {
        const f = flowcharts.find(x => x.id === id);
        titleSpan.textContent = f ? f.title : newTitle || 'Flowchart';
    }
    input.replaceWith(titleSpan);
    if (!newTitle) return;
    const url = kind === 'mindmap' ? `/api/mindmaps/${id}` : (kind === 'flowchart' ? `/api/flowcharts/${id}` : `/api/sequence-diagrams/${id}`);
    try {
        const res = await fetch(url, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: newTitle }) });
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || 'Rename failed');
        if (kind === 'mindmap') {
            await loadMindMaps();
        } else if (kind === 'sequence') {
            await loadSequenceDiagrams();
        } else {
            await loadFlowcharts();
        }
        renderMindMapList();
        renderSequenceDiagramList();
        renderFlowchartList();
    } catch (e) {
        console.error(e);
        if (kind === 'mindmap') {
            const mm = mindmaps.find(m => m.id === id);
            titleSpan.textContent = mm ? mm.title : 'Untitled';
        } else if (kind === 'sequence') {
            const d = sequenceDiagrams.find(x => x.id === id);
            titleSpan.textContent = d ? d.title : 'Sequence Diagram';
        } else {
            const f = flowcharts.find(x => x.id === id);
            titleSpan.textContent = f ? f.title : 'Flowchart';
        }
    }
}

function startRenameFlowchart(id) {
    const f = flowcharts.find(x => x.id === id);
    if (!f) return;
    const item = document.querySelector(`#flowchart-list .mindmap-item[data-id="${id.replace(/"/g, '&quot;')}"]`);
    if (!item) return;
    const titleEl = item.querySelector('.mindmap-item-title');
    if (!titleEl) return;
    const orig = titleEl.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'item-rename-input';
    input.value = orig;
    input.dataset.id = id;
    input.dataset.kind = 'flowchart';
    titleEl.replaceWith(input);
    input.focus();
    input.select();
    input.onblur = () => commitRename(input);
    input.onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); input.blur(); } if (e.key === 'Escape') { input.value = orig; input.blur(); } };
}

async function deleteMindMap(id) {
    if (!confirm('Delete this mind map? This cannot be undone.')) return;
    try {
        const res = await fetch(`/api/mindmaps/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');
        if (currentMindMapId === id) {
            currentMindMapId = null;
            showWelcome();
            hideUpdatePromptSection();
        }
        await loadMindMaps();
        renderMindMapList();
        renderSequenceDiagramList();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function deleteSequenceDiagram(id) {
    if (!confirm('Delete this sequence diagram? This cannot be undone.')) return;
    try {
        const res = await fetch(`/api/sequence-diagrams/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');
        if (currentSequenceDiagramId === id) {
            currentSequenceDiagramId = null;
            showWelcome();
            hideUpdatePromptSection();
        }
        await loadSequenceDiagrams();
        renderMindMapList();
        renderSequenceDiagramList();
        renderFlowchartList();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function deleteFlowchart(id) {
    if (!confirm('Delete this flowchart? This cannot be undone.')) return;
    try {
        const res = await fetch(`/api/flowcharts/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');
        if (currentFlowchartId === id) {
            currentFlowchartId = null;
            showWelcome();
            hideUpdatePromptSection();
        }
        await loadFlowcharts();
        renderMindMapList();
        renderSequenceDiagramList();
        renderFlowchartList();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

function changeSeqDiagramStyle(style) {
    currentSeqDiagramStyle = style === 'bw' ? 'bw' : 'colorful';
    document.querySelectorAll('input[name="seq-style"]').forEach(function(radio) {
        radio.checked = radio.value === currentSeqDiagramStyle;
    });
    if (currentSequenceDiagramId) {
        loadSequenceDiagram(currentSequenceDiagramId);
    }
}

async function updateWithPrompt() {
    const input = document.getElementById('update-prompt-input');
    const prompt = (input && input.value || '').trim();
    if (!prompt) {
        alert('Enter a prompt describing what to add or change.');
        return;
    }
    if (currentMindMapId) {
        showLoading();
        try {
            const res = await fetch(`/api/mindmaps/${currentMindMapId}?palette=${currentPalette}&fontFamily=${encodeURIComponent(currentFontFamily)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || 'Update failed');
            const data = await res.json();
            if (input) input.value = '';
            displayMindMap(data.data);
            loadMindMaps();
            renderMindMapList();
            hideLoading();
        } catch (e) {
            alert('Error: ' + e.message);
            hideLoading();
        }
        return;
    }
    if (currentSequenceDiagramId) {
        showLoading();
        try {
            const res = await fetch(`/api/sequence-diagrams/${currentSequenceDiagramId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || 'Update failed');
            const diagram = await res.json();
            if (input) input.value = '';
            displaySequenceDiagram(diagram);
            loadSequenceDiagrams();
            renderSequenceDiagramList();
            hideLoading();
        } catch (e) {
            alert('Error: ' + e.message);
            hideLoading();
        }
        return;
    }
    if (currentFlowchartId) {
        showLoading();
        try {
            const res = await fetch(`/api/flowcharts/${currentFlowchartId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || 'Update failed');
            const diagram = await res.json();
            if (input) input.value = '';
            displayFlowchart(diagram);
            loadFlowcharts();
            renderFlowchartList();
            hideLoading();
        } catch (e) {
            alert('Error: ' + e.message);
            hideLoading();
        }
        return;
    }
    alert('Select a mind map, sequence diagram, or flowchart first.');
}

// Sanitize Mermaid sequence diagram to avoid common parse errors
function sanitizeMermaidSequence(syntax) {
    if (!syntax || typeof syntax !== 'string') return syntax;
    let s = syntax;
    // "loop for each ..." can confuse parser
    s = s.replace(/\bloop\s+for\s+/gi, 'loop For ');
    // Mermaid 10 "Note over" accepts only two participants; rewrite "Note over A,B,C,D: text" -> "Note over A,D: text"
    s = s.replace(/Note over ([^:]+):/g, function(match, participants) {
        const list = participants.split(',').map(function(p) { return p.trim(); }).filter(Boolean);
        if (list.length > 2) {
            return 'Note over ' + list[0] + ',' + list[list.length - 1] + ':';
        }
        return match;
    });
    // "box" may only contain participant/actor declarations, not messages. Remove malformed box blocks that contain arrows.
    s = s.replace(/\bbox\s+[^\n]+\n([\s\S]*?)\bend\b/g, function(match, inner) {
        var hasArrow = /--?>>?/.test(inner);
        if (hasArrow) {
            return inner;
        }
        return match;
    });
    return s;
}

// Display sequence diagram in main area (Mermaid)
async function displaySequenceDiagram(diagram) {
    const container = document.getElementById('mindmap-container');
    if (!container) return;
    let mermaidSyntax = diagram.mermaid_syntax || diagram.mermaidSyntax;
    if (!mermaidSyntax) {
        container.innerHTML = '<p class="error">No diagram data</p>';
        hideLoading();
        return;
    }
    mermaidSyntax = sanitizeMermaidSequence(mermaidSyntax);
    var styleClass = currentSeqDiagramStyle === 'bw' ? 'seq-bw' : 'seq-colorful';
    var paletteClass = (currentSeqDiagramStyle === 'bw') ? '' : (' seq-palette-' + (currentPalette || 'professional'));
    container.innerHTML = '<div id="seq-diagram-wrap" class="sequence-diagram-wrap ' + styleClass + paletteClass + '"></div>';
    const wrap = document.getElementById('seq-diagram-wrap');
    const uniqueId = 'mermaid-seq-' + Date.now();
    try {
        if (typeof window.mermaid === 'undefined') {
            wrap.innerHTML = '<p class="error">Mermaid not loaded. Refresh the page.</p>';
            hideLoading();
            return;
        }
        var fontFamily = (currentFontFamily || 'Arial, sans-serif').replace(/^'|'$/g, '');
        if (window.mermaid && window.mermaid.initialize) {
            window.mermaid.initialize({
                startOnLoad: false,
                theme: 'default',
                securityLevel: 'loose',
                sequence: {
                    actorFontFamily: fontFamily,
                    messageFontFamily: fontFamily,
                    noteFontFamily: fontFamily,
                    actorFontSize: 14,
                    messageFontSize: 14,
                    noteFontSize: 14
                }
            });
        }
        const { svg } = await window.mermaid.render(uniqueId, mermaidSyntax);
        wrap.innerHTML = svg;
        showBackButton();
        hideLoading();
    } catch (err) {
        const errMsg = (err && (err.message || err.str || String(err))) || 'Unknown error';
        console.error('Mermaid render error:', err);
        wrap.innerHTML =
            '<p class="error">Could not render diagram.</p>' +
            '<p class="error-detail">' + escapeHtml(errMsg) + '</p>' +
            '<p class="sidebar-hint">Try simplifying the diagram or avoid "loop for" (use "loop For each" or "loop Process each").</p>' +
            '<pre class="mermaid-source">' + escapeHtml(mermaidSyntax) + '</pre>';
        hideLoading();
    }
}

// Create new flowchart
async function createFlowchart() {
    const title = document.getElementById('flowchart-title').value.trim();
    const text = document.getElementById('flowchart-text').value.trim();
    if (!text) {
        alert('Please describe the process or paste text');
        return;
    }
    hideFlowchartDialog();
    showLoading();
    try {
        const response = await fetch('/api/flowcharts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, title: title || undefined })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to create flowchart');
        }
        const diagram = await response.json();
        if (!diagram || !diagram.id) throw new Error('Invalid response: flowchart not saved');
        currentFlowchartId = diagram.id;
        currentMindMapId = null;
        currentSequenceDiagramId = null;
        displayFlowchart(diagram);
        hideLoading();
        await loadFlowcharts();
        renderFlowchartList();
        loadMindMaps();
        loadSequenceDiagrams();
    } catch (error) {
        alert('Error: ' + error.message);
        hideLoading();
    }
}

// Load flowchart by id
async function loadFlowchart(id) {
    showLoading();
    currentFlowchartId = id;
    currentMindMapId = null;
    currentSequenceDiagramId = null;
    try {
        const response = await fetch(`/api/flowcharts/${id}`);
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || 'Failed to load flowchart');
        }
        const diagram = await response.json();
        displayFlowchart(diagram);
        renderFlowchartList();
        renderMindMapList();
        renderSequenceDiagramList();
        showUpdatePromptSection();
    } catch (error) {
        alert('Error: ' + error.message);
        hideLoading();
    }
}

// Force flowchart to be top-down and ensure valid first line
function sanitizeFlowchartSyntax(syntax) {
    if (!syntax || typeof syntax !== 'string') return syntax;
    var s = syntax.trim();
    if (s.toLowerCase().startsWith('flowchart lr')) {
        s = 'flowchart TD' + s.substring(12);
    } else if (!s.toLowerCase().startsWith('flowchart')) {
        s = 'flowchart TD\n' + s;
    } else if (!/^flowchart\s+td\b/i.test(s)) {
        s = s.replace(/^flowchart\s+\w+/i, 'flowchart TD');
    }
    return s;
}

// Current flowchart diagram (for notes); set when displaying a flowchart
let currentFlowchartDiagram = null;

// Display flowchart in main area (Mermaid) with left/right notes columns
async function displayFlowchart(diagram) {
    const container = document.getElementById('mindmap-container');
    if (!container) return;
    let mermaidSyntax = diagram.mermaid_syntax || diagram.mermaidSyntax;
    if (!mermaidSyntax) {
        container.innerHTML = '<p class="error">No flowchart data</p>';
        hideLoading();
        return;
    }
    currentFlowchartDiagram = diagram;
    mermaidSyntax = sanitizeFlowchartSyntax(mermaidSyntax);
    var styleClass = currentSeqDiagramStyle === 'bw' ? 'seq-bw' : 'seq-colorful';
    var paletteClass = (currentSeqDiagramStyle === 'bw') ? '' : (' seq-palette-' + (currentPalette || 'professional'));
    var notes = diagram.notes || [];
    container.innerHTML =
        '<div class="flowchart-page">' +
        '  <div class="flowchart-notes-col flowchart-notes-left">' +
        '    <div class="flowchart-notes-header">Notes (left)</div>' +
        '    <div class="flowchart-notes-list" data-side="left"></div>' +
        '    <button type="button" class="btn-add-flowchart-note" data-side="left">+ Add note</button>' +
        '  </div>' +
        '  <div class="flowchart-center">' +
        '    <div id="flowchart-wrap" class="sequence-diagram-wrap flowchart-wrap ' + styleClass + paletteClass + '"></div>' +
        '  </div>' +
        '  <div class="flowchart-notes-col flowchart-notes-right">' +
        '    <div class="flowchart-notes-header">Notes (right)</div>' +
        '    <div class="flowchart-notes-list" data-side="right"></div>' +
        '    <button type="button" class="btn-add-flowchart-note" data-side="right">+ Add note</button>' +
        '  </div>' +
        '</div>';
    renderFlowchartNotesPanels(notes);
    bindFlowchartNotesEvents();
    const wrap = document.getElementById('flowchart-wrap');
    const uniqueId = 'mermaid-flow-' + Date.now();
    try {
        if (typeof window.mermaid === 'undefined') {
            wrap.innerHTML = '<p class="error">Mermaid not loaded. Refresh the page.</p>';
            hideLoading();
            return;
        }
        if (window.mermaid && window.mermaid.initialize) {
            try {
                window.mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    securityLevel: 'loose',
                    flowchart: {
                        htmlLabels: true,
                        useMaxWidth: false,
                        padding: 20,
                        nodeSpacing: 22,
                        rankSpacing: 26,
                        curve: 'basis'
                    }
                });
            } catch (initErr) {
                console.warn('Flowchart mermaid.initialize fallback:', initErr);
                window.mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    securityLevel: 'loose',
                    flowchart: { htmlLabels: true, useMaxWidth: false }
                });
            }
        }
        const { svg } = await window.mermaid.render(uniqueId, mermaidSyntax);
        wrap.innerHTML = svg;
        attachFlowchartZoom();
        showBackButton();
        hideLoading();
    } catch (err) {
        const errMsg = (err && (err.message || err.str || String(err))) || 'Unknown error';
        console.error('Mermaid flowchart render error:', err);
        wrap.innerHTML = '<p class="error">Could not render flowchart.</p><p class="error-detail">' + escapeHtml(errMsg) + '</p><pre class="mermaid-source">' + escapeHtml(mermaidSyntax) + '</pre>';
        hideLoading();
    }
}

function attachFlowchartZoom() {
    var wrap = document.getElementById('flowchart-wrap');
    var d3lib = typeof d3 !== 'undefined' ? d3 : (typeof window.d3 !== 'undefined' ? window.d3 : null);
    if (!wrap || !d3lib) return;
    var svgEl = wrap.querySelector('svg');
    if (!svgEl) return;
    try {
        var svg = d3lib.select(svgEl);
        var inner = svg.select('g');
        if (inner.empty()) inner = svg;
        var zoom = d3lib.zoom().scaleExtent([0.15, 5]).on('zoom', function(ev) {
            inner.attr('transform', ev.transform);
        });
        svg.call(zoom);
        window.d3ZoomIn = function() { svg.transition().duration(250).call(zoom.scaleBy, 1.3); };
        window.d3ZoomOut = function() { svg.transition().duration(250).call(zoom.scaleBy, 0.7); };
        window.d3ResetZoom = function() { svg.transition().duration(250).call(zoom.transform, d3lib.zoomIdentity); };
    } catch (e) {
        console.warn('Flowchart zoom init failed:', e);
    }
}

function showBackButton() {
    var btn = document.getElementById('back-to-welcome-btn');
    if (btn) btn.style.display = 'inline-block';
}

function hideBackButton() {
    var btn = document.getElementById('back-to-welcome-btn');
    if (btn) btn.style.display = 'none';
}

function goBackToWelcome() {
    currentMindMapId = null;
    currentSequenceDiagramId = null;
    currentFlowchartId = null;
    currentFlowchartDiagram = null;
    window.d3ZoomIn = null;
    window.d3ZoomOut = null;
    window.d3ResetZoom = null;
    hideUpdatePromptSection();
    showWelcome();
    hideBackButton();
    renderMindMapList();
    renderSequenceDiagramList();
    renderFlowchartList();
}

function renderFlowchartNotesPanels(notes) {
    var leftList = document.querySelector('.flowchart-notes-list[data-side="left"]');
    var rightList = document.querySelector('.flowchart-notes-list[data-side="right"]');
    if (!leftList || !rightList) return;
    var leftNotes = (notes || []).filter(function(n) { return (n.side || 'left') === 'left'; });
    var rightNotes = (notes || []).filter(function(n) { return (n.side || 'right') === 'right'; });
    leftList.innerHTML = leftNotes.map(function(n) { return flowchartNoteCardHtml(n); }).join('');
    rightList.innerHTML = rightNotes.map(function(n) { return flowchartNoteCardHtml(n); }).join('');
}

function flowchartNoteCardHtml(note) {
    var id = (note.id || '').replace(/"/g, '&quot;');
    var content = escapeHtml((note.content || '').trim());
    return '<div class="flowchart-note-card" data-note-id="' + id + '">' +
        '<div class="flowchart-note-content" data-note-id="' + id + '">' + (content || '<em>Empty note</em>') + '</div>' +
        '<div class="flowchart-note-actions">' +
        '<button type="button" class="flowchart-note-btn flowchart-note-edit" title="Edit">✎</button>' +
        '<button type="button" class="flowchart-note-btn flowchart-note-delete" title="Delete">🗑</button>' +
        '</div></div>';
}

function bindFlowchartNotesEvents() {
    var diagramId = currentFlowchartId;
    if (!diagramId) return;
    document.querySelectorAll('.btn-add-flowchart-note').forEach(function(btn) {
        btn.onclick = function() {
            var side = btn.getAttribute('data-side') || 'left';
            addFlowchartNote(side);
        };
    });
    document.querySelectorAll('.flowchart-note-edit').forEach(function(btn) {
        btn.onclick = function() {
            var card = btn.closest('.flowchart-note-card');
            var noteId = card ? card.getAttribute('data-note-id') : null;
            if (noteId) editFlowchartNote(noteId);
        };
    });
    document.querySelectorAll('.flowchart-note-delete').forEach(function(btn) {
        btn.onclick = function() {
            var card = btn.closest('.flowchart-note-card');
            var noteId = card ? card.getAttribute('data-note-id') : null;
            if (noteId && confirm('Delete this note?')) deleteFlowchartNote(noteId);
        };
    });
}

function addFlowchartNote(side) {
    var diagramId = currentFlowchartId;
    if (!diagramId) return;
    var content = prompt('Note text (sticky ' + side + '):');
    if (content === null) return;
    content = (content || '').trim();
    if (!content) {
        alert('Enter some text for the note.');
        return;
    }
    fetch('/api/flowcharts/' + encodeURIComponent(diagramId) + '/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content, side: side })
    }).then(function(r) {
        if (!r.ok) return r.json().then(function(j) { throw new Error(j.error || 'Failed to add note'); });
        return r.json();
    }).then(function() {
        return fetch('/api/flowcharts/' + encodeURIComponent(diagramId));
    }).then(function(r) {
        if (!r.ok) throw new Error('Failed to reload flowchart');
        return r.json();
    }).then(function(diagram) {
        currentFlowchartDiagram = diagram;
        renderFlowchartNotesPanels(diagram.notes || []);
        bindFlowchartNotesEvents();
    }).catch(function(e) {
        alert('Error: ' + (e.message || e));
    });
}

function editFlowchartNote(noteId) {
    var diagramId = currentFlowchartId;
    if (!diagramId) return;
    var card = document.querySelector('.flowchart-note-card[data-note-id="' + noteId.replace(/"/g, '\\"') + '"]');
    if (!card) return;
    var contentEl = card.querySelector('.flowchart-note-content');
    var note = (currentFlowchartDiagram && currentFlowchartDiagram.notes) ? currentFlowchartDiagram.notes.find(function(n) { return n.id === noteId; }) : null;
    var currentContent = note ? (note.content || '') : (contentEl ? contentEl.textContent : '');
    var newContent = prompt('Edit note:', currentContent);
    if (newContent === null) return;
    newContent = (newContent || '').trim();
    fetch('/api/flowcharts/' + encodeURIComponent(diagramId) + '/notes/' + encodeURIComponent(noteId), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newContent })
    }).then(function(r) {
        if (!r.ok) return r.json().then(function(j) { throw new Error(j.error || 'Failed to update note'); });
        return r.json();
    }).then(function() {
        return fetch('/api/flowcharts/' + encodeURIComponent(diagramId));
    }).then(function(r) {
        if (!r.ok) throw new Error('Failed to reload flowchart');
        return r.json();
    }).then(function(diagram) {
        currentFlowchartDiagram = diagram;
        renderFlowchartNotesPanels(diagram.notes || []);
        bindFlowchartNotesEvents();
    }).catch(function(e) {
        alert('Error: ' + (e.message || e));
    });
}

function deleteFlowchartNote(noteId) {
    var diagramId = currentFlowchartId;
    if (!diagramId) return;
    fetch('/api/flowcharts/' + encodeURIComponent(diagramId) + '/notes/' + encodeURIComponent(noteId), {
        method: 'DELETE'
    }).then(function(r) {
        if (!r.ok) return r.json().then(function(j) { throw new Error(j.error || 'Failed to delete note'); });
        return fetch('/api/flowcharts/' + encodeURIComponent(diagramId));
    }).then(function(r) {
        if (!r.ok) throw new Error('Failed to reload flowchart');
        return r.json();
    }).then(function(diagram) {
        currentFlowchartDiagram = diagram;
        renderFlowchartNotesPanels(diagram.notes || []);
        bindFlowchartNotesEvents();
    }).catch(function(e) {
        alert('Error: ' + (e.message || e));
    });
}

// Create new mind map
async function createMindMap() {
    const title = document.getElementById('mindmap-title').value.trim();
    const text = document.getElementById('mindmap-text').value.trim();
    
    if (!text) {
        alert('Please enter some text');
        return;
    }
    
    hideCreateDialog();
    showLoading();
    
    try {
        const response = await fetch('/api/mindmaps', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                title: title || undefined,
                palette: currentPalette,
                fontFamily: currentFontFamily
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create mind map');
        }
        
        const mindmap = await response.json();
        currentMindMapId = mindmap.id;
        displayMindMap(mindmap.data);
        loadMindMaps();
    } catch (error) {
        alert('Error: ' + error.message);
        hideLoading();
    }
}

// Load mind map
async function loadMindMap(id) {
    showLoading();
    currentMindMapId = id;
    currentSequenceDiagramId = null;
    currentFlowchartId = null;
    
    try {
        const response = await fetch(`/api/mindmaps/${id}?palette=${currentPalette}&fontFamily=${encodeURIComponent(currentFontFamily)}`);
        
        if (!response.ok) {
            let errorMessage = 'Failed to load mind map';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        const mindmap = await response.json();
        
        if (!mindmap) {
            throw new Error('No data received from server');
        }
        
        if (!mindmap.data) {
            throw new Error('Invalid mind map data: missing visualization data');
        }
        
        // Validate data structure
        if (mindmap.data.type === 'd3' && !mindmap.data.data) {
            throw new Error('Invalid mind map data: missing D3 data structure');
        }
        
        displayMindMap(mindmap.data);
        renderMindMapList();
        renderSequenceDiagramList();
        renderFlowchartList();
        showUpdatePromptSection();
    } catch (error) {
        console.error('Error loading mind map:', error);
        console.error('Mind map ID:', id);
        
        // Show more detailed error message
        let errorMsg = 'Error loading mind map: ' + error.message;
        if (error.message.includes('Invalid mind map data')) {
            errorMsg += '\n\nThis mind map may have been created with an older version and is incompatible.';
            errorMsg += '\nPlease try creating a new mind map.';
        }
        
        alert(errorMsg);
        hideLoading();
        
        // Clear the failed mind map from current selection
        currentMindMapId = null;
    }
}

// Display mind map
function displayMindMap(data) {
    const container = document.getElementById('mindmap-container');
    container.innerHTML = '<div id="mindmap"></div>';
    showBackButton();
    // Always render with D3.js
    if (data.type === 'd3' || data.data) {
        renderD3MindMap(data.data || data, container.querySelector('#mindmap'));
        hideLoading();
    } else {
        // Fallback for legacy data
        renderD3MindMap(data, container.querySelector('#mindmap'));
        hideLoading();
    }
}

// Layout functions - must be defined before renderD3MindMap
// Layout constants are loaded from config in loadConfig()

/**
 * Get depth-aware horizontal spacing
 * Deeper levels get progressively more horizontal space
 * @param {number} depth - Node depth (0 = root, 1 = first level, etc.)
 * @returns {number} Effective X gap for this depth
 */
function getEffectiveXGap(depth) {
    // Shallow levels → smaller gap, deeper levels → progressively larger gap
    // Formula: BASE_X_GAP * (1 + depth * multiplier)
    const multiplier = appConfig?.layout?.xGapDepthMultiplier || 0.15;
    return LAYOUT_CONSTANTS.BASE_X_GAP * (1 + depth * multiplier);
}

/**
 * Get depth-aware vertical spacing
 * Deeper levels get tighter vertical spacing (but never below 60% of base)
 * @param {number} depth - Node depth (0 = root, 1 = first level, etc.)
 * @returns {number} Effective Y gap for this depth
 */
function getEffectiveYGap(depth) {
    // Root and level 1 → full Y_GAP, deeper levels → gradually tighter
    // Formula: Y_GAP * max(minRatio, 1 - depth * reduce)
    const reduce = appConfig?.layout?.yGapDepthReduce || 0.08;
    const minRatio = appConfig?.layout?.yGapMinRatio || 0.6;
    return LAYOUT_CONSTANTS.BASE_Y_GAP * Math.max(minRatio, 1 - depth * reduce);
}

// Keywords to preserve casing (configurable)
const PRESERVE_CASING_KEYWORDS = [
    'API', 'ETH', 'BTC', 'USD', 'EUR', 'GBP', 'JPY', 'CNY',
    'HTTP', 'HTTPS', 'URL', 'URI', 'JSON', 'XML', 'HTML', 'CSS', 'JS',
    'SQL', 'DB', 'ID', 'UUID', 'GUID',
    'CPU', 'GPU', 'RAM', 'SSD', 'HDD',
    'AWS', 'GCP', 'Azure', 'S3', 'EC2',
    'NFT', 'DAO', 'DeFi', 'Web3', 'DApp'
];

/**
 * Normalize text casing: lowercase by default, preserve ALL CAPS and keywords
 * @param {string} text - Original text
 * @returns {string} Normalized text
 */
function normalizeTextCasing(text) {
    if (!text) return '';
    
    // Split by word boundaries (spaces, underscores, hyphens)
    return text.replace(/\b(\w+)\b/g, (match, word) => {
        // Preserve if ALL CAPS (3+ chars)
        if (word.length >= 3 && word === word.toUpperCase() && /[A-Z]/.test(word)) {
            return word;
        }
        
        // Preserve if in keyword list (case-insensitive match)
        const upperWord = word.toUpperCase();
        if (PRESERVE_CASING_KEYWORDS.some(kw => kw.toUpperCase() === upperWord)) {
            return word; // Keep original casing
        }
        
        // Default: lowercase
        return word.toLowerCase();
    });
}

/**
 * Calculate bounding box for a node based on its text content
 * Uses formatted text for accurate measurement
 * @param {Object} node - D3 hierarchy node
 * @param {string} fontFamily - Font family for text measurement
 * @returns {Object} {width, height, formattedText}
 */
function calculateNodeBounds(node, fontFamily) {
    try {
        const fontSize = node.data.level === 0 ? 16 : node.data.type === "branch" ? 14 : 12;
        const originalText = node.data.name || '';
        
        // Format text BEFORE measurement
        const formattedText = normalizeTextCasing(originalText);
        
        // Ensure fontFamily is valid, fallback to Arial if invalid
        const safeFontFamily = fontFamily || 'Arial, sans-serif';
        
        // Create temporary SVG element for measurement
        // Must be appended to DOM for getBBox to work
        const tempSvg = d3.select(document.body)
            .append("svg")
            .style("position", "absolute")
            .style("visibility", "hidden")
            .style("pointer-events", "none");
        
        const tempText = tempSvg.append("text")
            .attr("font-size", fontSize + "px")
            .attr("font-family", safeFontFamily)
            .attr("font-weight", node.data.level === 0 || node.data.type === "branch" ? "600" : "400")
            .text(formattedText);
        
        // Measure actual rendered text
        let bbox;
        try {
            bbox = tempText.node().getBBox();
        } catch (e) {
            // If measurement fails (font not loaded), use fallback dimensions
            console.warn('Font measurement failed, using fallback:', e);
            bbox = { width: formattedText.length * 8, height: fontSize * 1.2 };
        }
        
        // Clean up
        tempSvg.remove();
        
        return {
            width: Math.max(bbox.width + LAYOUT_CONSTANTS.NODE_PADDING, LAYOUT_CONSTANTS.NODE_MIN_WIDTH),
            height: Math.max(bbox.height + 10, LAYOUT_CONSTANTS.NODE_MIN_HEIGHT),
            formattedText: formattedText
        };
    } catch (error) {
        console.error('Error calculating node bounds:', error);
        // Return safe fallback
        return {
            width: LAYOUT_CONSTANTS.NODE_MIN_WIDTH,
            height: LAYOUT_CONSTANTS.NODE_MIN_HEIGHT,
            formattedText: node.data.name || ''
        };
    }
}

/**
 * Calculate total height of a subtree (for vertical centering)
 * @param {Object} node - D3 hierarchy node
 * @param {string} fontFamily - Font family for measurement
 * @returns {number} Total height needed for subtree
 */
/**
 * PASS 1: Compute subtree height for a node
 * Pure function that calculates the total vertical space needed
 * Uses depth-aware Y_GAP for accurate spacing
 * @param {Object} node - D3 hierarchy node
 * @param {string} fontFamily - Font family for measurement
 * @returns {number} Total height needed for this subtree
 */
function computeSubtreeHeight(node, fontFamily) {
    // Use pre-calculated bounds if available
    const ownBounds = node.nodeBounds || calculateNodeBounds(node, fontFamily);
    const ownHeight = ownBounds.height;
    
    // Leaf node: height is just the node itself
    if (!node.children || node.children.length === 0) {
        node.subtreeHeight = ownHeight;
        return ownHeight;
    }
    
    // Non-leaf: sum of all children's subtree heights + depth-aware gaps
    // Use effective Y_GAP based on children's depth (node.depth + 1)
    const childDepth = node.depth + 1;
    const effectiveYGap = getEffectiveYGap(childDepth);
    
    let childrenTotalHeight = 0;
    node.children.forEach((child, index) => {
        childrenTotalHeight += computeSubtreeHeight(child, fontFamily);
        if (index < node.children.length - 1) {
            childrenTotalHeight += effectiveYGap;
        }
    });
    
    // Subtree height = max(own height, children total height)
    // This ensures parent reserves enough space for all descendants
    const subtreeHeight = Math.max(ownHeight, childrenTotalHeight);
    node.subtreeHeight = subtreeHeight;
    return subtreeHeight;
}

/**
 * Pure layout function - computes positions in world coordinates
 * Root at (0, 0), half children go left, half right
 * All descendants inherit parent's direction
 * Uses TWO-PASS layout to prevent overlaps
 * @param {Object} root - D3 hierarchy root node
 * @param {Object} options - Layout options
 * @param {string} options.fontFamily - Font family for text measurement
 */
function computeMindMapLayout(root, options = {}) {
    const fontFamily = options.fontFamily || 'Arial, sans-serif';
    
    // Pre-process all nodes: format text and calculate bounds
    // This ensures layout uses formatted text measurements
    root.each(d => {
        const bounds = calculateNodeBounds(d, fontFamily);
        d.formattedText = bounds.formattedText;
        d.nodeBounds = { width: bounds.width, height: bounds.height };
    });
    
    // PASS 1: Compute subtree heights for all nodes (bottom-up)
    // This must be done before positioning
    computeSubtreeHeight(root, fontFamily);
    
    // Root at origin (will be centered by camera)
    root.x = LAYOUT_CONSTANTS.ROOT_X;
    root.y = LAYOUT_CONSTANTS.ROOT_Y;
    
    const branches = root.children || [];
    if (branches.length === 0) return;
    
    // Split branches: half left, half right
    const leftCount = Math.ceil(branches.length / 2);
    const leftBranches = branches.slice(0, leftCount);
    const rightBranches = branches.slice(leftCount);
    
    // PASS 2: Position nodes using subtree heights
    // Use depth-aware X_GAP for first level (depth 1)
    const firstLevelXGap = getEffectiveXGap(1);
    
    // Layout left branches (starting at Y=0, will be centered)
    if (leftBranches.length > 0) {
        layoutSubtree(leftBranches, -firstLevelXGap, true, 0);
    }
    
    // Layout right branches (starting at Y=0, will be centered)
    if (rightBranches.length > 0) {
        layoutSubtree(rightBranches, firstLevelXGap, false, 0);
    }
    
    // Center root vertically relative to all branches
    const allBranches = [...leftBranches, ...rightBranches];
    if (allBranches.length > 0) {
        const minY = Math.min(...allBranches.map(b => {
            const bounds = b.nodeBounds;
            return b.y - bounds.height / 2;
        }));
        const maxY = Math.max(...allBranches.map(b => {
            const bounds = b.nodeBounds;
            return b.y + bounds.height / 2;
        }));
        root.y = (minY + maxY) / 2;
    }
}

/**
 * PASS 2: Position a node and its children within parent's vertical band
 * Parent-banded layout: all descendants must lie within parent's band
 * Uses depth-aware spacing for improved aspect ratio
 * @param {Object} node - D3 hierarchy node
 * @param {number} x - X position
 * @param {number} bandTop - Top of parent's vertical band (bandTop = parent.y - parent.subtreeHeight/2)
 * @param {boolean} isLeft - Direction: true = left, false = right
 */
function positionNode(node, x, bandTop, isLeft) {
    // Define this node's vertical band
    const bandBottom = bandTop + node.subtreeHeight;
    
    // Position node at center of its band
    node.x = x;
    node.y = bandTop + node.subtreeHeight / 2;
    
    // If no children, we're done
    if (!node.children || node.children.length === 0) {
        return;
    }
    
    // VISUAL IMPROVEMENT: Depth-aware horizontal spacing
    // Deeper levels get progressively more horizontal space
    const childDepth = node.depth + 1;
    const effectiveXGap = getEffectiveXGap(childDepth);
    const childX = isLeft ? x - effectiveXGap : x + effectiveXGap;
    
    // VISUAL IMPROVEMENT: Depth-aware vertical spacing
    // Deeper levels get tighter vertical spacing (but still non-overlapping)
    const effectiveYGap = getEffectiveYGap(childDepth);
    
    // Position children sequentially within this node's band
    // Children MUST fit within [bandTop, bandBottom]
    // Calculate total space needed for all children using effective Y_GAP
    const childrenTotalHeight = node.children.reduce((sum, child, index) => {
        return sum + child.subtreeHeight + (index < node.children.length - 1 ? effectiveYGap : 0);
    }, 0);
    
    // Verify children fit in parent's band (should always be true due to PASS 1)
    if (childrenTotalHeight > node.subtreeHeight) {
        console.error('Children exceed parent band - layout calculation error:', {
            node: node.data.name,
            parentSubtreeHeight: node.subtreeHeight,
            childrenTotalHeight,
            effectiveYGap,
            bandTop,
            bandBottom
        });
    }
    
    // Position children sequentially starting at bandTop
    let childBandTop = bandTop;
    
    node.children.forEach((child, index) => {
        // Position child within parent's band
        // childBandTop is the top of child's allocated space within parent's band
        positionNode(child, childX, childBandTop, isLeft);
        
        // Move to next child's band top
        // Each child consumes exactly child.subtreeHeight + effectiveYGap
        childBandTop += child.subtreeHeight + effectiveYGap;
        
        // Verify child stays within parent's band
        const childBandBottom = childBandTop - effectiveYGap; // Current child's bottom
        if (childBandBottom > bandBottom) {
            console.error('Child band exceeds parent band:', {
                parent: node.data.name,
                child: child.data.name,
                parentBand: [bandTop, bandBottom],
                childBandBottom,
                effectiveYGap
            });
        }
    });
    
    // Center parent vertically over its children (within band constraints)
    // This improves visual appearance while maintaining band constraints
    const childMinY = Math.min(...node.children.map(c => {
        const bounds = c.nodeBounds;
        return c.y - bounds.height / 2;
    }));
    const childMaxY = Math.max(...node.children.map(c => {
        const bounds = c.nodeBounds;
        return c.y + bounds.height / 2;
    }));
    
    // Calculate desired centered position
    const desiredY = (childMinY + childMaxY) / 2;
    
    // Constrain parent to its band: [bandTop, bandBottom]
    const ownBounds = node.nodeBounds;
    const minAllowedY = bandTop + ownBounds.height / 2;
    const maxAllowedY = bandBottom - ownBounds.height / 2;
    
    // Center parent within band, but don't violate band boundaries
    node.y = Math.max(minAllowedY, Math.min(maxAllowedY, desiredY));
}

/**
 * Layout a subtree of sibling nodes
 * Each sibling gets its own vertical band that doesn't overlap with others
 * Uses depth-aware Y_GAP for improved aspect ratio
 * @param {Array} nodes - Array of sibling nodes to layout
 * @param {number} parentX - X position of parent
 * @param {boolean} isLeft - Direction: true = left, false = right
 * @param {number} bandTop - Top of vertical band for this group of siblings
 */
function layoutSubtree(nodes, parentX, isLeft, bandTop = 0) {
    if (nodes.length === 0) return;
    
    // Get depth-aware Y_GAP for this level
    // For root's children, depth is 1
    const nodeDepth = nodes[0] ? nodes[0].depth : 1;
    const effectiveYGap = getEffectiveYGap(nodeDepth);
    
    // Position each sibling node in its own non-overlapping band
    let currentBandTop = bandTop;
    
    nodes.forEach((node, index) => {
        // Position node and all its descendants within its band
        // Each sibling gets exactly node.subtreeHeight worth of vertical space
        positionNode(node, parentX, currentBandTop, isLeft);
        
        // Move to next sibling's band top
        // Sibling bands are separated by depth-aware Y_GAP
        currentBandTop += node.subtreeHeight + effectiveYGap;
    });
    
    // Center all nodes around Y=0 (for root's children only)
    // This maintains band structure but centers the entire group
    if (bandTop === 0) {
        const totalHeight = currentBandTop - effectiveYGap; // Remove last gap
        const centerOffset = -totalHeight / 2;
        
        // Adjust all nodes and their descendants by the same offset
        // This preserves band relationships while centering the group
        nodes.forEach(node => {
            adjustSubtreeY(node, centerOffset);
        });
    }
}

/**
 * Adjust Y position of a node and all its descendants
 * @param {Object} node - D3 hierarchy node
 * @param {number} offset - Y offset to apply
 */
function adjustSubtreeY(node, offset) {
    node.y += offset;
    if (node.children) {
        node.children.forEach(child => adjustSubtreeY(child, offset));
    }
}

// Render D3.js mind map
function renderD3MindMap(d3Data, container) {
    try {
        // Ensure we have a valid font family, fallback to Arial
        let fontFamily = d3Data.fontFamily || currentFontFamily || "Arial, sans-serif";
        
        // Sanitize font family - remove any invalid characters
        fontFamily = fontFamily.replace(/[<>"']/g, '').trim();
        if (!fontFamily) {
            fontFamily = "Arial, sans-serif";
        }
        
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        if (width === 0 || height === 0) {
            console.warn('Container has zero dimensions, waiting for resize');
            setTimeout(() => renderD3MindMap(d3Data, container), 100);
            return;
        }
        
        // Clear container
        container.innerHTML = '';
        
        const svg = d3.select(container)
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        const g = svg.append("g");
        
        // Create zoom behavior - camera only, never modifies node positions
        let zoom = d3.zoom()
            .scaleExtent([0.1, 5])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });
        
        svg.call(zoom);
        
        // Build hierarchy
        const root = d3.hierarchy(d3Data.data);
        
        // Store formatted text on nodes for later rendering
        // Use try-catch for each node to handle font measurement failures gracefully
        root.each(d => {
            try {
                const bounds = calculateNodeBounds(d, fontFamily);
                d.formattedText = bounds.formattedText;
                d.nodeBounds = { width: bounds.width, height: bounds.height };
            } catch (error) {
                console.warn('Error calculating bounds for node:', d.data.name, error);
                // Use fallback bounds
                d.formattedText = d.data.name || '';
                d.nodeBounds = { 
                    width: LAYOUT_CONSTANTS.NODE_MIN_WIDTH, 
                    height: LAYOUT_CONSTANTS.NODE_MIN_HEIGHT 
                };
            }
        });
        
        // Compute layout in world coordinates (pure function)
        // Layout uses formatted text measurements from above
        computeMindMapLayout(root, { fontFamily });
        
        const colors = d3Data.colors;
    
    // COLOR IMPROVEMENT: Color families per branch with sibling differentiation
    // Assign base color (hue) to each first-level child, descendants inherit hue
    const branchHueMap = new Map();
    const FAN_OUT_PX = LAYOUT_CONSTANTS.FAN_OUT_PX; // Max horizontal offset for siblings
    
    // Assign base hue to each root child (level 1)
    if (root.children) {
        root.children.forEach((branch, index) => {
            // Generate base hue for this branch based on index (deterministic)
            const hue = (index * 360 / root.children.length) % 360;
            
            // Store base hue for this branch and all descendants
            branchHueMap.set(branch, hue);
            branch.each(d => {
                if (d !== branch) {
                    branchHueMap.set(d, hue);
                }
            });
        });
    }
    
    /**
     * Get node color with sibling differentiation
     * - Hue: constant within branch (from root child)
     * - Saturation: depth-aware (stronger at level 1, reduces with depth)
     * - Lightness: varies among siblings + depth adjustment
     */
    function getNodeColor(node) {
        if (node.depth === 0) {
            // Root: use light neutral color
            return node.data.color || colors.root || COLOR_CONFIG.rootDefault;
        }
        
        const baseHue = branchHueMap.get(node);
        if (baseHue === undefined) {
            return node.data.color || COLOR_CONFIG.fallback;
        }
        
        // Get sibling index for lightness variation
        let siblingIndex = 0;
        let siblingCount = 1;
        if (node.parent && node.parent.children) {
            siblingCount = node.parent.children.length;
            siblingIndex = node.parent.children.indexOf(node);
        }
        
        // SIBLING DIFFERENTIATION: Vary lightness among siblings
        // Siblings get different lightness values (LIGHT colors only)
        const siblingLightnessBase = COLOR_CONFIG.siblingLightnessMin + 
            (siblingIndex / Math.max(1, siblingCount - 1)) * COLOR_CONFIG.siblingLightnessRange;
        
        // DEPTH-AWARE TREATMENT:
        // - Level 1: moderate saturation, light base
        // - Level 2+: reduce saturation further and increase lightness
        let saturation, lightness;
        if (node.depth === 1) {
            saturation = COLOR_CONFIG.depth1Saturation;
            lightness = siblingLightnessBase;
        } else {
            // Deeper levels: reduce saturation and increase lightness (even lighter)
            const depthAdjust = (node.depth - 1) * 0.1;
            saturation = Math.max(
                COLOR_CONFIG.depth2PlusSaturationMin, 
                COLOR_CONFIG.depth1Saturation - depthAdjust * COLOR_CONFIG.depth2PlusSaturationReduce
            );
            lightness = Math.min(
                COLOR_CONFIG.depthLightnessMax, 
                siblingLightnessBase + depthAdjust * COLOR_CONFIG.depthLightnessIncrease
            );
        }
        
        return d3.hsl(baseHue, saturation, lightness).toString();
    }
    
    /**
     * Get stroke color (darker shade of fill)
     * Stroke intensity varies slightly among siblings for better distinction
     */
    function getStrokeColor(node) {
        if (node.depth === 0) {
            const rootColor = node.data.color || colors.root || COLOR_CONFIG.rootDefault;
            const hsl = d3.hsl(rootColor);
            // Light stroke: reduce lightness slightly but keep it light
            return d3.hsl(hsl.h, hsl.s, Math.max(COLOR_CONFIG.strokeLightnessMin, hsl.l - 0.1)).toString();
        }
        
        const fillColor = getNodeColor(node);
        const hsl = d3.hsl(fillColor);
        
        // Get sibling index for stroke variation
        let siblingIndex = 0;
        if (node.parent && node.parent.children) {
            siblingIndex = node.parent.children.indexOf(node);
        }
        
        // Light stroke: vary slightly among siblings but keep it light
        const strokeDarkness = COLOR_CONFIG.strokeDarknessMin + (siblingIndex % 2) * 
            (COLOR_CONFIG.strokeDarknessMax - COLOR_CONFIG.strokeDarknessMin);
        return d3.hsl(hsl.h, hsl.s, Math.max(COLOR_CONFIG.strokeLightnessMin, hsl.l - strokeDarkness)).toString();
    }
    
    /**
     * Get edge color (matches child node's base color)
     * Edge opacity and stroke width decrease with depth
     */
    function getEdgeColor(link) {
        const child = link.target;
        
        if (child.depth === 0) {
            return colors.edge || COLOR_CONFIG.edgeDefault;
        }
        
        // Use child's color (which already has branch hue)
        const childColor = getNodeColor(child);
        const hsl = d3.hsl(childColor);
        
        // Light edge: slightly desaturate but keep it light
        return d3.hsl(
            hsl.h, 
            Math.max(0.15, hsl.s - COLOR_CONFIG.edgeDesaturate), // Desaturate slightly
            Math.max(COLOR_CONFIG.edgeLightnessMin, hsl.l - COLOR_CONFIG.edgeLightnessReduce) // Keep light
        ).toString();
    }
    
    // VISUAL IMPROVEMENT 1: Calculate horizontal fan-out for siblings
    function getSiblingFanOut(node) {
        if (!node.parent || !node.parent.children) return 0;
        
        const siblings = node.parent.children;
        const index = siblings.indexOf(node);
        const count = siblings.length;
        
        if (count <= 1) return 0;
        
        // Symmetric offset around parent
        const offset = (index - (count - 1) / 2) * FAN_OUT_PX;
        return offset;
    }
    
    // VISUAL IMPROVEMENT 4 & 5: Edge anchoring and visual hierarchy
    // Helper: Get edge anchor point on node box (accounts for fan-out)
    function getEdgeAnchor(node, isSource) {
        const bounds = node.nodeBounds;
        const fanOut = getSiblingFanOut(node);
        const isLeft = node.x < 0;
        const actualX = node.x + fanOut; // Account for visual fan-out offset
        
        if (isSource) {
            // Source anchor: connect from parent's edge (right edge for left nodes, left edge for right nodes)
            const edgeX = isLeft ? actualX + bounds.width / 2 : actualX - bounds.width / 2;
            return { x: edgeX, y: node.y };
        } else {
            // Target anchor: connect to child's edge (left edge for left nodes, right edge for right nodes)
            const edgeX = isLeft ? actualX - bounds.width / 2 : actualX + bounds.width / 2;
            return { x: edgeX, y: node.y };
        }
    }
    
    // Draw links - curved arrows with improved visual hierarchy
    const links = g.selectAll(".link")
        .data(root.links())
        .enter()
        .append("path")
        .attr("class", "link")
        .attr("d", d => {
            const source = d.source;
            const target = d.target;
            const depth = target.depth;
            
            // Get anchor points on box edges
            const sourceAnchor = getEdgeAnchor(source, true);
            const targetAnchor = getEdgeAnchor(target, false);
            
            // Create smooth curved path using quadratic bezier
            const dx = targetAnchor.x - sourceAnchor.x;
            const dy = targetAnchor.y - sourceAnchor.y;
            const controlX = sourceAnchor.x + dx * 0.5;
            const controlY = sourceAnchor.y + dy * 0.5;
            
            // VISUAL IMPROVEMENT 5: Curvature increases slightly with depth
            const curveFactor = 0.3 + (depth - 1) * 0.05; // Slightly more curve for deeper levels
            const perpX = -dy * curveFactor;
            const perpY = dx * curveFactor;
            
            return `M ${sourceAnchor.x} ${sourceAnchor.y} Q ${controlX + perpX} ${controlY + perpY} ${targetAnchor.x} ${targetAnchor.y}`;
        })
        .attr("stroke", d => getEdgeColor(d))
        .attr("stroke-width", d => {
            // VISUAL IMPROVEMENT 5: Thickness decreases with depth
            const depth = d.target.depth;
            return Math.max(1.5, 3 - depth * 0.3);
        })
        .attr("fill", "none")
        .attr("opacity", d => {
            // VISUAL IMPROVEMENT 5: Opacity reduces with depth
            const depth = d.target.depth;
            return Math.max(0.4, 0.8 - depth * 0.1);
        });
    
    // Draw nodes
    const nodes = g.selectAll(".node")
        .data(root.descendants())
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("transform", d => {
            // VISUAL IMPROVEMENT 1: Apply gentle horizontal fan-out for siblings
            // This is visual-only and doesn't affect layout positions
            const fanOut = getSiblingFanOut(d);
            return `translate(${d.x + fanOut}, ${d.y})`;
        });
    
    // VISUAL IMPROVEMENT 6: Hover highlight (optional)
    let hoveredNode = null;
    
    // Render nodes: use pre-calculated bounds from layout phase
    // Bounds were calculated using formatted text, so boxes will always fit
    nodes.each(function(d) {
        const node = d3.select(this);
        
        // VISUAL IMPROVEMENT 3: Depth-based typography rhythm
        let fontSize, fontWeight, lineHeight;
        if (d.depth === 0) {
            fontSize = 16;
            fontWeight = 600;
            lineHeight = 1.2;
        } else if (d.depth === 1) {
            fontSize = 14;
            fontWeight = 500;
            lineHeight = 1.25;
        } else {
            fontSize = 12;
            fontWeight = 400;
            lineHeight = 1.3;
        }
        
        // Get pre-calculated bounds and formatted text (from layout phase)
        const bounds = d.nodeBounds;
        const formattedText = d.formattedText;
        
        if (!bounds || !formattedText) {
            console.warn('Node missing bounds or formatted text:', d);
            return;
        }
        
        // VISUAL IMPROVEMENT 2: Use branch color family
        const nodeFillColor = getNodeColor(d);
        const nodeStrokeColor = getStrokeColor(d);
        
        // STEP 1: Draw rectangle sized to fit text (bounds already account for text size)
        node.append("rect")
            .attr("x", -bounds.width / 2)
            .attr("y", -bounds.height / 2)
            .attr("width", bounds.width)
            .attr("height", bounds.height)
            .attr("rx", 8)
            .attr("ry", 8)
            .attr("fill", nodeFillColor)
            .attr("stroke", nodeStrokeColor)
            .attr("stroke-width", d.depth === 0 ? 3 : d.depth === 1 ? 2.5 : 2)
            .style("cursor", "pointer")
            .on("mouseenter", function() {
                // VISUAL IMPROVEMENT 6: Hover highlight
                hoveredNode = d;
                nodes.each(function(n) {
                    const nNode = d3.select(this);
                    // Highlight: hovered node, its ancestors, and its descendants
                    const isAncestorOfHovered = isAncestor(n, d);
                    const isDescendantOfHovered = isDescendantOf(d, n);
                    const isHovered = n === d;
                    
                    if (isHovered || isAncestorOfHovered || isDescendantOfHovered) {
                        nNode.select("rect").style("opacity", 1);
                        nNode.select("text").style("opacity", 1);
                    } else {
                        nNode.select("rect").style("opacity", 0.3);
                        nNode.select("text").style("opacity", 0.3);
                    }
                });
                
                // Highlight relevant links
                links.style("opacity", l => {
                    const connectsToHovered = l.source === d || l.target === d;
                    const connectsAncestor = isAncestor(l.source, d) || isAncestor(l.target, d);
                    const connectsDescendant = isDescendantOf(d, l.source) || isDescendantOf(d, l.target);
                    return (connectsToHovered || connectsAncestor || connectsDescendant) ? 1 : 0.2;
                });
            })
            .on("mouseleave", function() {
                hoveredNode = null;
                nodes.selectAll("rect").style("opacity", 1);
                nodes.selectAll("text").style("opacity", 1);
                links.style("opacity", null); // Reset to default opacity from attr()
            });
        
        // STEP 2: Draw visible text (formatted, guaranteed to fit in box)
        node.append("text")
            .attr("dy", 5)
            .attr("text-anchor", "middle")
            .attr("fill", d.data.textColor || (d.depth === 0 ? '#fff' : '#333'))
            .attr("font-size", fontSize + "px")
            .attr("font-weight", fontWeight)
            .attr("font-family", fontFamily)
            .attr("line-height", lineHeight)
            .style("pointer-events", "none")
            .text(formattedText);
    });
    
    // Helper functions for hover highlight
    function isAncestor(ancestor, node) {
        let current = node.parent;
        while (current) {
            if (current === ancestor) return true;
            current = current.parent;
        }
        return false;
    }
    
    function isDescendantOf(ancestor, node) {
        if (!ancestor.children) return false;
        for (let child of ancestor.children) {
            if (child === node || isDescendantOf(child, node)) return true;
        }
        return false;
    }
    
    // Initial camera position: center root at 1.0 scale
    setTimeout(() => {
        // Center root at viewport center, scale 1.0
        const translateX = width / 2 - root.x;
        const translateY = height / 2 - root.y;
        
        svg.transition().duration(500).call(
            zoom.transform,
            d3.zoomIdentity.translate(translateX, translateY).scale(1.0)
        );
    }, 100);
    
    // Store zoom functions globally for buttons
    window.d3ZoomIn = () => svg.transition().call(zoom.scaleBy, 1.3);
    window.d3ZoomOut = () => svg.transition().call(zoom.scaleBy, 0.7);
    window.d3ResetZoom = () => {
        // Zoom to fit: move camera to show entire mind map
        const bounds = g.node().getBBox();
        const fullWidth = bounds.width;
        const fullHeight = bounds.height;
        const padding = 50;
        
        // Calculate scale to fit (camera only, not positions)
        const scale = Math.min(
            (width - 2 * padding) / fullWidth, 
            (height - 2 * padding) / fullHeight
        );
        
        // Calculate translation to center bounds in viewport (camera only)
        const centerX = bounds.x + bounds.width / 2;
        const centerY = bounds.y + bounds.height / 2;
        const translateX = width / 2 - centerX * scale;
        const translateY = height / 2 - centerY * scale;
        
        svg.transition().duration(500).call(
            zoom.transform,
            d3.zoomIdentity.translate(translateX, translateY).scale(scale)
        );
    };
    } catch (error) {
        console.error('Error rendering mind map:', error);
        container.innerHTML = `<div class="error-message">Error rendering mind map: ${error.message}</div>`;
        throw error;
    }
}

// Change style
function changeStyle(style) {
    currentStyle = style;
    if (currentMindMapId) {
        loadMindMap(currentMindMapId);
    }
}

// Change palette
async function changePalette(palette) {
    try {
        currentPalette = palette;
        
        // Update active state
        document.querySelectorAll('.palette-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`[data-palette="${palette}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
        
        if (currentMindMapId) {
            await loadMindMap(currentMindMapId);
        }
        if (currentSequenceDiagramId) {
            await loadSequenceDiagram(currentSequenceDiagramId);
        }
        if (currentFlowchartId) {
            await loadFlowchart(currentFlowchartId);
        }
    } catch (error) {
        console.error('Error changing palette:', error);
        alert('Error changing color palette: ' + error.message);
    }
}

// Show loading
function showLoading() {
    const container = document.getElementById('mindmap-container');
    container.innerHTML = '<div class="loading">Creating mind map... Please wait</div>';
}

// Hide loading
function hideLoading() {
    // Loading is hidden when mind map is displayed
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Toggle sidebar
function toggleSidebar(side) {
    const sidebar = document.getElementById(`${side}-sidebar`);
    const toggleIcon = document.getElementById(`${side}-toggle-icon`);
    const container = document.getElementById('mindmap-container');
    
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        
        // Update toggle icon
        if (toggleIcon) {
            if (sidebar.classList.contains('collapsed')) {
                if (side === 'left') {
                    toggleIcon.textContent = '▶';
                } else {
                    toggleIcon.textContent = '◀';
                }
            } else {
                if (side === 'left') {
                    toggleIcon.textContent = '◀';
                } else {
                    toggleIcon.textContent = '▶';
                }
            }
        }
        
        // Wait for CSS transition to complete, then resize
        setTimeout(() => {
            // Force a layout recalculation
            if (container) {
                // Trigger a reflow to ensure container has new dimensions
                void container.offsetWidth;
                
                // If there's a D3 visualization, manually trigger resize
                if (container.querySelector('svg')) {
                    const svg = container.querySelector('svg');
                    const newWidth = container.clientWidth;
                    const newHeight = container.clientHeight;
                    
                    if (svg && newWidth > 0 && newHeight > 0) {
                        // Update SVG dimensions
                        d3.select(svg)
                            .attr('width', newWidth)
                            .attr('height', newHeight);
                        
                        // If there's a zoom behavior, reset it to fit new dimensions
                        if (window.d3ResetZoom) {
                            setTimeout(() => window.d3ResetZoom(), 50);
                        }
                    }
                }
            }
            
            // Trigger resize event for any other listeners
            window.dispatchEvent(new Event('resize'));
        }, 350); // Wait for CSS transition (0.3s) to complete
    }
}


// Change renderer
function changeRenderer(renderer) {
    currentRenderer = renderer;
    if (currentMindMapId) {
        loadMindMap(currentMindMapId);
    }
}

// Change font
async function changeFont(fontFamily) {
    try {
        currentFontFamily = fontFamily;
        if (currentMindMapId) {
            await loadMindMap(currentMindMapId);
        }
        if (currentSequenceDiagramId) {
            await loadSequenceDiagram(currentSequenceDiagramId);
        }
        if (currentFlowchartId) {
            await loadFlowchart(currentFlowchartId);
        }
    } catch (error) {
        console.error('Error changing font:', error);
        alert('Error changing font: ' + error.message);
    }
}

// Zoom functions
function zoomIn() {
    if (window.d3ZoomIn) {
        window.d3ZoomIn();
    } else if (network) {
        const scale = network.getScale();
        network.moveTo({
            scale: scale * 1.3,
            animation: {
                duration: 300,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
}

function zoomOut() {
    if (window.d3ZoomOut) {
        window.d3ZoomOut();
    } else if (network) {
        const scale = network.getScale();
        network.moveTo({
            scale: scale * 0.7,
            animation: {
                duration: 300,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
}

function resetZoom() {
    if (window.d3ResetZoom) {
        window.d3ResetZoom();
    } else if (network) {
        network.fit({
            animation: {
                duration: 400,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
}

// Keyboard shortcuts for zoom
document.addEventListener('keydown', function(event) {
    if (event.ctrlKey || event.metaKey) {
        if (event.key === '=' || event.key === '+') {
            event.preventDefault();
            zoomIn();
        } else if (event.key === '-') {
            event.preventDefault();
            zoomOut();
        } else if (event.key === '0') {
            event.preventDefault();
            resetZoom();
        }
    }
});

