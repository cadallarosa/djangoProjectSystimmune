import os
from celery import Celery
from celery.schedules import crontab
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

app = Celery('djangoProject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])


import plotly_integration.process_development.downstream_processing.akta.opcua_server.tasks

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Option 1: Run every 6 hours (midnight, 6am, noon, 6pm)
    'import-every-6-hours': {
        'task': 'plotly_integration.process_development.downstream_processing.akta.opcua_server.tasks.run_complete_import_pipeline',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours at minute 0
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not started
        }
    },

    # Option 2: Run at specific times (2am, 8am, 2pm, 8pm)
    # Uncomment this and comment out Option 1 if you prefer specific times
    # 'import-2am': {
    #     'task': 'plotly_integration.process_development.downstream_processing.akta.opcua_server.tasks.run_complete_import_pipeline',
    #     'schedule': crontab(hour=2, minute=0),
    # },
    # 'import-8am': {
    #     'task': 'plotly_integration.process_development.downstream_processing.akta.opcua_server.tasks.run_complete_import_pipeline',
    #     'schedule': crontab(hour=8, minute=0),
    # },
    # 'import-2pm': {
    #     'task': 'plotly_integration.process_development.downstream_processing.akta.opcua_server.tasks.run_complete_import_pipeline',
    #     'schedule': crontab(hour=14, minute=0),
    # },
    # 'import-8pm': {
    #     'task': 'plotly_integration.process_development.downstream_processing.akta.opcua_server.tasks.run_complete_import_pipeline',
    #     'schedule': crontab(hour=20, minute=0),
    # },

    # Check traversal status every hour (optional monitoring)
    'check-traversal-status': {
        'task': 'plotly_integration.process_development.downstream_processing.akta.opcua_server.tasks.check_traversal_status',
        'schedule': crontab(minute=30),  # Every hour at minute 30
    },
}

# Additional Celery Configuration
app.conf.update(
    # Timezone configuration (adjust to your timezone)
    timezone='America/Los_Angeles',
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result backend settings (if using)
    result_expires=3600,  # Results expire after 1 hour

    # Beat settings
    beat_schedule_filename='celerybeat-schedule',
)