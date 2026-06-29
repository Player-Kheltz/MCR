"""Personalidades do Conselho MCR - Modulares e escalaveis.
Cada personalidade e um arquivo独立 que exporta:
- nome: str
- papel: str (fixo/honorario/psicologo)
- especialidade: list[str] (topicos que domina)
- pensar(pergunta, contexto, kg) -> str
- memorizar(pergunta, opiniao) -> None
"""
