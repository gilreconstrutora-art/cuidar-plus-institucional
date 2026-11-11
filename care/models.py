import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Institution(models.Model):
    name = models.CharField(max_length=180)
    cnpj = models.CharField(max_length=18, unique=True)
    active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)

class StaffProfile(models.Model):
    ROLE_CHOICES = [("ADMIN", "Administrador"), ("COORD", "Coordenação"), ("NURSE", "Enfermagem"), ("CAREGIVER", "Cuidador"), ("PHARMACY", "Farmácia"), ("FAMILY", "Família")]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    identifier = models.CharField(max_length=40)
    active = models.BooleanField(default=True)
    device_id = models.CharField(max_length=120, blank=True)

class Resident(models.Model):
    STATUS = [("ACTIVE", "Ativo"), ("INACTIVE", "Inativo"), ("HOSPITAL", "Hospitalizado")]
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    name = models.CharField(max_length=180)
    birth_date = models.DateField(null=True, blank=True)
    room = models.CharField(max_length=30, blank=True)
    bed = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="ACTIVE")
    care_notes = models.TextField(blank=True)
    photo_authorized = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

class CarePlan(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="plans")
    version = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    approved_by = models.ForeignKey(StaffProfile, null=True, blank=True, on_delete=models.PROTECT)
    approved_at = models.DateTimeField(null=True, blank=True)

class CareTask(models.Model):
    KIND = [("ADMIN", "Administrativa"), ("CARE", "Assistencial"), ("CLINICAL", "Clínica")]
    STATUS = [("PENDING", "Pendente"), ("DONE", "Concluída"), ("MISSED", "Não realizada"), ("REFUSED", "Recusada"), ("EXCEPTION", "Intercorrência")]
    plan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=180)
    kind = models.CharField(max_length=20, choices=KIND, default="CARE")
    scheduled_at = models.DateTimeField()
    instruction = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(StaffProfile, null=True, blank=True, on_delete=models.PROTECT)
    note = models.TextField(blank=True)

class ResidentSession(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="sessions")
    staff = models.ForeignKey(StaffProfile, on_delete=models.PROTECT)
    device_id = models.CharField(max_length=120)
    started_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    emergency = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["resident"], condition=models.Q(closed_at__isnull=True), name="one_open_session_per_resident")]

class Medication(models.Model):
    STATUS = [("ACTIVE", "Ativo"), ("SUSPENDED", "Suspenso"), ("ENDED", "Encerrado")]
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField(max_length=180)
    presentation = models.CharField(max_length=120)
    concentration = models.CharField(max_length=80, blank=True)
    dose = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=30)
    route = models.CharField(max_length=50)
    frequency = models.CharField(max_length=120)
    scheduled_times = models.JSONField(default=list)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    prescription_version = models.PositiveIntegerField(default=1)
    prescribed_by = models.ForeignKey(StaffProfile, on_delete=models.PROTECT, related_name="prescriptions")
    validated_by = models.ForeignKey(StaffProfile, null=True, blank=True, on_delete=models.PROTECT, related_name="validated_medications")
    status = models.CharField(max_length=20, choices=STATUS, default="ACTIVE")

class MedicationAdministration(models.Model):
    STATE = [("ADMINISTERED", "Administrado"), ("REFUSED", "Recusado"), ("NOT_ADMINISTERED", "Não administrado"), ("UNCONFIRMED", "Não confirmado")]
    operation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT, related_name="administrations")
    scheduled_at = models.DateTimeField()
    declared_at = models.DateTimeField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(StaffProfile, on_delete=models.PROTECT)
    state = models.CharField(max_length=20, choices=STATE)
    justification = models.TextField(blank=True)
    note = models.TextField(blank=True)
    is_estimated_time = models.BooleanField(default=False)

class StockMovement(models.Model):
    TYPE = [("IN", "Entrada"), ("ADMIN", "Administração"), ("LOSS", "Perda"), ("RETURN", "Devolução"), ("ADJUST", "Ajuste")]
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT, related_name="stock_movements")
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    movement_type = models.CharField(max_length=20, choices=TYPE)
    reason = models.TextField(blank=True)
    operation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(StaffProfile, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class Alert(models.Model):
    SEVERITY = [("INFO", "Informativo"), ("WARNING", "Atenção"), ("CRITICAL", "Crítico")]
    resident = models.ForeignKey(Resident, null=True, blank=True, on_delete=models.CASCADE)
    event = models.CharField(max_length=120)
    severity = models.CharField(max_length=20, choices=SEVERITY, default="WARNING")
    status = models.CharField(max_length=20, default="OPEN")
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_by = models.ForeignKey(StaffProfile, null=True, blank=True, on_delete=models.PROTECT)
    closed_at = models.DateTimeField(null=True, blank=True)

class AuditEvent(models.Model):
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    actor = models.ForeignKey(StaffProfile, null=True, blank=True, on_delete=models.PROTECT)
    operation = models.CharField(max_length=80)
    resident = models.ForeignKey(Resident, null=True, blank=True, on_delete=models.SET_NULL)
    device_id = models.CharField(max_length=120, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

class FamilyAccess(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="family_accesses")
    contact_name = models.CharField(max_length=180)
    access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    permissions = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class NotificationDelivery(models.Model):
    STATUS = [("PENDING", "Pendente"), ("SENT", "Enviada"), ("FAILED", "Falhou"), ("CANCELLED", "Cancelada")]
    channel = models.CharField(max_length=30, default="WEBHOOK")
    recipient = models.CharField(max_length=240)
    event = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
