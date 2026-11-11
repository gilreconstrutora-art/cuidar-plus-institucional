import os
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from care.models import Institution, StaffProfile

class Command(BaseCommand):
    help = "Cria ou atualiza um gerente a partir de variáveis de ambiente, sem gravar senha no código."
    def handle(self, *args, **kwargs):
        username = os.getenv("BOOTSTRAP_USERNAME")
        password = os.getenv("BOOTSTRAP_PASSWORD")
        institution_name = os.getenv("BOOTSTRAP_INSTITUTION", "Instituição Cuidar+")
        cnpj = os.getenv("BOOTSTRAP_CNPJ", "00.000.000/0001-00")
        if not username or not password or len(password) < 12:
            raise CommandError("Defina BOOTSTRAP_USERNAME e BOOTSTRAP_PASSWORD com pelo menos 12 caracteres.")
        institution, _ = Institution.objects.get_or_create(cnpj=cnpj, defaults={"name": institution_name})
        user, created = User.objects.get_or_create(username=username, defaults={"is_staff": True, "is_active": True})
        user.is_staff = True; user.is_active = True; user.set_password(password); user.save()
        StaffProfile.objects.update_or_create(user=user, defaults={"institution": institution, "role": "ADMIN", "identifier": username, "active": True})
        self.stdout.write(self.style.SUCCESS(f"Gerente configurado: {username} (instituição: {institution.name})"))
