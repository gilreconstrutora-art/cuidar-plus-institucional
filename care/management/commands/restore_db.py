import shutil
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = "Restaura um backup SQLite local. Em PostgreSQL, use pg_restore/psql com aprovação operacional."
    def add_arguments(self, parser):
        parser.add_argument("source")
    def handle(self, *args, **options):
        source = Path(options["source"]).resolve()
        if not source.exists():
            raise CommandError("Arquivo de backup não encontrado.")
        if connection.vendor != "sqlite":
            raise CommandError("Restauração PostgreSQL deve ser executada com pg_restore/psql e procedimento aprovado.")
        destination = Path(connection.settings_dict["NAME"]).resolve()
        shutil.copy2(source, destination)
        self.stdout.write(self.style.SUCCESS(f"Backup restaurado em {destination}"))
