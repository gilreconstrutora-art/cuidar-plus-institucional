import shutil
import sqlite3
import os
import subprocess
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
        if connection.vendor == "postgresql":
            pg_dump = shutil.which("pg_dump")
            if not pg_dump:
                raise CommandError("pg_dump não está instalado no ambiente de produção.")
            cfg = connection.settings_dict
            env = os.environ.copy()
            env["PGPASSWORD"] = str(cfg.get("PASSWORD") or "")
            command = [pg_dump, "--format=custom", "--file", str(target), "--host", str(cfg.get("HOST") or "localhost"), "--port", str(cfg.get("PORT") or 5432), "--username", str(cfg.get("USER") or ""), "--dbname", str(cfg.get("NAME") or "")]
            try:
                subprocess.run(command, check=True, env=env, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:
                raise CommandError("pg_dump falhou; consulte o log operacional do provedor sem expor credenciais.") from exc
            self.stdout.write(self.style.SUCCESS(f"Backup PostgreSQL criado em {target}"))
            return
        raise CommandError(f"Banco não suportado: {connection.vendor}")
