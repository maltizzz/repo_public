import sys
sys.path.append('/Users/PJ/Desktop/git/repos/news_checker/korea/')
from api import Media
from celery import Celery
import time
from celery.schedules import crontab

'''
# 48 12 * * * /Users/PJ/Desktop/git/repos/news_checker/korea/ETL.py
1. crontab -e
2. Esc + :wq
3. crontab -l
4. pgrep cron to check if cron registered correctly

'''

agent = Media()
agent.ETL()

