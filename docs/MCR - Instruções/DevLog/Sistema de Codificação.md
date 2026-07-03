>> CATALOG tags=encoding, utf-8, devlog updated=2026-06-23
# DevLog — Sistema de Codificação (Encoding)

## Contexto
O MCR sofreu por muito tempo com caracteres acentuados corrompidos (ex: "Não" aparecendo como "NÃ£o"). A causa raiz era um pipeline de encoding inconsistente entre servidor, protocolo e cliente.

## Pipeline Antigo (problema)
```
C++ com escapes octais (\343) → Latin-1
Lua salvo como ISO-8859-1 → Latin-1  
Protocolo → Latin-1
OTClient espera Latin-1 → exibe OK
```

**Problema:** Não dava para escrever "Você" diretamente. O C++ exigia `\352` para "ê", Lua exigia ISO-8859-1. Qualquer deslize corrompia o texto.

## Pipeline Novo (solução)
```
C++ UTF-8 literal (com /utf-8 no MSVC) → bytes UTF-8
Lua UTF-8 sem BOM → bytes UTF-8
toLatin1() converte UTF-8 → Latin-1 na saída do protocolo
Protocolo → Latin-1
OTClient → render OK
```

**Mudanças necessárias:**
- `/utf-8` já estava ativo nas 3 configurações do .vcxproj (Debug, Release, ReleaseDebug)
- `sendCancelMessage` já chamava `toLatin1()` — só não estava sendo chamado em `sendTextMessage`
- ProtocolGame::sendTextMessage: adicionado `toLatin1(message.text)` na linha 4796

## O que foi corrigido

| Local | O que mudou | Arquivo |
|---|---|---|
| `sendTextMessage` | Adicionado `toLatin1(message.text)` | `protocolgame.cpp:4796` |
| `player.cpp:7636` | "Não" literal → funcionou com `/utf-8` + `toLatin1()` | `player.cpp` |
| `items.cpp:276` | Removido `toLatin1(xmlContent)` — XML é UTF-8 real | `items.cpp` |
| `player.cpp:getDescription` | Escapes octais convertidos para UTF-8 literal | `player.cpp` |
| `mount_summon.lua` | Unicode escapes `\u{e3}` removidos, UTF-8 literal | `mount_summon.lua` |

## O que não precisa mais ser feito
- Escapes octais em C++ (opcionais)
- ISO-8859-1 em Lua (obsoleto)
- Conversão Latin-1→UTF-8 no OTClient (`mcr_name_fix.otmod` pode ser removido)

## Regras para o futuro
1. C++: escrever acentos diretamente ("Você", "Configuração")
2. Lua: salvar como UTF-8 sem BOM
3. XML: salvar como UTF-8 real (declaração `encoding="UTF-8"` + bytes UTF-8)
4. Toda string que sai pelo protocolo DEVE passar por `toLatin1()` antes de `msg.addString()`
