// ==================== Init ====================
(function init() {
    if (typeof isStaticPreviewHost === 'function' && isStaticPreviewHost()) {
        window.location.replace(`${BACKEND_ORIGIN}/dashboard`);
        return;
    }

    if (!API.getToken()) {
        goToPage('login');
        return;
    }

    // Initialize theme first
    initializeTheme();

    const user = API.getUser();
    if (user) {
        document.getElementById('sidebarUser').textContent = user.username;
    }

    // Navigation
    document.querySelectorAll('.sidebar nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            switchPage(page);
        });
    });

    loadFiles();
    loadProfile();
    initializeBotWidget();
})();

// ==================== Navigation ====================
function switchPage(page) {
    document.querySelectorAll('.main-content > section').forEach(s => s.classList.add('hidden'));
    document.getElementById('page-' + page).classList.remove('hidden');
    document.querySelectorAll('.sidebar nav a').forEach(a => a.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`).classList.add('active');

    window.currentDashboardPage = page;

    if (page === 'files' || page === 'shared') loadFiles();
    if (page === 'shared-by-me') loadShareHistory();
    if (page === 'audit') loadAuditLog();
    if (page === 'security') loadProfile();
}

// ==================== Files ====================
let allFiles = { owned: [], shared: [] };

async function loadFiles() {
    hideAlert('alert-files');
    const { status, data } = await API.get('/files/');
    if (status !== 200) {
        const message = data?.error || 'Unable to load files. Ensure backend server is running.';
        showAlert('alert-files', message, 'danger');
        renderOwnedFiles([]);
        renderSharedFiles([]);
        renderStats({ owned: [], shared: [] });
        renderVisibleFeaturePanel();
        return;
    }

    allFiles = data?.files || { owned: [], shared: [] };
    renderOwnedFiles(allFiles.owned);
    renderSharedFiles(allFiles.shared);
    renderStats(allFiles);
    renderVisibleFeaturePanel();
}

function renderVisibleFeaturePanel() {
    const select = document.getElementById('featureFileSelect');
    const result = document.getElementById('visibleFeatureResult');
    if (!select || !result) return;

    const files = allFiles?.owned || [];
    if (!files.length) {
        select.innerHTML = '<option value="">No files available</option>';
        select.disabled = true;
        result.innerHTML = '<p class="text-muted">Upload a file to use AI insights.</p>';
        return;
    }

    select.disabled = false;
    select.innerHTML = files.map(file => (
        `<option value="${file.id}" data-filename="${escapeAttr(file.filename)}">${escapeHtml(file.filename)} (${escapeHtml((file.file_type || 'unknown').toUpperCase())})</option>`
    )).join('');

    result.innerHTML = '<p class="text-muted">Select a file and click "Run AI Insights".</p>';
}

function _selectedFeatureFile() {
    const select = document.getElementById('featureFileSelect');
    if (!select || !select.value) return null;

    const selectedId = parseInt(select.value, 10);
    if (!selectedId) return null;

    const file = (allFiles?.owned || []).find(item => item.id === selectedId);
    if (!file) return null;
    return file;
}

async function runVisibleAiInsights() {
    const selected = _selectedFeatureFile();
    const result = document.getElementById('visibleFeatureResult');
    if (!selected || !result) {
        alert('Please select a file first.');
        return;
    }

    await loadFileInsights(selected.id, 'visibleFeatureResult');
}

async function loadShareHistory() {
    const { status, data } = await API.get('/files/share-history');
    if (status !== 200) {
        renderShareHistory([]);
        return;
    }

    renderShareHistory(data.records || []);
}

function actionIcon(name) {
    const icons = {
        download: '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/></svg>',
        share: '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 10.7l6.8-3.4"/><path d="M8.6 13.3l6.8 3.4"/></svg>',
        preview: '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z"/><circle cx="12" cy="12" r="3"/></svg>',
        metadata: '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><circle cx="12" cy="8" r=".8" fill="currentColor" stroke="none"/></svg>',
        delete: '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18"/><path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2"/><path d="M19 6l-1 14a1 1 0 0 1-1 .9H7a1 1 0 0 1-1-.9L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>',
    };
    return icons[name] || '';
}

function renderOwnedFiles(files) {
    const table = document.getElementById('fileTable');
    const empty = document.getElementById('emptyFiles');
    const tbody = document.getElementById('fileTableBody');

    if (!files || files.length === 0) {
        table.classList.add('hidden');
        empty.classList.remove('hidden');
        tbody.innerHTML = '';
        return;
    }

    empty.classList.add('hidden');
    table.classList.remove('hidden');

    tbody.innerHTML = files.map(file => `
        <tr>
            <td title="${escapeAttr(file.filename)}">${fileIcon(file.file_type)} ${escapeHtml(file.filename)}</td>
            <td><span class="badge badge-info">${escapeHtml((file.file_type || 'unknown').toUpperCase())}</span></td>
            <td>${formatBytes(file.file_size)}</td>
            <td>${file.is_encrypted ? '<span class="badge badge-success">Yes</span>' : '<span class="badge badge-warning">No</span>'}</td>
            <td>${formatDate(file.created_at)}</td>
            <td>
                <div class="table-actions">
                    <button class="btn-icon" title="Download" aria-label="Download" onclick="downloadFile(${file.id}, '${escapeAttr(file.filename)}')">${actionIcon('download')}</button>
                    <button class="btn-icon" title="Share" aria-label="Share" onclick="openShareModal(${file.id})">${actionIcon('share')}</button>
                    <button class="btn-icon" title="Preview" aria-label="Preview" onclick="openFilePreview(${file.id}, '${escapeAttr(file.filename)}', '${escapeAttr(file.file_type || '')}')">${actionIcon('preview')}</button>
                    <button class="btn-icon" title="Metadata" aria-label="Metadata" onclick="viewMetadata(${file.id})">${actionIcon('metadata')}</button>
                    <button class="btn-icon btn-danger" title="Delete" aria-label="Delete" onclick="deleteFile(${file.id})">${actionIcon('delete')}</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderSharedFiles(files) {
    const table = document.getElementById('sharedTable');
    const empty = document.getElementById('emptyShared');
    const tbody = document.getElementById('sharedTableBody');

    if (!files || files.length === 0) {
        table.classList.add('hidden');
        empty.classList.remove('hidden');
        tbody.innerHTML = '';
        return;
    }

    empty.classList.add('hidden');
    table.classList.remove('hidden');

    tbody.innerHTML = files.map(file => `
        <tr>
            <td title="${escapeAttr(file.filename)}">${fileIcon(file.file_type)} ${escapeHtml(file.filename)}</td>
            <td><span class="badge badge-info">${escapeHtml((file.file_type || 'unknown').toUpperCase())}</span></td>
            <td>${formatBytes(file.file_size)}</td>
            <td>${escapeHtml(file.shared_by_username || file.owner_username || '-')}</td>
            <td>${formatDate(file.shared_at)}</td>
            <td>${formatDate(file.created_at)}</td>
            <td>
                <div class="table-actions">
                    <button class="btn-icon" title="Download" aria-label="Download" onclick="downloadFile(${file.id}, '${escapeAttr(file.filename)}')">${actionIcon('download')}</button>
                    <button class="btn-icon" title="Preview" aria-label="Preview" onclick="openFilePreview(${file.id}, '${escapeAttr(file.filename)}', '${escapeAttr(file.file_type || '')}')">${actionIcon('preview')}</button>
                    <button class="btn-icon" title="Metadata" aria-label="Metadata" onclick="viewMetadata(${file.id})">${actionIcon('metadata')}</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderStats(files) {
    const statsRow = document.getElementById('statsRow');
    if (!statsRow) return;

    const owned = files?.owned || [];
    const shared = files?.shared || [];
    const totalBytes = [...owned, ...shared].reduce((sum, file) => sum + (file.file_size || 0), 0);
    const encryptedCount = [...owned, ...shared].filter(file => file.is_encrypted).length;

    statsRow.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">My Files</div>
            <div class="stat-value">${owned.length}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Shared With Me</div>
            <div class="stat-value">${shared.length}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Size</div>
            <div class="stat-value">${formatBytes(totalBytes)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Encrypted</div>
            <div class="stat-value">${encryptedCount}/${owned.length + shared.length}</div>
        </div>
    `;
}

function renderShareHistory(records) {
    const table = document.getElementById('shareHistoryTable');
    const empty = document.getElementById('emptyShareHistory');
    const tbody = document.getElementById('shareHistoryTableBody');

    if (!records || records.length === 0) {
        table.classList.add('hidden');
        empty.classList.remove('hidden');
        tbody.innerHTML = '';
        return;
    }

    empty.classList.add('hidden');
    table.classList.remove('hidden');

    tbody.innerHTML = records.map(record => `
        <tr>
            <td>${formatDateTimeWithSeconds(record.created_at)}</td>
            <td>${escapeHtml(record.filename || '-')}</td>
            <td>${escapeHtml(record.target_username || '-')}</td>
            <td>${renderShareActionBadge(record.action)}</td>
            <td>${escapeHtml(record.permission || record.previous_permission || '-')}</td>
        </tr>
    `).join('');
}

function renderShareActionBadge(action) {
    const normalized = String(action || '').toUpperCase();
    const label = escapeHtml((action || '-').replace('_', ' '));
    if (normalized.includes('REVOKE')) {
        return `<span class="badge badge-warning">${label}</span>`;
    }
    return `<span class="badge badge-success">${label}</span>`;
}

// ==================== Upload ====================
function openUploadModal() {
    document.getElementById('fileInput').value = '';
    hideAlert('alert-upload');
    openModal('uploadModal');
}

async function uploadFile() {
    const input = document.getElementById('fileInput');
    if (!input.files.length) {
        showAlert('alert-upload', 'Please select a file.', 'danger');
        return;
    }

    const btn = document.getElementById('uploadBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Uploading...';

    const { status, data } = await API.uploadFile(input.files[0]);

    btn.disabled = false;
    btn.textContent = 'Upload';

    if (status === 201) {
        closeModal('uploadModal');
        loadFiles();
    } else {
        const msg = data.errors ? data.errors.join('\n') : (data.error || 'Upload failed.');
        showAlert('alert-upload', msg, 'danger');
    }
}

// ==================== Download ====================
async function downloadFile(fileId, filename) {
    const { status, data } = await API.get(`/files/${fileId}`);
    if (status !== 200) {
        alert(data.error || 'Failed to download file.');
        return;
    }

    // Decode base64 content
    const byteChars = atob(data.file.content);
    const byteArray = new Uint8Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
        byteArray[i] = byteChars.charCodeAt(i);
    }
    const blob = new Blob([byteArray]);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function _base64ToBlob(base64Data, mimeType = 'application/octet-stream') {
    const byteChars = atob(base64Data);
    const byteArray = new Uint8Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
        byteArray[i] = byteChars.charCodeAt(i);
    }
    return new Blob([byteArray], { type: mimeType });
}

function _mimeTypeFromFileType(fileType) {
    const normalized = (fileType || '').toLowerCase();
    const mapping = {
        // Documents
        pdf: 'application/pdf',
        txt: 'text/plain',
        log: 'text/plain',
        md: 'text/markdown',
        rst: 'text/plain',
        rtf: 'application/rtf',
        json: 'application/json',
        xml: 'application/xml',
        csv: 'text/csv',
        tsv: 'text/tab-separated-values',
        yaml: 'application/yaml',
        yml: 'application/yaml',
        toml: 'application/toml',
        ini: 'text/plain',
        cfg: 'text/plain',
        conf: 'text/plain',
        odt: 'application/vnd.oasis.opendocument.text',
        ods: 'application/vnd.oasis.opendocument.spreadsheet',
        odp: 'application/vnd.oasis.opendocument.presentation',
        
        // Images
        png: 'image/png',
        jpg: 'image/jpeg',
        jpeg: 'image/jpeg',
        gif: 'image/gif',
        webp: 'image/webp',
        bmp: 'image/bmp',
        svg: 'image/svg+xml',
        ico: 'image/x-icon',
        
        // Audio
        mp3: 'audio/mpeg',
        wav: 'audio/wav',
        flac: 'audio/flac',
        aac: 'audio/aac',
        m4a: 'audio/mp4',
        ogg: 'audio/ogg',
        
        // Video
        mp4: 'video/mp4',
        webm: 'video/webm',
        avi: 'video/x-msvideo',
        mov: 'video/quicktime',
        mkv: 'video/x-matroska',
        flv: 'video/x-flv',
        wmv: 'video/x-ms-wmv',
        m4v: 'video/x-m4v',
        
        // Microsoft Office (OOXML)
        docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        doc: 'application/msword',
        xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        xls: 'application/vnd.ms-excel',
        pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        ppt: 'application/vnd.ms-powerpoint',
        
        // Archives
        zip: 'application/zip',
        rar: 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
        gz: 'application/gzip',
        tar: 'application/x-tar',
        bz2: 'application/x-bzip2',
        xz: 'application/x-xz',
        
        // Code
        py: 'text/plain',
        js: 'text/plain',
        ts: 'text/plain',
        jsx: 'text/plain',
        tsx: 'text/plain',
        cpp: 'text/plain',
        c: 'text/plain',
        java: 'text/plain',
        go: 'text/plain',
        rs: 'text/plain',
        rb: 'text/plain',
        php: 'text/plain',
        sh: 'text/plain',
        bash: 'text/plain',
        vue: 'text/plain',
        html: 'text/html',
        css: 'text/css',
        sql: 'text/plain',
    };
    return mapping[normalized] || 'application/octet-stream';
}

function _previewUrl(fileId, token, mode = '') {
    const suffix = mode ? `&mode=${encodeURIComponent(mode)}` : '';
    return API.baseUrl + `/files/${fileId}/preview?token=${encodeURIComponent(token)}${suffix}`;
}

function _isPresentationType(fileType) {
    const t = (fileType || '').toLowerCase();
    return t === 'ppt' || t === 'pptx';
}

function _togglePreviewDownloadButton(show, fileType) {
    const btn = document.getElementById('downloadFromPreviewBtn');
    if (!btn) return;

    // Keep presentation previews focused on in-app viewing.
    if (_isPresentationType(fileType)) {
        btn.style.display = 'none';
        return;
    }

    btn.style.display = show ? 'flex' : 'none';
}

function _renderBlobPreview(previewRoot, blob, filename, fileType) {
    const mimeType = _mimeTypeFromFileType((fileType || '').toLowerCase()) || blob.type || 'application/octet-stream';
    const objectUrl = URL.createObjectURL(blob);
    previewRoot.dataset.objectUrl = objectUrl;

    let contentHtml = '';
    let showDownloadBtn = false;

    if (mimeType.startsWith('image/')) {
        contentHtml = `<img src="${objectUrl}" alt="${escapeAttr(filename)}" class="preview-media-image">`;
    } else if (mimeType === 'application/pdf') {
        contentHtml = `<iframe src="${objectUrl}" title="${escapeAttr(filename)}" class="preview-native-frame"></iframe>`;
    } else if (mimeType.startsWith('audio/')) {
        contentHtml = `<div class="preview-center-block">
            <audio controls style="width:100%;max-width:560px;margin:20px 0;">
                <source src="${objectUrl}" type="${mimeType}">
                Your browser does not support audio playback.
            </audio>
            <p class="text-muted">${escapeHtml(filename)}</p>
        </div>`;
    } else if (mimeType.startsWith('video/')) {
        contentHtml = `<div class="preview-center-block">
            <video controls class="preview-media-video">
                <source src="${objectUrl}" type="${mimeType}">
                Your browser does not support video playback.
            </video>
        </div>`;
    } else {
        // Generic page-style native preview attempt (Office, text, other binaries).
        // If browser cannot render, user still sees an embeddable viewer area + download option.
        contentHtml = `<iframe src="${objectUrl}" title="${escapeAttr(filename)}" class="preview-native-frame"></iframe>`;
        showDownloadBtn = true;
    }

    previewRoot.innerHTML = `
        <div class="preview-file-title">${escapeHtml(filename)}</div>
        <div class="preview-surface">${contentHtml}</div>
    `;

    return showDownloadBtn;
}

async function _loadNativeRawPreview(previewRoot, fileId, filename, fileType, token) {
    const response = await fetch(_previewUrl(fileId, token, 'raw'), {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) return false;

    const blob = await response.blob();
    const showDownloadBtn = _renderBlobPreview(previewRoot, blob, filename, fileType);
    _togglePreviewDownloadButton(showDownloadBtn, fileType);
    return true;
}

async function openFilePreview(fileId, filename, fileType) {
    const previewRoot = document.getElementById('previewContent');
    const featurePanel = document.getElementById('previewFeaturePanel');
    const previousObjectUrl = previewRoot.dataset.objectUrl;
    if (previousObjectUrl) {
        URL.revokeObjectURL(previousObjectUrl);
        previewRoot.dataset.objectUrl = '';
    }
    const token = API.getToken();
    const previewUrl = _previewUrl(fileId, token);
    
    // Store file info for download
    previewRoot.dataset.fileId = fileId;
    previewRoot.dataset.filename = filename;
    if (featurePanel) {
        featurePanel.innerHTML = '<p class="text-muted">Loading AI summary...</p>';
    }
    
    try {
        const response = await fetch(previewUrl, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            if (_isPresentationType(fileType)) {
                previewRoot.innerHTML = '<p class="text-muted">Presentation preview is temporarily unavailable for this file.</p>';
                _togglePreviewDownloadButton(false, fileType);
            } else {
                previewRoot.innerHTML = '<p class="text-muted">Preview unavailable. Click "Download File" button below to access this file.</p>';
                _togglePreviewDownloadButton(true, fileType);
            }
            await loadFileInsights(fileId, 'previewFeaturePanel');
            openModal('previewModal');
            return;
        }
        
        const contentType = response.headers.get('content-type') || '';
        
        // Check if response is JSON (HTML preview from converter)
        if (contentType.includes('application/json')) {
            const data = await response.json();
            
            if (data.preview && data.preview.html) {
                // Display converted HTML preview
                previewRoot.innerHTML = `
                    <div class="preview-file-title">${escapeHtml(data.filename || filename)}</div>
                    <div class="preview-surface">${data.preview.html}</div>
                `;
                _togglePreviewDownloadButton(false, fileType);
            } else if (data.preview && data.preview.message) {
                // Error in conversion
                previewRoot.innerHTML = `<p class="text-muted">${escapeHtml(data.preview.message)}</p>`;
                _togglePreviewDownloadButton(true, fileType);
            } else {
                previewRoot.innerHTML = '<p class="text-muted">Preview unavailable.</p>';
                _togglePreviewDownloadButton(true, fileType);
            }
        } else {
            // Raw file response (image, PDF, audio, video)
            const blob = await response.blob();
            const showDownloadBtn = _renderBlobPreview(previewRoot, blob, filename, fileType);
            _togglePreviewDownloadButton(showDownloadBtn, fileType);
        }

        await loadFileInsights(fileId, 'previewFeaturePanel');
    } catch (err) {
        console.error('Preview error:', err);
        previewRoot.innerHTML = '<p class="text-muted">Failed to load preview. Click "Download File" to access this file.</p>';
        _togglePreviewDownloadButton(true, fileType);
        const panel = document.getElementById('previewFeaturePanel');
        if (panel) {
            panel.innerHTML = '<p class="text-muted">AI summary could not be loaded.</p>';
        }
    }
    
    openModal('previewModal');
}

function downloadFromPreview() {
    const previewRoot = document.getElementById('previewContent');
    const fileId = previewRoot.dataset.fileId;
    const filename = previewRoot.dataset.filename;
    if (fileId && filename) {
        downloadFile(fileId, filename);
    }
}

// ==================== Delete ====================
async function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file? This cannot be undone.')) return;

    const { status, data } = await API.del(`/files/${fileId}`);
    if (status === 200) {
        loadFiles();
    } else {
        alert(data.error || 'Failed to delete file.');
    }
}

// ==================== Share ====================
function openShareModal(fileId) {
    document.getElementById('shareFileId').value = fileId;
    document.getElementById('shareUsername').value = '';
    document.getElementById('sharePermission').value = 'read';
    hideAlert('alert-share');
    openModal('shareModal');
}

async function shareFile() {
    const fileId = document.getElementById('shareFileId').value;
    const username = document.getElementById('shareUsername').value.trim();
    const permission = document.getElementById('sharePermission').value;

    if (!username) {
        showAlert('alert-share', 'Please enter a username.', 'danger');
        return;
    }

    const { status, data } = await API.post(`/files/${fileId}/share`, { username, permission });
    if (status === 200) {
        closeModal('shareModal');
        loadFiles();
        loadShareHistory();
    } else {
        showAlert('alert-share', data.error || 'Failed to share file.', 'danger');
    }
}

// ==================== Metadata ====================
async function viewMetadata(fileId) {
    const { status, data } = await API.get(`/files/${fileId}/metadata`);
    if (status !== 200) {
        alert(data.error || 'Failed to load metadata.');
        return;
    }

    const m = data.metadata;
    const metaModal = document.getElementById('metaModal');
    metaModal.dataset.fileId = fileId;
    metaModal.dataset.filename = m.filename || 'file';

    let permsHtml = '';
    if (m.permissions && m.permissions.length > 0) {
        permsHtml = `
            <h4 style="margin-top:20px; margin-bottom:8px;">Shared With</h4>
            <table class="file-table" style="margin:0">
                <thead><tr><th>User</th><th>Permission</th><th>Granted By</th><th>Granted At</th><th>Updated At</th></tr></thead>
                <tbody>
                    ${m.permissions.map(p => `
                        <tr>
                            <td>${escapeHtml(p.username)}</td>
                            <td><span class="badge badge-info">${escapeHtml(p.permission)}</span></td>
                            <td>${escapeHtml(p.granted_by_username || '-')}</td>
                            <td>${formatDate(p.created_at)}</td>
                            <td>${formatDate(p.updated_at)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    document.getElementById('metaContent').innerHTML = `
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">Filename</div>
                <div class="meta-value">${escapeHtml(m.filename)}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">File Type</div>
                <div class="meta-value">${escapeHtml(m.file_type || 'unknown')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Size</div>
                <div class="meta-value">${formatBytes(m.file_size)}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Encrypted</div>
                <div class="meta-value">${m.is_encrypted ? '✅ Yes' : '❌ No'}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Created</div>
                <div class="meta-value">${formatDate(m.created_at)}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Updated</div>
                <div class="meta-value">${formatDate(m.updated_at)}</div>
            </div>
        </div>
        ${permsHtml}
        <div class="feature-panel" id="fileInsightsContainer">
            <p class="text-muted">Generating AI insights...</p>
        </div>
        <div id="fileHistoryContainer" style="margin-top:20px"></div>
    `;
    openModal('metaModal');

    await loadFileInsights(fileId);

    const historyResponse = await API.get(`/files/${fileId}/history`);
    const container = document.getElementById('fileHistoryContainer');
    if (!container) return;

    if (historyResponse.status !== 200) {
        container.innerHTML = '<p class="text-muted">Unable to load file history.</p>';
        return;
    }

    const history = historyResponse.data.history || [];
    if (history.length === 0) {
        container.innerHTML = '<p class="text-muted">No file history yet.</p>';
        return;
    }

    container.innerHTML = `
        <h4 style="margin-bottom:8px;">File History</h4>
        <table class="file-table" style="margin:0">
            <thead><tr><th>Timestamp</th><th>Action</th><th>Details</th></tr></thead>
            <tbody>
                ${history.map(item => `
                    <tr>
                        <td>${formatDate(item.timestamp)}</td>
                        <td><span class="badge badge-info">${escapeHtml(item.action)}</span></td>
                        <td>${escapeHtml(item.details || '-')}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function loadFileInsights(fileId, containerId = 'fileInsightsContainer') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '<p class="text-muted">Analyzing file with AI model...</p>';

    const { status, data } = await API.get(`/files/${fileId}/insights`);
    if (status !== 200) {
        container.innerHTML = `<p class="text-muted">${escapeHtml(data.error || 'Unable to generate insights.')}</p>`;
        return;
    }

    const insights = data.insights || {};
    const keywords = (insights.keywords || []).map(keyword => `<span class="insight-chip">${escapeHtml(keyword)}</span>`).join('');
    const tags = (insights.tags || []).map(tag => `<span class="badge badge-info">${escapeHtml(tag)}</span>`).join('');
    const actions = (insights.suggested_actions || []).map(action => `<li>${escapeHtml(action)}</li>`).join('');
    const fileLabel = insights.source === 'groq'
        ? 'AI Insights (Groq)'
        : insights.source === 'groq_unavailable'
        ? 'AI Insights (Unavailable)'
        : insights.source === 'legacy_presentation'
        ? 'Legacy PowerPoint text preview'
        : insights.source === 'presentation'
            ? 'Presentation outline preview'
            : 'AI summary';

    const sensitivity = String(insights.sensitivity || 'low').toLowerCase();
    const badgeClass = sensitivity === 'high'
        ? 'danger'
        : sensitivity === 'medium' || sensitivity === 'unknown'
            ? 'warning'
            : 'success';

    container.innerHTML = `
        <div class="feature-panel-header">
            <div>
                <h4>${fileLabel}</h4>
                <p class="text-muted">AI-generated summary and classification from extracted file content.</p>
            </div>
            <span class="badge badge-${badgeClass}">
                ${escapeHtml((insights.sensitivity || 'unknown').toUpperCase())} sensitivity
            </span>
        </div>
        ${insights.source === 'groq_unavailable' ? `<div class="alert alert-warning show" style="margin-bottom:12px;">${escapeHtml(insights.error || 'AI service is unavailable.')}</div>` : ''}
        <div class="text-muted" style="margin-bottom:10px;font-size:.82rem;">
            ${escapeHtml(insights.engine || 'ai analysis')}
        </div>
        <div class="insight-card insight-card-wide">
            <div class="insight-label">Summary (50-100 words)</div>
            <div class="insight-value">${escapeHtml(insights.summary || 'No readable summary was found.')}</div>
        </div>
        <div class="insight-grid insight-grid-compact">
            <div class="insight-card">
                <div class="insight-label">Metrics</div>
                <div class="insight-value">${escapeHtml(insights.metrics ? `${insights.metrics.words} words, ${insights.metrics.lines} lines, ${insights.metrics.characters} characters` : 'Unavailable')}</div>
            </div>
            <div class="insight-card">
                <div class="insight-label">Source</div>
                <div class="insight-value">${escapeHtml(insights.source || 'binary')}</div>
            </div>
        </div>
        <div class="mt-4">
            <div class="insight-label">Keywords</div>
            <div class="insight-tags">${keywords || '<span class="text-muted">No keywords detected.</span>'}</div>
        </div>
        <div class="mt-4">
            <div class="insight-label">Tags</div>
            <div class="insight-tags">${tags || '<span class="text-muted">No tags available.</span>'}</div>
        </div>
        <div class="mt-4">
            <div class="insight-label">Suggested actions</div>
            <ul class="insight-list">${actions || '<li>No suggested actions.</li>'}</ul>
        </div>
    `;
}

async function refreshFileInsightsFromMetadata() {
    const modal = document.getElementById('metaModal');
    const fileId = modal.dataset.fileId;
    if (!fileId) return;
    await loadFileInsights(fileId);
}

// ==================== Security / 2FA ====================
let setup2faSecret = null;

async function loadProfile() {
    const { status, data } = await API.get('/auth/me');
    if (status !== 200) {
        showAlert('alert-security', data?.error || 'Unable to load profile information.', 'danger');
        return;
    }

    const user = data.user;
    API.setUser(user);
    document.getElementById('sidebarUser').textContent = user.username;
    document.getElementById('profileUsername').textContent = user.username;
    document.getElementById('profileRole').textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);
    document.getElementById('profileCreated').textContent = formatDate(user.created_at);
    document.getElementById('profile2FA').textContent = user.two_factor_enabled ? 'Enabled' : 'Disabled';

    const badge = document.getElementById('twoFaBadge');
    if (user.two_factor_enabled) {
        badge.innerHTML = '<span class="badge badge-success">Enabled</span>';
        document.getElementById('twoFaDisabled').classList.add('hidden');
        document.getElementById('twoFaSetup').classList.add('hidden');
        document.getElementById('twoFaEnabled').classList.remove('hidden');
    } else {
        badge.innerHTML = '<span class="badge badge-warning">Disabled</span>';
        document.getElementById('twoFaDisabled').classList.remove('hidden');
        document.getElementById('twoFaSetup').classList.add('hidden');
        document.getElementById('twoFaEnabled').classList.add('hidden');
    }
}

async function setup2FA() {
    hideAlert('alert-security');
    const pinCode = document.getElementById('setupOtpCode').value.trim();
    const confirmPinCode = document.getElementById('confirmPinCode').value.trim();

    if (!/^\d{6}$/.test(pinCode)) {
        showAlert('alert-security', 'PIN must be exactly 6 digits.', 'danger');
        return;
    }
    if (!/^\d{6}$/.test(confirmPinCode)) {
        showAlert('alert-security', 'Confirm PIN must be exactly 6 digits.', 'danger');
        return;
    }
    if (pinCode !== confirmPinCode) {
        showAlert('alert-security', 'PIN and Confirm PIN must match.', 'danger');
        return;
    }

    const { status, data } = await API.post('/auth/setup-2fa', { pin_code: pinCode });
    if (status !== 200) {
        showAlert('alert-security', data.error || 'Failed to enable PIN lock.', 'danger');
        return;
    }

    document.getElementById('setupOtpCode').value = '';
    document.getElementById('confirmPinCode').value = '';
    showAlert('alert-security', 'PIN lock enabled successfully.', 'success');
    await loadProfile();
}

function cancel2FASetup() {
    setup2faSecret = null;
    document.getElementById('twoFaSetup').classList.add('hidden');
    document.getElementById('twoFaDisabled').classList.remove('hidden');
}

async function confirm2FA() {
    // No-op kept for backwards compatibility with older template versions.
    return;
}

async function disable2FA() {
    if (!confirm('Disable PIN lock for this account?')) return;
    hideAlert('alert-security');

    const { status, data } = await API.post('/auth/disable-2fa', {});
    if (status === 200) {
        showAlert('alert-security', 'PIN lock disabled.', 'success');
        loadProfile();
    } else {
        showAlert('alert-security', data.error || 'Failed to disable PIN lock.', 'danger');
    }
}

// ==================== Audit Log ====================
async function loadAuditLog() {
    const { status, data } = await API.get('/auth/audit-log');
    if (status !== 200) {
        const table = document.getElementById('auditTable');
        const empty = document.getElementById('emptyAuditTrail');
        const tbody = document.getElementById('auditTableBody');
        table.classList.add('hidden');
        empty.classList.remove('hidden');
        tbody.innerHTML = '';
        return;
    }

    const table = document.getElementById('auditTable');
    const empty = document.getElementById('emptyAuditTrail');
    const tbody = document.getElementById('auditTableBody');
    const logs = data.logs || [];

    if (logs.length === 0) {
        table.classList.add('hidden');
        empty.classList.remove('hidden');
        tbody.innerHTML = '';
        return;
    }

    table.classList.remove('hidden');
    empty.classList.add('hidden');
    tbody.innerHTML = logs.map(log => `
        <tr class="audit-row">
            <td>${formatDate(log.timestamp)}</td>
            <td>${renderAuditAction(log.action)}</td>
            <td>${escapeHtml(log.resource || '-')}</td>
            <td>${escapeHtml(log.details || '-')}</td>
            <td>${escapeHtml(log.ip_address || '-')}</td>
        </tr>
    `).join('');
}

function renderAuditAction(action) {
    const normalized = String(action || '').toUpperCase();
    const label = escapeHtml(action || 'UNKNOWN');

    if (normalized.includes('DENIED') || normalized.includes('THREAT')) {
        return `<span class="badge badge-danger">⛔ ${label}</span>`;
    }
    if (normalized.includes('DELETE') || normalized.includes('REVOKE')) {
        return `<span class="badge badge-warning">⚠ ${label}</span>`;
    }
    if (normalized.includes('SHARE') || normalized.includes('UPLOAD') || normalized.includes('LOGIN')) {
        return `<span class="badge badge-success">✓ ${label}</span>`;
    }
    return `<span class="badge badge-info">ℹ ${label}</span>`;
}

// ==================== Modal Helpers ====================
function openModal(id) {
    document.getElementById(id).classList.add('show');
}

function closeModal(id) {
    if (id === 'previewModal') {
        const previewRoot = document.getElementById('previewContent');
        if (previewRoot) {
            const objectUrl = previewRoot.dataset.objectUrl;
            if (objectUrl) URL.revokeObjectURL(objectUrl);
            previewRoot.dataset.objectUrl = '';
            previewRoot.innerHTML = '';
        }
    }
    document.getElementById(id).classList.remove('show');
}

// Close modal on backdrop click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeModal(overlay.id);
        }
    });
});

