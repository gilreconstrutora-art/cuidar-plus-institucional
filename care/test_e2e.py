from django.contrib.auth.models import User
from django.test import TestCase
from .models import Institution, StaffProfile


class InstitutionalFlowE2ETests(TestCase):
    def setUp(self):
        institution = Institution.objects.create(name="ILPI E2E", cnpj="22.222.222/0001-22")
        user = User.objects.create_user("coord-e2e", password="senha-e2e-123456")
        StaffProfile.objects.create(user=user, institution=institution, role="COORD", identifier="E2E-01")

    def test_public_presentation_and_caregiver_pages_render(self):
        self.assertEqual(self.client.get("/apresentacao/").status_code, 200)
        caregiver = self.client.get("/caregiver/")
        self.assertRedirects(caregiver, "/login/?next=/caregiver/")
        self.client.post("/login/", {"username": "coord-e2e", "password": "senha-e2e-123456", "next": "/caregiver/"})
        self.assertContains(self.client.get("/caregiver/"), "Cuidados pendentes")

    def test_manager_login_reaches_premium_central(self):
        response = self.client.post("/login/", {"username": "coord-e2e", "password": "senha-e2e-123456"})
        self.assertRedirects(response, "/central/")
        dashboard = self.client.get("/central/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Central gerencial")
