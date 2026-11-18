import json
import urllib.error
import urllib.request
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import CareProcedure, NotificationDelivery
from .services import generate_procedure_occurrences

@shared_task
def process_notification_outbox(limit=50):
    rows = list(NotificationDelivery.objects.filter(status="PENDING", next_attempt_at__lte=timezone.now()).order_by("created_at")[:limit])
    webhook = getattr(settings, "NOTIFICATION_WEBHOOK_URL", "").strip()
    sent = failed = deferred = 0
    for row in rows:
        row.attempts += 1
        if not webhook:
            row.last_error = "NOTIFICATION_WEBHOOK_URL não configurada."
            row.next_attempt_at = timezone.now() + timedelta(minutes=15)
            row.save(update_fields=["attempts", "last_error", "next_attempt_at"])
            deferred += 1
            continue
        request = urllib.request.Request(webhook, data=json.dumps({"event": row.event, "recipient": row.recipient, "payload": row.payload}).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status >= 300:
                    raise urllib.error.HTTPError(webhook, response.status, "webhook returned non-success", response.headers, None)
            row.status = "SENT"; row.sent_at = timezone.now(); row.last_error = ""
            row.save(update_fields=["attempts", "status", "sent_at", "last_error"])
            sent += 1
        except Exception as exc:
            row.last_error = str(exc)[:500]
            row.next_attempt_at = timezone.now() + timedelta(minutes=min(60, 2 ** min(row.attempts, 6)))
            if row.attempts >= 8:
                row.status = "FAILED"
            row.save(update_fields=["attempts", "last_error", "next_attempt_at", "status"])
            failed += 1
    return {"claimed": len(rows), "sent": sent, "failed": failed, "deferred": deferred}

@shared_task
def generate_published_procedure_occurrences():
    total = 0
    for procedure in CareProcedure.objects.filter(status="PUBLISHED").iterator():
        total += generate_procedure_occurrences(procedure)
    return {"created": total}
