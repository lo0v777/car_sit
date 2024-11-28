from flask import Flask
from celery import Celery

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://redis:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379'


celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])



from app import routes  
