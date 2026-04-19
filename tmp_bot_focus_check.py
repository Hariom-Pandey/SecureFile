import os
import sys
import tempfile

sys.path.insert(0, r'D:\OperatingProject\project')
from config import Config

workdir = tempfile.mkdtemp(prefix='bot_focus_')
Config.DATABASE_PATH = os.path.join(workdir, 'bot_focus.db')
Config.STORAGE_PATH = os.path.join(workdir, 'storage')
Config.ENCRYPTION_KEY_FILE = os.path.join(workdir, 'bot_focus.key')

from main import create_app
from app.protection.encryption import EncryptionService

EncryptionService.reset()
app = create_app(testing=True)
client = app.test_client()

username = 'bot_focus_user'
password = 'Test123!@#'
client.post('/api/auth/register', json={'username': username, 'password': password})
login = client.post('/api/auth/login', json={'username': username, 'password': password})
login_json = login.get_json() or {}
token = login_json.get('access_token')
headers = {'Authorization': f'Bearer {token}'} if token else {}

def pick_snippet(payload):
    if not isinstance(payload, dict):
        return ''
    for key in ('message', 'response', 'text', 'summary'):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value[:120]
    data = payload.get('data')
    if isinstance(data, dict):
        for key in ('message', 'response', 'text', 'summary'):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value[:120]
    return ''

def report(label, resp):
    body = resp.get_json(silent=True) or {}
    success = body.get('success')
    source = body.get('source')
    typ = body.get('type')
    snippet = pick_snippet(body)
    print(f"{label}: status={resp.status_code} success={success} source={source} type={typ} snippet={snippet}")

context_resp = client.get('/api/files/bot/context', headers=headers)
report('GET /api/files/bot/context', context_resp)

cap_resp = client.get('/api/files/bot/capabilities', headers=headers)
report('GET /api/files/bot/capabilities', cap_resp)

msg_resp = client.post('/api/files/bot/message', headers=headers, json={'message': 'Summarize my current dashboard status', 'context': {}})
report("POST /api/files/bot/message", msg_resp)
