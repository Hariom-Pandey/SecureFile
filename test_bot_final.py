import sys,os,tempfile
sys.path.insert(0,r'D:\OperatingProject\project')
from config import Config
from io import BytesIO
td=tempfile.mkdtemp()
Config.DATABASE_PATH=os.path.join(td,'bot_test3.db')
Config.STORAGE_PATH=os.path.join(td,'storage')
from main import create_app
from app.protection.encryption import EncryptionService
EncryptionService.reset()
app=create_app(testing=True)
c=app.test_client()
r=c.post('/api/auth/register',json={'username':'bot_u3','password':'Test123!@#'})
l=c.post('/api/auth/login',json={'username':'bot_u3','password':'Test123!@#'})
t=l.get_json()['access_token']
print('ENDPOINT TESTS:')
print()
msg=c.post('/api/files/bot/message',headers={'Authorization':f'Bearer {t}'},json={'message':'How do I share files?','context':{}})
print('Message endpoint:')
print(f'Status: {msg.status_code}')
data=msg.get_json()
print(f'Success: {data.get("success")}')
print(f'Type: {data.get("type")}')
print(f'Response: {data.get("message")[:80]}...')
