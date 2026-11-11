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

## Docker

```powershell
.\scripts\deploy.ps1 -Mode Docker
```

O Compose sobe web ASGI, PostgreSQL, Redis e worker Celery. O ambiente ainda precisa de domínio, HTTPS, segredos reais, política de backup e monitoramento.
