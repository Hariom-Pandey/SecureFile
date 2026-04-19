import sys,os,tempfile
sys.path.insert(0,r'D:\OperatingProject\project')
from config import Config

td=tempfile.mkdtemp()
Config.DATABASE_PATH=os.path.join(td,'bot_test.db')
Config.STORAGE_PATH=os.path.join(td,'storage')

from main import create_app
from app.protection.encryption import EncryptionService

EncryptionService.reset()
app=create_app(testing=True)
c=app.test_client()

# Register and login
r=c.post('/api/auth/register',json={'username':'bot_user','password':'Test123!@#'})
l=c.post('/api/auth/login',json={'username':'bot_user','password':'Test123!@#'})
t=l.get_json()['access_token']

# Test 1: Bot message
print('TEST 1: Bot message endpoint')
msg_response=c.post('/api/files/bot/message',headers={'Authorization':f'Bearer {t}'},json={'message':'How do I share files?','context':{'user_role':'user'}})
print(f'Status: {msg_response.status_code}')
resp_json=msg_response.get_json()
print(f'Full Response: {resp_json}')
print()

# Test 2: Bot tips
print('TEST 2: Bot tips endpoint')
tips_response=c.get('/api/files/bot/tips',headers={'Authorization':f'Bearer {t}'})
print(f'Status: {tips_response.status_code}')
tips_data=tips_response.get_json()
print(f'Tips count: {len(tips_data.get("tips", []))}')
if tips_data.get('tips'):
    print(f'Sample tips:')
    for i, tip in enumerate(tips_data.get('tips', [])[:3]):
        print(f'  {i+1}. {tip[:70]}...')
print()

# Test 3: Bot topics
print('TEST 3: Bot topics endpoint')
topics_response=c.get('/api/files/bot/topics',headers={'Authorization':f'Bearer {t}'})
print(f'Status: {topics_response.status_code}')
topics_data=topics_response.get_json()
topics_list = list(topics_data.get('topics', {}).keys())
print(f'Topics ({len(topics_list)}): {topics_list}')
