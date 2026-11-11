from celery import shared_task
from django.utils import timezone
from .models import NotificationDelivery

@shared_task
def process_notification_outbox(limit=50):
    rows = list(NotificationDelivery.objects.filter(status="PENDING", next_attempt_at__lte=timezone.now()).order_by("created_at")[:limit])
    return {"claimed": len(rows), "provider": "external-adapter-required"}
