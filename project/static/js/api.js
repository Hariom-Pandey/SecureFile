const BACKEND_ORIGIN = 'http://127.0.0.1:5000';

function isStaticPreviewHost() {
    const usingFileProtocol = window.location.protocol === 'file:';
    const looksLikeTemplateHtml = /\/templates\//.test(window.location.pathname) || /\.html$/i.test(window.location.pathname);
    const localHost = ['127.0.0.1', 'localhost'].includes(window.location.hostname);
    const usingLiveServer = localHost && window.location.port !== '5000' && looksLikeTemplateHtml;
    return usingFileProtocol || usingLiveServer;
}

function isOfflineMode() {
    return false;
}

function pageUrl(page) {
    if (isStaticPreviewHost()) {
        return `${BACKEND_ORIGIN}/${page}`;
    }
    return `/${page}`;
}

function goToPage(page) {
    window.location.href = pageUrl(page);
}

// ==================== API Helper ====================
const API = {
    baseUrl: isStaticPreviewHost() ? `${BACKEND_ORIGIN}/api` : '/api',
    requestTimeoutMs: 10000,

    getToken() {
        return localStorage.getItem('access_token');
    },

    setToken(token) {
        localStorage.setItem('access_token', token);
    },

    clearToken() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
    },

    getUser() {
        const storedUser = localStorage.getItem('user');
        if (!storedUser) return null;

        try {
            return JSON.parse(storedUser);
        } catch (_err) {
            localStorage.removeItem('user');
            return null;
        }
    },

    setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    },

    async request(path, options = {}) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.requestTimeoutMs);

            const headers = {
                'Content-Type': 'application/json',
                ...(options.headers || {}),
            };
            const token = this.getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const res = await fetch(this.baseUrl + path, {
                ...options,
                headers,
                signal: controller.signal,
            });
            clearTimeout(timeoutId);

            const contentType = res.headers.get('content-type') || '';
            let data = {};
            if (contentType.includes('application/json')) {
                data = await res.json();
            } else {
                data = { error: `Request failed with status ${res.status}.` };
            }

            if (res.status === 401 && !path.includes('/login') && !path.includes('/verify-2fa')) {
                this.clearToken();
                goToPage('login');
            }
            return { status: res.status, data };
        } catch (err) {
            const message = err && err.name === 'AbortError'
                ? 'Request timed out. Please check the server and try again.'
                : 'Unable to reach the server. Ensure the backend is running.';
            return { status: 503, data: { error: message } };
        }
    },

    get(path)       { return this.request(path); },
    post(path, body){ return this.request(path, { method: 'POST', body: JSON.stringify(body) }); },
    put(path, body) { return this.request(path, { method: 'PUT', body: JSON.stringify(body) }); },
    del(path)       { return this.request(path, { method: 'DELETE' }); },

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        const token = this.getToken();

        try {
            const res = await fetch(this.baseUrl + '/files/upload', {
                method: 'POST',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {},
                body: formData,
            });
            return { status: res.status, data: await res.json() };
        } catch (_err) {
            return { status: 503, data: { error: 'Unable to upload file. Ensure the backend is running.' } };
        }
    }
};

// ==================== Utility ====================
function showAlert(id, message, type = 'danger') {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = `alert alert-${type} show`;
    el.textContent = message;
    if (type === 'success') setTimeout(() => el.classList.remove('show'), 4000);
}

function hideAlert(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('show');
}

function parseAppTimestamp(dateStr) {
    if (!dateStr) return null;

    if (dateStr instanceof Date) return dateStr;

    const raw = String(dateStr).trim();
    if (!raw) return null;

    // SQLite CURRENT_TIMESTAMP is UTC in "YYYY-MM-DD HH:MM:SS".
    // Convert to ISO UTC explicitly to avoid browser-local parsing ambiguity.
    const sqliteUtcPattern = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
    const normalized = sqliteUtcPattern.test(raw)
        ? raw.replace(' ', 'T') + 'Z'
        : raw;

    const parsed = new Date(normalized);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = parseAppTimestamp(dateStr);
    if (!d) return '-';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
         + ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function formatDateTimeWithSeconds(dateStr) {
    const d = parseAppTimestamp(dateStr);
    if (!d) return '-';

    return d.toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
    }) + ' ' + d.toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
}

function fileIcon(type) {
    const icons = {
        pdf: '📄', txt: '📝', png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️',
        doc: '📋', docx: '📋', xls: '📊', xlsx: '📊', csv: '📊',
        json: '📦', xml: '📦',
    };
    return icons[type] || '📁';
}
