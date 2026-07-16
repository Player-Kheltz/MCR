# MCR — Projeto de Servidor Customizado

## O Projeto
MCR é um servidor Tibia customizado que substitui o sistema de vocacoes pelo
SPA (Sistema de Progressao do Aventureiro). Nao existem vocacoes tradicionais
(Knights, Paladins, Sorcerers, Druids). Todo personagem comeca como Aventureiro
(vocation=0) e evolui por dominios.

## Dominios (SPA)
Os dominios sao areas de conhecimento que o aventureiro desenvolve ao realizar acoes:
- Primarios: Combate (1), Magia (2), Oficios (3), Natureza (4)
- Secundarios: Laminas (10), Elementos (20)
- Especialidades: Espadas Leves (100), Fogo (23), Gelo (24), Terra (25), Energia (26)

A propagacao de afinidade segue o ratio 4:2:1.

## Tecnologias
- Canary: Servidor C++17/20, Lua 5.4, MySQL/MariaDB
- OTClient Redemption: Cliente C++17, OpenGL, OTUI
- MCR.Grimorio: Ferramenta de gestao C#/.NET 8 WPF
- LoginServer: Go, gRPC, HTTP

## Encoding
- Lua: ISO-8859-1 (Latin-1)
- C++: UTF-8 com /utf-8 no MSVC
- Protocolo: toLatin1() antes de msg.addString()
