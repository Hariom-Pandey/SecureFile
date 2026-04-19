import os
import sys
import tempfile

sys.path.insert(0, r'D:\OperatingProject\project')

from config import Config

workdir = tempfile.mkdtemp(prefix='bot_endpoint_test_')
Config.DATABASE_PATH = os.path.join(workdir, 'bot_test.db')
Config.STORAGE_PATH = os.path.join(workdir, 'storage')

from main import create_app
from app.protection.encryption import EncryptionService

EncryptionService.reset()
app = create_app(testing=True)
client = app.test_client()

username = 'bot_endpoint_user'
password = 'Test123!@#'

reg = client.post('/api/auth/register', json={'username': username, 'password': password})
print('Register:', reg.status_code)

login = client.post('/api/auth/login', json={'username': username, 'password': password})
print('Login:', login.status_code)
login_json = login.get_json() or {}
token = login_json.get('access_token')
print('Token present:', bool(token))

headers = {'Authorization': f'Bearer {token}'} if token else {}

normal = client.post('/api/files/bot/message', headers=headers, json={'message': 'How can I upload a file?', 'context': {}})
normal_json = normal.get_json() or {}
print('Normal message status:', normal.status_code)
print('Normal success:', normal_json.get('success'))
print('Normal type:', normal_json.get('type'))
print('Normal text:', (normal_json.get('message') or '')[:120])

fallback = client.post('/api/files/bot/message', headers=headers, json={'message': 'asdkjhasdkjh qweoiu zxcmn', 'context': {}})
fallback_json = fallback.get_json() or {}
print('Fallback message status:', fallback.status_code)
print('Fallback success:', fallback_json.get('success'))
print('Fallback type:', fallback_json.get('type'))
print('Fallback text:', (fallback_json.get('message') or '')[:120])
