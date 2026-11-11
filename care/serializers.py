from rest_framework import serializers
from .models import Resident, CareTask, Medication, MedicationAdministration, Alert, AuditEvent, ResidentSession, FamilyAccess

class ResidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resident
        fields = ["id", "name", "birth_date", "room", "bed", "status", "care_notes", "photo_authorized", "updated_at"]

class CareTaskSerializer(serializers.ModelSerializer):
    resident_id = serializers.IntegerField(source="plan.resident_id", read_only=True)
    class Meta:
        model = CareTask
        fields = ["id", "resident_id", "name", "kind", "scheduled_at", "instruction", "status", "completed_at", "note"]

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ["id", "resident", "name", "presentation", "concentration", "dose", "unit", "route", "frequency", "scheduled_times", "starts_on", "ends_on", "prescription_version", "prescribed_by", "validated_by", "status"]

class AdministrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationAdministration
        fields = ["operation_id", "medication", "scheduled_at", "declared_at", "recorded_at", "recorded_by", "state", "justification", "note", "is_estimated_time"]
        read_only_fields = ["medication", "recorded_at", "recorded_by"]
        extra_kwargs = {"operation_id": {"read_only": False}}

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ["id", "resident", "event", "severity", "status", "details", "created_at", "acknowledged_by", "closed_at"]

class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = "__all__"

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentSession
        fields = ["token", "resident", "staff", "device_id", "started_at", "last_seen_at", "closed_at", "emergency"]
        read_only_fields = ["token", "resident", "staff", "started_at", "last_seen_at", "closed_at"]

class FamilyAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyAccess
        fields = ["contact_name", "access_token", "permissions", "active", "expires_at", "created_at"]
        read_only_fields = ["access_token", "created_at"]
