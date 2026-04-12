import os
import sys
import django
from datetime import date

# Setup Django
sys.path.insert(0, r'C:\Users\Admin\Desktop\echonotes\echonotes')
os.environ['DJANGO_SETTINGS_MODULE'] = 'echonotes.settings'
django.setup()

from blog.models import DailyPrompt, WordOfTheDay

print('=== Daily Prompts ===')
total = DailyPrompt.objects.count()
print(f'Total in DB: {total}')
today_prompt = DailyPrompt.objects.filter(date=date.today())
print(f'Today ({date.today()}): {today_prompt.count()}')
latest = DailyPrompt.objects.order_by('-date').first()
if latest:
    print(f'Latest: {latest.date} - Active:{latest.is_active} - {latest.prompt[:80]}')
else:
    print('NO PROMPTS IN DB AT ALL')

print()
print('=== Word of the Day ===')
total_w = WordOfTheDay.objects.count()
print(f'Total in DB: {total_w}')
today_word = WordOfTheDay.objects.filter(date=date.today())
print(f'Today: {today_word.count()}')
latest_w = WordOfTheDay.objects.order_by('-date').first()
if latest_w:
    print(f'Latest: {latest_w.date} - {latest_w.word}')
else:
    print('NO WORDS IN DB AT ALL')
