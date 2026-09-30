import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alitrans_project.settings')

app = Celery('alitrans_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()