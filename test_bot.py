import sys,os,tempfile
sys.path.insert(0,r'D:\OperatingProject\project')
from config import Config
from app.files.bot_service import BotService

# Test 1: Bot message processing
print('TEST 1: Bot message processing')
response = BotService.process_message('How do I share files securely?', {'user_role': 'user'})
print('Success: ' + str(response.get('success')))
print('Type: ' + str(response.get('type')))
print('Message length: ' + str(len(response.get('message', ''))) + ' chars')
print()

# Test 2: Quick tips
print('TEST 2: Quick tips')
tips = BotService.get_quick_tips()
print('Number of tips: ' + str(len(tips)))
if tips:
    print('First tip: ' + tips[0][:50] + '...')
else:
    print('No tips')
print()

# Test 3: Help topics
print('TEST 3: Help topics')
topics = BotService.get_help_topics()
print('Topics available: ' + str(list(topics.keys())))
print()

# Test 4: Response classification
print('TEST 4: Response classification')
query = 'What is encryption?'
response_text = 'Encryption is the process of encoding data...'
response_type = BotService._classify_response(query, response_text)
print('Query: "' + query + '" -> Type: ' + str(response_type))
