# Implantação do Cuidar+

## Validação em um comando

No PowerShell, na raiz do projeto:

```powershell
.\scripts\deploy.ps1 -Mode Local
```

Esse comando instala dependências, aplica migrações, coleta arquivos estáticos, executa verificações e testes.

## Gerente inicial

Defina os valores somente no ambiente de implantação e execute:

```powershell
$env:BOOTSTRAP_USERNAME = "gerente"
$env:BOOTSTRAP_PASSWORD = "senha-com-12-ou-mais-caracteres"
& $py manage.py bootstrap_manager
```

Depois acesse `/login/` e, após autenticar, `/central/`.

## Produção segura

Defina `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` e `REDIS_URL` no ambiente do provedor. Não coloque esses valores no GitHub. O Compose exige os segredos de banco e da aplicação e persiste Redis com AOF.

O worker envia a outbox somente quando `NOTIFICATION_WEBHOOK_URL` estiver configurada; sem esse valor, os eventos ficam pendentes e são reprogramados, sem fingir que foram enviados.

## Backup

`manage.py backup_db caminho/arquivo` cria cópia SQLite local ou dump customizado PostgreSQL quando `pg_dump` estiver disponível. O arquivo deve ser armazenado fora do host e sua restauração deve ser testada em ambiente separado antes de qualquer uso real.

## Docker

```powershell
.\scripts\deploy.ps1 -Mode Docker
```

O Compose sobe web ASGI, PostgreSQL, Redis e worker Celery. O ambiente ainda precisa de domínio, HTTPS, segredos reais, política de backup e monitoramento.