// ==================== Logout ====================
function logout() {
    API.clearToken();
    goToPage('login');
}

// ==================== Theme Management ====================
function initializeTheme() {
    // Load saved theme preference or detect system preference
    const savedTheme = localStorage.getItem('app-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    applyTheme(theme);
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

function applyTheme(theme) {
    const html = document.documentElement;
    html.setAttribute('data-theme', theme);
    localStorage.setItem('app-theme', theme);
    
    // Update button UI
    const themeIcon = document.getElementById('themeIcon');
    const themeLabel = document.getElementById('themeLabel');
    
    if (theme === 'light') {
        themeIcon.textContent = '☀️';
        themeLabel.textContent = 'Light';
    } else {
        themeIcon.textContent = '🌙';
        themeLabel.textContent = 'Dark';
    }
}

// ==================== XSS Prevention ====================
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(text)));
    return div.innerHTML;
}

function escapeAttr(text) {
    return escapeHtml(text).replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

// ==================== AI BOT FUNCTIONS ====================
let botWidgetMinimized = false;
let botProjectContext = null;
let botRequestCache = {};  // Cache bot responses
let botLastRequestTime = 0;  // Throttle requests
const BOT_REQUEST_THROTTLE_MS = 500;  // Min time between requests
const BOT_CACHE_TTL_MS = 300000;  // Cache responses for 5 minutes

function initializeBotWidget() {
    window.currentDashboardPage = 'files';
    const launcher = document.getElementById('botLauncher');
    const bot = document.getElementById('floatingBot');
    if (!launcher || !bot) return;

    launcher.style.display = 'flex';
    bot.style.display = 'none';
    // DO NOT auto-load context or capabilities - only on user action
}

async function preloadBotContext() {
    const { status, data } = await API.get('/files/bot/context');
    if (status === 200 && data?.context) {
        botProjectContext = data.context;
    }
}

async function loadBotCapabilities() {
    const quickActions = document.getElementById('botQuickActions');
    if (!quickActions) return;

    const { status, data } = await API.get('/files/bot/capabilities');
    if (status !== 200 || !Array.isArray(data?.quick_prompts)) return;

    quickActions.innerHTML = data.quick_prompts.slice(0, 4).map(prompt => (
        `<button class="bot-chip" onclick="sendQuickBotPrompt('${escapeAttr(prompt)}')">${escapeHtml(prompt)}</button>`
    )).join('');
}

function openBotWidget() {
    const launcher = document.getElementById('botLauncher');
    const bot = document.getElementById('floatingBot');
    if (!launcher || !bot) return;

    launcher.style.display = 'none';
    bot.style.display = 'block';
    botWidgetMinimized = false;

    const content = document.getElementById('botContent');
    const collapsed = document.getElementById('botCollapsed');
    if (content) content.style.display = 'flex';
    if (collapsed) collapsed.style.display = 'none';

    // Load capabilities only once when user opens bot
    if (!window.botCapabilitiesLoaded) {
        loadBotCapabilities();
        window.botCapabilitiesLoaded = true;
    }

    const input = document.getElementById('botInput');
    if (input) input.focus();
}

function toggleBotWidget() {
    botWidgetMinimized = !botWidgetMinimized;
    document.getElementById('botContent').style.display = botWidgetMinimized ? 'none' : 'flex';
    document.getElementById('botCollapsed').style.display = botWidgetMinimized ? 'block' : 'none';
}

function closeBotWidget() {
    minimizeBotToLauncher();
}

function minimizeBotToLauncher() {
    const launcher = document.getElementById('botLauncher');
    const bot = document.getElementById('floatingBot');
    if (!launcher || !bot) return;
    bot.style.display = 'none';
    launcher.style.display = 'flex';
}

function sendQuickBotPrompt(text) {
    const input = document.getElementById('botInput');
    if (!input) return;
    input.value = text;
    sendBotMessage();
}

function _appendBotActions(container, actions) {
    if (!container || !Array.isArray(actions) || !actions.length) return;

    const actionsWrap = document.createElement('div');
    actionsWrap.className = 'bot-response-actions';

    actions.forEach(action => {
        const btn = document.createElement('button');
        btn.className = 'bot-action-btn';
        btn.textContent = action.label || 'Run';
        btn.addEventListener('click', () => executeBotAction(action.id, action.payload || {}));
        actionsWrap.appendChild(btn);
    });

    container.appendChild(actionsWrap);
}

function executeBotAction(actionId, payload = {}) {
    switch (actionId) {
        // FILE UPLOAD
        case 'open_upload_modal':
            openUploadModal();
            break;

        // NAVIGATION
        case 'switch_page':
            if (payload.page) switchPage(payload.page);
            break;

        // SHARING ACTIONS
        case 'open_share_for_selected': {
            const selected = _selectedFeatureFile();
            if (selected?.id) {
                openShareModal(selected.id);
            } else {
                alert('Select a file first from the AI Insights selector.');
            }
            break;
        }

        // PREVIEW ACTION
        case 'open_preview_for_selected': {
            const selected = _selectedFeatureFile();
            if (selected?.id) {
                openFilePreview(selected.id, selected.filename, selected.file_type || '');
            } else {
                alert('Select a file first from the AI Insights selector.');
            }
            break;
        }

        // AI INSIGHTS
        case 'run_ai_insights_selected':
            runVisibleAiInsights();
            break;

        // REFRESH
        case 'refresh_files':
            loadFiles();
            break;

        // TIPS
        case 'show_bot_tips':
            showBotTips();
            break;

        // THREAT DETECTION - Navigate to security settings
        case 'run_threat_detection':
            switchPage('security');
            appendBotActionFeedback('Navigated to Security Settings. Threat detection module is active.');
            break;

        // ENCRYPTION - List encrypted files by filtering current files
        case 'list_encrypted_files':
            _botListEncryptedFiles();
            break;

        // BULK ARCHIVE - Filter old files for archiving
        case 'bulk_archive_action':
            _botBulkArchiveUI();
            break;

        // GENERATE SECURITY REPORT - Fetch and display audit data
        case 'generate_security_report':
            _botGenerateSecurityReport();
            break;

        // VIEW SHARED ACCESS - Navigate to shared by me
        case 'list_shared_files':
            switchPage('shared-by-me');
            appendBotActionFeedback('Showing files you\'ve shared with others.');
            break;

        // NEW ACTIONS: FILTERING & SEARCH
        case 'filter_shared_files':
            switchPage('shared');
            appendBotActionFeedback('Showing files shared with you.');
            break;

        case 'filter_encrypted':
            _botFilterEncrypted();
            break;

        case 'filter_by_type':
            appendBotActionFeedback('Use the file type selector in the left panel to filter files.');
            break;

        case 'filter_by_date':
            appendBotActionFeedback('Files are sorted by recent first. Older files can be archived.');
            break;

        case 'open_search':
            appendBotActionFeedback('Use Ctrl+F to search files by name.');
            break;

        // NEW ACTIONS: MANAGEMENT
        case 'manage_access':
            switchPage('security');
            appendBotActionFeedback('Open Security Settings to manage access control and permissions.');
            break;

        case 'bulk_download':
            appendBotActionFeedback('Select multiple files with checkboxes, then choose "Download All".');
            break;

        case 'export_metadata':
            appendBotActionFeedback('File metadata can be viewed in the details panel for each file.');
            break;

        // NEW ACTIONS: INSIGHTS & STATS
        case 'show_file_stats':
            _botShowFileStats();
            break;

        case 'bulk_analyze_files':
            appendBotActionFeedback('Select files to analyze. AI Insights will process multiple files.');
            break;

        case 'view_access_timeline':
            switchPage('audit');
            appendBotActionFeedback('Activity timeline shows all file access and sharing events.');
            break;

        case 'list_open_files':
            _botListOpenFiles();
            break;

        // NEW ACTIONS: HELP & EDUCATION
        case 'show_faq':
            appendBotActionFeedback('FAQ: Common questions covered in bot tips and help section.');
            break;

        default:
            break;
    }
}

// BOT ACTION HELPER: List encrypted files
function _botListEncryptedFiles() {
    const allFiles = window.fileList || [];
    const encrypted = allFiles.filter(f => f.is_encrypted);
    
    if (encrypted.length === 0) {
        appendBotActionFeedback('No encrypted files found.');
        return;
    }
    
    const list = encrypted.map(f => `• ${f.filename} (${(f.size / 1024).toFixed(1)}KB)`).join('\n');
    appendBotActionFeedback(`Found ${encrypted.length} encrypted files:\n${list}`);
}

// BOT ACTION HELPER: Bulk archive UI
function _botBulkArchiveUI() {
    const allFiles = window.fileList || [];
    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    
    const oldFiles = allFiles.filter(f => {
        const uploadDate = new Date(f.upload_date);
        return uploadDate < thirtyDaysAgo;
    });
    
    if (oldFiles.length === 0) {
        appendBotActionFeedback('No files older than 30 days to archive.');
        return;
    }
    
    const list = oldFiles.slice(0, 5).map(f => `• ${f.filename}`).join('\n');
    const msg = `Found ${oldFiles.length} files older than 30 days:\n${list}${oldFiles.length > 5 ? '\n... and ' + (oldFiles.length - 5) + ' more' : ''}`;
    appendBotActionFeedback(msg + '\n\nUse file checkboxes to select and manage.');
}

// BOT ACTION HELPER: Generate security report
async function _botGenerateSecurityReport() {
    try {
        const { status, data } = await API.get('/auth/audit-log');
        if (status !== 200 || !data.logs) {
            appendBotActionFeedback('Unable to generate security report. Check Audit Log directly.');
            return;
        }
        
        const logs = data.logs || [];
        const actionCount = {};
        
        logs.forEach(log => {
            actionCount[log.action] = (actionCount[log.action] || 0) + 1;
        });
        
        let report = `SECURITY AUDIT REPORT\n`;
        report += `Total activities: ${logs.length}\n`;
        report += `Date range: Last ${Math.ceil(logs.length / 10)} actions\n\n`;
        report += `Activity Summary:\n`;
        
        Object.entries(actionCount).forEach(([action, count]) => {
            report += `• ${action}: ${count}\n`;
        });
        
        appendBotActionFeedback(report);
    } catch (err) {
        appendBotActionFeedback('Security report generation failed. Check Audit Log section.');
    }
}

// BOT ACTION HELPER: Append file selection UI
async function _appendBotFileSelection(parentDiv, userQuery) {
    try {
        const { status, data } = await API.get('/files/bot/user-files');
        if (status !== 200 || !data.files || data.files.length === 0) {
            appendBotActionFeedback('No files found. Try uploading a file first.');
            return;
        }

        const filesContainer = document.createElement('div');
        filesContainer.className = 'bot-file-selection';
        filesContainer.style.marginTop = '8px';
        
        const title = document.createElement('div');
        title.style.fontSize = '12px';
        title.style.fontWeight = 'bold';
        title.style.marginBottom = '8px';
        title.style.color = '#666';
        title.textContent = 'Which file would you like to work with?';
        filesContainer.appendChild(title);

        const filesList = document.createElement('div');
        filesList.className = 'bot-file-list';
        filesList.style.display = 'flex';
        filesList.style.flexDirection = 'column';
        filesList.style.gap = '6px';
        filesList.style.maxHeight = '200px';
        filesList.style.overflowY = 'auto';

        data.files.forEach(file => {
            const btn = document.createElement('button');
            btn.className = 'bot-file-option';
            btn.style.padding = '8px 12px';
            btn.style.textAlign = 'left';
            btn.style.border = '1px solid #ddd';
            btn.style.borderRadius = '6px';
            btn.style.backgroundColor = '#f9f9f9';
            btn.style.cursor = 'pointer';
            btn.style.fontSize = '13px';
            btn.style.transition = 'background-color 0.2s';
            
            const fileName = document.createElement('div');
            fileName.style.fontWeight = '500';
            fileName.style.marginBottom = '2px';
            fileName.textContent = file.filename;
            
            const fileInfo = document.createElement('div');
            fileInfo.style.fontSize = '11px';
            fileInfo.style.color = '#999';
            const sizeKB = (file.size / 1024).toFixed(1);
            fileInfo.textContent = `${sizeKB}KB • ${file.file_type || 'unknown'} ${file.is_encrypted ? '🔒 encrypted' : ''}`;
            
            btn.appendChild(fileName);
            btn.appendChild(fileInfo);
            
            btn.addEventListener('mouseover', () => {
                btn.style.backgroundColor = '#f0f0f0';
            });
            btn.addEventListener('mouseout', () => {
                btn.style.backgroundColor = '#f9f9f9';
            });
            
            btn.addEventListener('click', () => {
                _botProcessFileAction(file, userQuery);
            });
            
            filesList.appendChild(btn);
        });

        filesContainer.appendChild(filesList);
        parentDiv.appendChild(filesContainer);

    } catch (err) {
        console.error('Error loading files for bot:', err);
        appendBotActionFeedback('Unable to load files. Please try again.');
    }
}

// BOT ACTION HELPER: Process file action based on user query
async function _botProcessFileAction(file, userQuery) {
    const query = userQuery.toLowerCase();
    const messagesContainer = document.getElementById('botMessages');
    
    // Share action
    if (query.includes('share')) {
        openShareModal(file.id);
        appendBotActionFeedback(`✓ Opening share options for "${file.filename}". You can now share it with friends or colleagues!`);
        return;
    }

    // Preview action
    if (query.includes('preview') || query.includes('open') || query.includes('view')) {
        openFilePreview(file.id, file.filename, file.file_type);
        appendBotActionFeedback(`✓ Opening preview for "${file.filename}".`);
        return;
    }

    // Insights action
    if (query.includes('insight') || query.includes('analyze')) {
        appendBotActionFeedback(`Analyzing "${file.filename}"... This may take a moment.`);
        // Would integrate with actual insights API
        return;
    }

    // Archive action
    if (query.includes('archive')) {
        appendBotActionFeedback(`${file.filename} is ready to archive. You can archive files from the file management section.`);
        return;
    }

    // Default: Show what file was selected
    appendBotActionFeedback(`✓ Selected: "${file.filename}". What would you like to do with it?`);
}

// BOT ACTION HELPER: Append feedback message to bot widget
function appendBotActionFeedback(message) {
    const messagesContainer = document.getElementById('botMessages');
    if (!messagesContainer) return;
    
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'bot-message bot-response bot-type-info';
    feedbackDiv.textContent = message;
    messagesContainer.appendChild(feedbackDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// NEW BOT ACTION HELPERS

// Filter encrypted files locally
function _botFilterEncrypted() {
    const allFiles = window.fileList || [];
    const encrypted = allFiles.filter(f => f.is_encrypted);
    const count = encrypted.length;
    appendBotActionFeedback(`🔒 Found ${count} encrypted file(s). These are protected with AES encryption.`);
}

// Show file statistics
function _botShowFileStats() {
    const allFiles = window.fileList || [];
    const totalSize = allFiles.reduce((sum, f) => sum + (f.size || 0), 0);
    const encrypted = allFiles.filter(f => f.is_encrypted).length;
    const avgSize = allFiles.length > 0 ? (totalSize / allFiles.length / 1024).toFixed(1) : 0;
    
    const stats = `📊 File Statistics:\n` +
        `Total files: ${allFiles.length}\n` +
        `Total size: ${(totalSize / 1024 / 1024).toFixed(2)}MB\n` +
        `Encrypted: ${encrypted} files\n` +
        `Average size: ${avgSize}KB`;
    appendBotActionFeedback(stats);
}

// List recently opened files
function _botListOpenFiles() {
    const allFiles = window.fileList || [];
    if (allFiles.length === 0) {
        appendBotActionFeedback('No files uploaded yet. Start by uploading a file.');
        return;
    }
    
    const recent = allFiles.slice(0, 5);
    const list = recent.map(f => `• ${f.filename}`).join('\n');
    appendBotActionFeedback(`📂 Recent files:\n${list}`);
}

function botInputKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendBotMessage();
    }
}

async function sendBotMessage() {
    const input = document.getElementById('botInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Check throttle
    const now = Date.now();
    if (now - botLastRequestTime < BOT_REQUEST_THROTTLE_MS) {
        appendBotActionFeedback('Please wait a moment before sending another message.');
        return;
    }
    botLastRequestTime = now;
    
    // Add user message to chat
    const messagesContainer = document.getElementById('botMessages');
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'bot-message user-message';
    userMsgDiv.textContent = message;
    messagesContainer.appendChild(userMsgDiv);
    
    input.value = '';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Check cache
    const cacheKey = message.toLowerCase().trim();
    if (botRequestCache[cacheKey] && (Date.now() - botRequestCache[cacheKey].time < BOT_CACHE_TTL_MS)) {
        const cachedData = botRequestCache[cacheKey].data;
        _displayBotResponse(messagesContainer, cachedData, message);
        return;
    }
    
    // Get context data for the bot (minimize data)
    const selected = _selectedFeatureFile();
    const contextData = {
        current_file: selected?.filename || '',
        current_page: window.currentDashboardPage || 'files',
    };
    
    // Show loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'bot-message bot-response bot-loading';
    loadingDiv.textContent = '⏳ Thinking...';
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Send to bot API
    const { status, data } = await API.post('/files/bot/message', {
        message: message,
        context: contextData
    });
    
    // Remove loading indicator
    loadingDiv.remove();
    
    // Handle response
    if (status === 200 && data.success) {
        // Cache successful response
        botRequestCache[cacheKey] = { data: data, time: Date.now() };
        _displayBotResponse(messagesContainer, data, message);
    } else if (status === 429) {
        // Rate limit
        const retryAfter = data.retry_after || 10;
        const botMsgDiv = document.createElement('div');
        botMsgDiv.className = 'bot-message bot-response bot-error';
        botMsgDiv.textContent = `⏱️ Rate limited. Please wait ${retryAfter} seconds before sending another message.`;
        messagesContainer.appendChild(botMsgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else {
        // Error
        const botMsgDiv = document.createElement('div');
        botMsgDiv.className = 'bot-message bot-response bot-error';
        botMsgDiv.textContent = data?.message || 'Sorry, something went wrong. Please try again.';
        messagesContainer.appendChild(botMsgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Helper to display bot response
async function _displayBotResponse(container, data, userQuery = '') {
    const botMsgDiv = document.createElement('div');
    botMsgDiv.className = 'bot-message bot-response';
    
    if (data.success) {
        botMsgDiv.textContent = data.message;
        botMsgDiv.classList.add(`bot-type-${data.type}`);
        _appendBotActions(botMsgDiv, data.agent_actions || []);
        
        // Show file selection if needed for file operations
        if (data.needs_file_selection) {
            await _appendBotFileSelection(botMsgDiv, userQuery);
        }
    }
    
    container.appendChild(botMsgDiv);
    container.scrollTop = container.scrollHeight;
}

async function showBotTips() {
    const { status, data } = await API.get('/files/bot/tips');
    if (status !== 200) {
        alert('Unable to load tips');
        return;
    }
    
    const tipsContent = document.getElementById('botTipsContent');
    tipsContent.innerHTML = '<ul class="tips-list">' + 
        data.tips.map(tip => `<li>${escapeHtml(tip)}</li>`).join('') +
        '</ul>';
    
    openModal('botTipsModal');
}

async function showBotTopics() {
    const { status, data } = await API.get('/files/bot/topics');
    if (status !== 200) {
        alert('Unable to load help topics');
        return;
    }
    
    const topics = data.topics;
    let topicsHtml = '<div class="help-topics">';
    for (const [key, desc] of Object.entries(topics)) {
        topicsHtml += `<div class="help-topic"><strong>${key}</strong><p>${escapeHtml(desc)}</p></div>`;
    }
    topicsHtml += '</div>';
    
    const tipsContent = document.getElementById('botTipsContent');
    tipsContent.innerHTML = topicsHtml;
    
    openModal('botTipsModal');
}
