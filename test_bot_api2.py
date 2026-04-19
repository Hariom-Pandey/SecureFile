import sys, os, tempfile, traceback
sys.path.insert(0, r'D:\OperatingProject\project')
from config import Config

td = tempfile.mkdtemp()
Config.DATABASE_PATH = os.path.join(td, 'bot_test2.db')
Config.STORAGE_PATH = os.path.join(td, 'storage')

from main import create_app
from app.protection.encryption import EncryptionService

EncryptionService.reset()
app = create_app(testing=True)
c = app.test_client()

c.post('/api/auth/register', json={'username': 'bot_user2', 'password': 'Test123!@#'})
l = c.post('/api/auth/login', json={'username': 'bot_user2', 'password': 'Test123!@#'})
t = l.get_json()['access_token']

print('TEST: Bot message endpoint')
for query in ['How do I share files?', 'What about encryption?', 'Tell me about security']:
    print(f'Query: "{query}"')
    try:
        msg_response = c.post('/api/files/bot/message', headers={'Authorization': f'Bearer {t}'}, json={'message': query, 'context': {}})
        data = msg_response.get_json() or {}
        print(f'Status: {msg_response.status_code}')
        print(f'Success: {data.get("success")}')
        print(f'Type: {data.get("type")}')
        print(f'Response: {data.get("message")}')
    except Exception as e:
        print('Exception:', repr(e))
        print('Traceback tail:', traceback.format_exc().splitlines()[-1])
    print()
