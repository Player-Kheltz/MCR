# 2026-06-23 — Gerenciamento de processos em segundo plano

## Decisao
Sempre finalizar servidores e servicos apos testes. Processos esquecidos bloqueiam compilacao e consomem recursos.

## Motivo
Servidor rodando impediu compilacao (LNK1104 - exe bloqueado). Perdi varios minutos debugando.

## Alternativas rejeitadas
Nao documentar como regra

## Referencias
scripts/auto.py (server stop/start), docs/lessons/
