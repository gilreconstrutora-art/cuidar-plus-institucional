from django.contrib import admin
from .models import Institution, StaffProfile, Resident, CarePlan, CareTask, Medication, MedicationAdministration, StockMovement, Alert, AuditEvent, ResidentSession, FamilyAccess, NotificationDelivery

for model in [Institution, StaffProfile, Resident, CarePlan, CareTask, Medication, MedicationAdministration, StockMovement, Alert, AuditEvent, ResidentSession, FamilyAccess, NotificationDelivery]:
    admin.site.register(model)
