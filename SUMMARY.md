# MCR — Sumário

## Core
- `devia/kernel/MCR.py` — 7.072 linhas, 48 classes, stdlib puro
- Cadeias Markov em 8+ níveis (byte, palavra, token, decisão, threshold, assinatura, filosofia, qualidade)
- Acoplamento N-dimensional + superposição + auto-evolução

## Pipeline de Mundo (44 módulos em mcr/)
- Geração de código Lua Canary com validação dupla (sintaxe + semântica)
- Busca semântica em 4 ondas (Radar)
- Motor de criatividade "E se..." (Emergir)
- Orquestrador Markoviano com 5 estados
- Bridge API REST (:7778) para Grimório C# WPF
- WorldObserver: eventos do servidor → perturbações de entropia

## Generalização (Fase D)
- Zero APIs hardcoded (SanityValidator minera do C++ em runtime)
- Clusters de assinatura — descobre tipos sem rótulos humanos
- Cold Start — aprende qualquer servidor do zero em ~2s
- Shadow Learning — erros de execução viram penalidades Markov

## Serviços
- NPC Server: socket TCP :7777
- Bridge API: HTTP REST :7778
- Ollama: localhost:11434 (qwen2.5-coder:7b, mistral:7b)
