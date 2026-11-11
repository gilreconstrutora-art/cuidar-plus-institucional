import shutil
import sqlite3
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = "Cria backup do banco local; PostgreSQL exige pg_dump disponível no ambiente."
    def add_arguments(self, parser):
        parser.add_argument("destination")
    def handle(self, *args, **options):
        target = Path(options["destination"]).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if connection.vendor == "sqlite":
            name = str(connection.settings_dict["NAME"])
            if name.startswith("file:") or name == ":memory:":
                connection.ensure_connection()
                target.write_bytes(connection.connection.serialize())
            else:
                shutil.copy2(name, target)
            self.stdout.write(self.style.SUCCESS(f"Backup SQLite criado em {target}"))
            return
        raise CommandError("Para PostgreSQL, execute pg_dump com a URL de produção e armazene o arquivo em local protegido.")
