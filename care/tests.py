from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.management import call_command
from tempfile import NamedTemporaryFile
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Institution, StaffProfile, Resident, CarePlan, CareTask, Medication, MedicationAdministration, Alert, AuditEvent, FamilyAccess

class CareCoreTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="ILPI Teste", cnpj="00.000.000/0001-00")
        user = User.objects.create_user("cuidadora", password="segura")
        self.staff = StaffProfile.objects.create(user=user, institution=self.institution, role="CAREGIVER", identifier="C-01")
        self.resident = Resident.objects.create(institution=self.institution, name="Maria Teste", room="1", bed="A")
        self.plan = CarePlan.objects.create(resident=self.resident)
        self.medication = Medication.objects.create(resident=self.resident, name="Medicamento teste", presentation="comprimido", dose=1, unit="un", route="oral", frequency="diária", scheduled_times=["08:00"], starts_on=timezone.localdate(), prescribed_by=self.staff)
        self.client = APIClient(); self.client.force_authenticate(user=user)

    def test_residents_are_scoped_to_institution(self):
        other = Institution.objects.create(name="Outra", cnpj="11.111.111/0001-11")
        Resident.objects.create(institution=other, name="Não aparece")
        response = self.client.get("/api/residents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["name"] for row in response.data], ["Maria Teste"])

    def test_resident_session_is_exclusive(self):
        first = self.client.post(f"/api/residents/{self.resident.pk}/session/", {"device_id": "cel-1"}, format="json")
        self.assertEqual(first.status_code, 201)
        second = self.client.post(f"/api/residents/{self.resident.pk}/session/", {"device_id": "cel-2"}, format="json")
        self.assertEqual(second.status_code, 400)
        emergency = self.client.post(f"/api/residents/{self.resident.pk}/session/", {"device_id": "cel-2", "emergency": True}, format="json")
        self.assertEqual(emergency.status_code, 201)
        self.assertEqual(AuditEvent.objects.filter(operation="SESSION_EMERGENCY_TRANSFER").count(), 1)

    def test_late_medication_requires_justification_and_is_idempotent(self):
        scheduled = timezone.now() - timedelta(minutes=61)
        body = {"scheduled_at": scheduled.isoformat(), "state": "ADMINISTERED"}
        rejected = self.client.post(f"/api/medications/{self.medication.pk}/administer/", body, format="json")
        self.assertEqual(rejected.status_code, 400)
        body["justification"] = "Registro realizado após o prazo administrativo."
        body["operation_id"] = "a2c1e3f0-1f3c-4d0c-ae8e-69fb74c1d111"
        accepted = self.client.post(f"/api/medications/{self.medication.pk}/administer/", body, format="json")
        repeated = self.client.post(f"/api/medications/{self.medication.pk}/administer/", body, format="json")
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(MedicationAdministration.objects.count(), 1)
        self.assertEqual(Alert.objects.count(), 1)

    def test_caregiver_cannot_change_resident_cadastre(self):
        response = self.client.post("/api/residents/", {"name": "Outro residente"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_manager_can_read_summary_report(self):
        self.staff.role = "COORD"; self.staff.save(update_fields=["role"])
        response = self.client.get("/api/reports/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["residents"]["active"], 1)

    def test_family_summary_is_read_only_and_token_scoped(self):
        access = FamilyAccess.objects.create(resident=self.resident, contact_name="Contato autorizado")
        response = APIClient().get(f"/api/family/{access.access_token}/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["resident"]["name"], "Maria Teste")
        self.assertEqual(APIClient().get("/api/family/00000000-0000-0000-0000-000000000000/summary/").status_code, 404)

    def test_sqlite_backup_command_creates_file(self):
        with NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            destination = tmp.name
        call_command("backup_db", destination)
        import os
        self.assertGreater(os.path.getsize(destination), 0)

    def test_manager_login_protects_central(self):
        manager_user = User.objects.create_user("manager", password="senha-segura-123")
        StaffProfile.objects.create(user=manager_user, institution=self.institution, role="COORD", identifier="M-01")
        client = APIClient()
        response = client.get("/central/")
        self.assertEqual(response.status_code, 302)
        login_response = client.post("/login/", {"username": "manager", "password": "senha-segura-123"})
        self.assertEqual(login_response.status_code, 302)
        self.assertTrue(login_response["Location"].endswith("/central/"))
