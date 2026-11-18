import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cuidar.settings")
app = Celery("cuidar")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "refresh-published-procedures": {"task": "care.tasks.generate_published_procedure_occurrences", "schedule": 3600.0},
    "process-notification-outbox": {"task": "care.tasks.process_notification_outbox", "schedule": 300.0},
}
