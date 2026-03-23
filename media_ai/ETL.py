import sys
from api import Media
from celery import Celery
import time
from celery.schedules import crontab


agent = Media()
agent.ETL()

