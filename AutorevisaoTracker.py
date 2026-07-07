"""AutorevisaoTracker — rastreia documentos consultados, pilares verificados e gera
a seção 'Autorevisão do Assistente' conforme PERSONALIDADE.md linha 502.

A cada arquivo modificado, o tracker gera automaticamente:
- Quais documentos foram consultados
- Quais pilares foram respeitados
- Quais critérios foram aplicados
- Quais regras foram seguidas
"""
import os
from typing import Set, List, Dict, Optional
from datetime import datetime


class AutorevisaoTracker:
    """Rastreia documentos consultados e pilares verificados durante uma sessão.
    
    Uso:
        at = AutorevisaoTracker()
        at.registrar_doc("PERSONALIDADE.md", "secoes 1-3")
        at.verificar_pilar(3, True, "nomes em PT-BR")
        at.aplicar_criterio(4, True, "prefixo [MCR-*] presente")
        print(at.gerar())  # → markdown formatado
    """
    
    # 7 Pilares (PERSONALIDADE.md linhas 36-46)
    PILARES = {
        1: "Jornada 100% no Cliente",
        2: "Escopo Máximo de Customização",
        3: "Idioma Oficial PT-BR",
        4: "Imersão Narrativa",
        5: "Experiência Moderna",
        6: "Rastreabilidade por Logs",
        7: "Progressão Orgânica e Modular",
    }
    
    # 15 Critérios (PERSONALIDADE.md linhas 204-222)
    CRITERIOS = {
        1: "Consistência com identidade do domínio",
        2: "Respeito à hierarquia pai-filho (getNivelEfetivo)",
        3: "Feedback narrativo presente (padrão limpo v3.3)",
        4: "Rastreabilidade (prefixos [MCR-*])",
        5: "Compatibilidade com os 7 Pilares Permanentes",
        6: "Habilidades de gatilho com campo categoria",
        7: "Passivas de vida/mana/velocidade com campo efeito vazio",
        8: "magicEffect coerente com o elemento",
        9: "conditionMagicEffect separado se aplica condição",
        10: "condicaoFocoMin alinhado à potência",
        11: "Distribuição equilibrada de categorias",
        12: "efeitoConfig em vez de efeito manual",
        13: "Cooldowns e prioridades equilibrados",
        14: "Sinergia usa sinergia_escalonada",
        15: "Encoding: UTF-8 no C++, toLatin1() antes do protocolo",
    }
    
    # 14 Regras (PERSONALIDADE.md linhas 489-502)
    REGRAS = [
        "Não invente problemas. Baseie conclusões exclusivamente no código.",
        "Sempre informe arquivo, classe e função envolvidos.",
        "Quando não houver certeza, marque como 'Hipótese'.",
        "Priorize estabilidade, desempenho e compatibilidade.",
        "Considere impacto sobre servidor, cliente, editor e Grimório.",
        "Proponha mudanças pequenas e incrementais (PRs independentes).",
        "Evite sugestões genéricas; prefira melhorias específicas.",
        "Considere interação entre C++, Lua, C#, banco de dados e protocolo.",
        "Respeite compatibilidade com versões existentes.",
        "Siga os Pilares Permanentes e regras de encoding.",
        "Inclua Autorevisão do Assistente ao modificar arquivos.",
    ]
    
    def __init__(self):
        self.docs_consultados: Dict[str, str] = {}  # path → detalhes
        self.pilares_verificados: Dict[int, tuple] = {}  # num → (ok, detalhe)
        self.criterios_aplicados: Dict[int, tuple] = {}  # num → (ok, detalhe)
        self.regras_seguidas: List[str] = []
        self.arquivos_modificados: List[str] = []
        self.hipoteses: List[str] = []
        self.observacoes: List[str] = []
    
    def registrar_doc(self, path: str, detalhes: str = ""):
        """Registra um documento consultado."""
        nome = os.path.basename(path) if os.path.exists(path) else path
        self.docs_consultados[path] = detalhes or nome
    
    def verificar_pilar(self, numero: int, ok: bool, detalhe: str = ""):
        """Registra verificação de um pilar."""
        self.pilares_verificados[numero] = (ok, detalhe)
    
    def aplicar_criterio(self, numero: int, ok: bool, detalhe: str = ""):
        """Registra aplicação de um critério de análise."""
        self.criterios_aplicados[numero] = (ok, detalhe)
    
    def marcar_hipotese(self, descricao: str):
        """Marca algo como hipótese (incerteza)."""
        self.hipoteses.append(descricao)
    
    def registrar_observacao(self, obs: str):
        """Registra observação adicional."""
        self.observacoes.append(obs)
    
    def registrar_modificacao(self, path: str):
        """Registra arquivo modificado."""
        if path not in self.arquivos_modificados:
            self.arquivos_modificados.append(path)
    
    def gerar(self) -> str:
        """Gera o bloco de autorevisão no formato PERSONALIDADE.md linha 502."""
        partes = ["", "---", "### Autorevisão do Assistente", ""]
        
        # Documentos consultados
        if self.docs_consultados:
            partes.append("**Documentos consultados:**")
            for path, detalhes in self.docs_consultados.items():
                partes.append(f"- {detalhes}")
            partes.append("")
        
        # Arquivos modificados
        if self.arquivos_modificados:
            partes.append("**Arquivos modificados:**")
            for path in self.arquivos_modificados:
                partes.append(f"- `{path}`")
            partes.append("")
        
        # Pilares verificados
        if self.pilares_verificados:
            partes.append("**Pilares verificados:**")
            for num in sorted(self.pilares_verificados):
                ok, detalhe = self.pilares_verificados[num]
                nome = self.PILARES.get(num, f"Pilar {num}")
                simbolo = "✅" if ok else "❌"
                partes.append(f"- {simbolo} Pilar {num} ({nome}): {detalhe}")
            partes.append("")
        
        # Critérios aplicados
        if self.criterios_aplicados:
            partes.append("**Critérios aplicados:**")
            for num in sorted(self.criterios_aplicados):
                ok, detalhe = self.criterios_aplicados[num]
                nome = self.CRITERIOS.get(num, f"Critério {num}")
                simbolo = "✅" if ok else "❌"
                partes.append(f"- {simbolo} Critério {num} ({nome}): {detalhe}")
            partes.append("")
        
        # Hipóteses
        if self.hipoteses:
            partes.append("**Hipóteses (sem certeza):**")
            for h in self.hipoteses:
                partes.append(f"- {h}")
            partes.append("")
        
        # Observações
        if self.observacoes:
            partes.append("**Observações:**")
            for obs in self.observacoes:
                partes.append(f"- {obs}")
            partes.append("")
        
        return '\n'.join(partes)
