# Prontidão comercial do Cuidar+

## Já demonstrável

- Página institucional em `/apresentacao/`.
- Central gerencial em `/`.
- Fluxo móvel demonstrativo em `/caregiver/`.
- API autenticada para residentes, tarefas, medicamentos, alertas e auditoria.
- Relatório-resumo em `/api/reports/summary/` para perfis autorizados.
- Área familiar somente leitura por token expirável.
- WebSocket ASGI e fila/outbox persistente preparados para Redis/Celery.
- Comandos de backup/restauração local e configuração PostgreSQL.
- Dados fictícios reproduzíveis com `manage.py seed_demo`.

## Condições para uso institucional real

1. Provisionar PostgreSQL, Redis, HTTPS e domínio em ambiente controlado.
2. Configurar adaptador de envio e monitoramento da fila de notificações.
3. Executar backup e restauração em infraestrutura-alvo.
4. Executar testes E2E em celulares institucionais, segurança e carga.
5. Validar protocolos de cuidado e medicamentos com responsáveis técnicos habilitados.
6. Definir contrato, suporte, retenção de dados, privacidade, treinamento e critérios de aceite.
7. Só então ativar dados reais e notificações para usuários.

O sistema está preparado para apresentação e piloto técnico controlado; não deve ser anunciado como produto clínico pronto sem essas validações.
