# Cuidar+ Institucional

Núcleo inicial funcional do sistema de gestão inteligente do cuidado. A implementação atual usa Django + Django REST Framework, SQLite para desenvolvimento e uma interface web responsiva servida pelo próprio Django.

## Executar localmente

```powershell
$py = 'C:\Users\User\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m pip install -r requirements.txt
& $py manage.py migrate
& $py manage.py runserver
```

Abra `http://127.0.0.1:8000/`. A API de saúde está em `/api/health/`; os demais endpoints exigem autenticação.

Para apresentação comercial, abra `http://127.0.0.1:8000/apresentacao/`. O fluxo móvel demonstrativo está em `http://127.0.0.1:8000/caregiver/`.

Para acesso gerencial, use `/login/`; após autenticar, a central fica em `/central/`. A implantação reproduzível está documentada em [DEPLOYMENT.md](DEPLOYMENT.md) e no comando `scripts/deploy.ps1`.

## Núcleo implementado

- isolamento de dados por instituição;
- perfis institucionais e autenticação Django/DRF;
- residentes e página inicial da central;
- planos e tarefas de cuidado;
- sessão exclusiva por residente, com transferência emergencial auditada;
- prescrição versionada e administração de medicamento;
- trava administrativa de 60 minutos com justificativa obrigatória;
- separação entre horário previsto, declarado e registrado no servidor;
- alertas de recusa, não confirmação e atraso;
- movimentação transacional de estoque na administração válida;
- idempotência por `operation_id`;
- auditoria de eventos e preservação de sessões encerradas;
- testes automatizados dos fluxos críticos.
- WebSocket ASGI em `/ws/events/`, com Redis/Channels no Compose;
- outbox persistente de notificações e tarefa Celery preparada para adaptador externo;
- resumo familiar somente leitura com token e expiração;
- comandos de backup/restauração SQLite e configuração PostgreSQL.

## Limites atuais

Este é um núcleo executável para piloto controlado, não uma declaração de prontidão clínica irrestrita. Permanecem dependências externas: provisionamento real de PostgreSQL/Redis/HTTPS, adaptador de envio de notificações, política de backup fora do host, testes de restauração em infraestrutura-alvo, testes E2E em dispositivos reais e validação dos protocolos por profissionais habilitados.
