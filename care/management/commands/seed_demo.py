from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from care.models import Institution, StaffProfile, Resident, CarePlan, CareTask, Medication

class Command(BaseCommand):
    help = "Cria dados fictícios mínimos para demonstração local, sem senha exibida ou gravada no código."
    def handle(self, *args, **kwargs):
        institution, _ = Institution.objects.get_or_create(cnpj="12.345.678/0001-90", defaults={"name": "Cuidar+ Demo"})
        user, created = User.objects.get_or_create(username="demo-cuidador", defaults={"first_name": "Cuidadora Demo"})
        if created:
            user.set_unusable_password(); user.save()
        staff, _ = StaffProfile.objects.get_or_create(user=user, defaults={"institution": institution, "role": "CAREGIVER", "identifier": "DEMO-01"})
        resident, _ = Resident.objects.get_or_create(institution=institution, name="Maria da Silva", defaults={"room": "1", "bed": "A"})
        plan, _ = CarePlan.objects.get_or_create(resident=resident, version=1)
        CareTask.objects.get_or_create(plan=plan, name="Hidratação", scheduled_at=timezone.now() + timedelta(hours=1), defaults={"instruction": "Oferecer água conforme plano autorizado."})
        Medication.objects.get_or_create(resident=resident, name="Medicamento demonstrativo", defaults={"presentation": "comprimido", "dose": 1, "unit": "un", "route": "oral", "frequency": "conforme prescrição", "scheduled_times": ["08:00"], "starts_on": timezone.localdate(), "prescribed_by": staff})
        self.stdout.write(self.style.SUCCESS("Dados demo criados. Usuário demo-cuidador está sem senha e não autentica até ser configurado localmente."))
