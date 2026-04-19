import sys,os,tempfile;sys.path.insert(0,r'D:\OperatingProject\project')
from config import Config
from io import BytesIO
from app.files.intelligence import FileIntelligenceService
from app.models.file_record import FileRecord

# Create a mock file record
record = FileRecord(
    original_name='test_document.txt',
    file_type='txt',
    owner_id=1,
    file_size=1500
)

# Sample document content
test_content = '''
Project Planning Meeting Notes - Q2 2026
Attendees: Project Manager, Team Lead, Developer
Agenda:
1. Review Q1 deliverables and identify blockers
2. Plan sprint schedule for April-June 2026
3. Resource allocation and team capacity planning
4. Risk assessment and mitigation strategies
5. Client communication timeline and milestones

Key Discussion Points:
- Dashboard redesign project on track, 75% complete
- Database optimization needed for performance improvement
- New API endpoints require security audit before deployment
- Team to attend training on new framework next month
- Expected go-live date: June 30, 2026
- Budget allocation approved for Q2 at ,000

Action Items:
- Security audit scheduled for May 15
- Team training: May 1-5
- Client presentation: May 20
- Final testing phase: June 1-20
'''

file_data = test_content.encode('utf-8')

# Build insights using Groq
insights = FileIntelligenceService.build_insights(record, file_data)

print('SUMMARY_ENGINE:', insights.get('engine'))
print('SUMMARY_LENGTH_WORDS:', FileIntelligenceService._word_count(insights['summary']))
print('SUMMARY_TEXT:', insights['summary'][:150] + '...' if len(insights['summary']) > 150 else insights['summary'])
print('KEYWORDS:', insights.get('keywords'))
print('TAGS:', insights.get('tags'))
print('SENSITIVITY:', insights.get('sensitivity'))
