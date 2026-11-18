from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import AuditEvent, Alert, CareProcedure, CareTask, MedicationAdministration, Resident, ResidentSession, StockMovement

def generate_procedure_occurrences(procedure, horizon_days=14):
    if procedure.status != "PUBLISHED":
        return 0
    today = timezone.localdate()
    start = max(procedure.starts_on, today)
    end = today + timedelta(days=horizon_days)
    if procedure.ends_on:
        end = min(end, procedure.ends_on)
    created = 0
    current = start
    while current <= end:
        include = procedure.frequency == "DAILY"
        if procedure.frequency == "ONCE":
            include = current == procedure.starts_on
        elif procedure.frequency == "WEEKLY":
            include = current.weekday() == procedure.starts_on.weekday()
        elif procedure.frequency == "SELECTED_DAYS":
            include = current.weekday() in procedure.weekdays
        if include:
            for time_value in procedure.scheduled_times:
                try:
                    hour, minute = [int(part) for part in str(time_value).split(":", 1)]
                    scheduled = timezone.make_aware(datetime.combine(current, datetime.min.time().replace(hour=hour, minute=minute)), timezone.get_current_timezone())
                except (TypeError, ValueError):
                    continue
                _, was_created = CareTask.objects.get_or_create(procedure=procedure, scheduled_at=scheduled, defaults={"plan": procedure.plan, "name": procedure.name, "kind": "CARE", "instruction": procedure.instruction})
                created += int(was_created)
        current += timedelta(days=1)
        if procedure.frequency == "ONCE":
            break
    return created

def profile_for(user):
    try:
        profile = user.staffprofile
    except Exception as exc:
        raise ValidationError("Usuário sem vínculo institucional.") from exc
    if not profile.active or not profile.institution.active:
        raise ValidationError("Credencial inativa.")
    return profile

def audit(actor, operation, resident=None, before=None, after=None, device_id="", metadata=None):
    return AuditEvent.objects.create(institution=actor.institution, actor=actor, operation=operation, resident=resident, device_id=device_id, before=before, after=after, metadata=metadata or {})

@transaction.atomic
def open_resident_session(actor, resident, device_id, emergency=False):
    if resident.institution_id != actor.institution_id:
        raise ValidationError("Residente fora da instituição do usuário.")
    current = ResidentSession.objects.select_for_update().filter(resident=resident, closed_at__isnull=True).first()
    if current:
        if current.staff_id == actor.id and current.device_id == device_id:
            current.last_seen_at = timezone.now(); current.save(update_fields=["last_seen_at"]); return current
        if not emergency:
            raise ValidationError("Este residente já está em atendimento em outro dispositivo.")
        current.closed_at = timezone.now(); current.save(update_fields=["closed_at"])
        audit(actor, "SESSION_EMERGENCY_TRANSFER", resident, device_id=device_id, metadata={"previous_staff_id": current.staff_id})
    session = ResidentSession.objects.create(resident=resident, staff=actor, device_id=device_id, emergency=emergency)
    audit(actor, "SESSION_OPEN", resident, device_id=device_id, metadata={"emergency": emergency})
    return session

@transaction.atomic
def complete_task(actor, task, status, note=""):
    if task.plan.resident.institution_id != actor.institution_id:
        raise ValidationError("Atividade fora da instituição do usuário.")
    if task.status != "PENDING":
        raise ValidationError("Atividade já processada; use uma correção auditada.")
    if status != "DONE" and not note.strip():
        raise ValidationError("Informe a observação ou o motivo quando o cuidado não for concluído.")
    task.status = status; task.note = note; task.completed_by = actor; task.completed_at = timezone.now(); task.save()
    audit(actor, "TASK_COMPLETE", task.plan.resident, before={"status": "PENDING"}, after={"status": status, "note": note})
    return task

@transaction.atomic
def record_administration(actor, medication, payload):
    if medication.resident.institution_id != actor.institution_id:
        raise ValidationError("Medicamento fora da instituição do usuário.")
    if medication.status != "ACTIVE":
        raise ValidationError("A prescrição não está ativa.")
    operation_id = payload.get("operation_id")
    if operation_id:
        existing = MedicationAdministration.objects.filter(operation_id=operation_id).first()
        if existing: return existing, False
    scheduled_at = payload["scheduled_at"]
    state = payload["state"]
    late = timezone.now() > scheduled_at + timedelta(minutes=60)
    justification = payload.get("justification", "")
    if late and not justification.strip():
        raise ValidationError("Após 60 minutos, a justificativa é obrigatória.")
    fields = {"medication": medication, "scheduled_at": scheduled_at, "declared_at": payload.get("declared_at"), "recorded_by": actor, "state": state, "justification": justification, "note": payload.get("note", ""), "is_estimated_time": payload.get("is_estimated_time", False)}
    if operation_id:
        fields["operation_id"] = operation_id
    administration = MedicationAdministration.objects.create(**fields)
    if state == "ADMINISTERED":
        StockMovement.objects.create(medication=medication, quantity=-medication.dose, movement_type="ADMIN", reason="Administração registrada", operation_id=administration.operation_id, created_by=actor)
    if late or state in {"REFUSED", "UNCONFIRMED", "NOT_ADMINISTERED"}:
        Alert.objects.create(resident=medication.resident, event="MEDICATION_EXCEPTION", severity="CRITICAL" if late else "WARNING", details={"administration_id": administration.id, "state": state, "late": late})
    audit(actor, "MEDICATION_ADMINISTRATION", medication.resident, after={"administration_id": administration.id, "state": state, "late": late})
    return administration, True
