# EXPERIMENTAL — Use agent_loop como pipeline principal.
# Executor foi construido como orquestrador de estrategias paralelo
# ao agent_loop. A correcao de ~30 linhas no agent_loop
# (passar exemplos do Indexer para o NPCGenerator) torna
# este modulo redundante. Mantido como referencia.
"""Executor — Orquestrador de preenchimento de gaps.

Percorre todos os gaps detectados e aplica estrategias
em ordem de prioridade (qualidade). Se a melhor estrategia
falha, tenta a proxima. Se todas falham, pergunta ao humano.

Fluxo:
  1. Detectar gaps (GapDetector)
  2. Para cada gap (ordenado por prioridade):
     a. Tentar estrategias em ordem (indexer > items_xml > web > llm > humano)
     b. Aceitar o primeiro resultado com confianca > 0.5
     c. Validar resultado (se aplicavel)
  3. Retornar placeholders preenchidos
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import os, sys, json, time

# Path setup
_MCR_DEVIA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MCR_DEVIA not in sys.path:
    sys.path.insert(0, _MCR_DEVIA)

from engine.gap_detector import Gap, GapType, detectar_gaps
from strategies.base import (
    get_estrategias, get_estrategias_para_gap, StrategyResult, BaseStrategy
)


# ============================================================
# RESULTADO DO EXECUTOR
# ============================================================

@dataclass
class ExecutorResult:
    """Resultado completo da execucao."""
    sucesso: bool
    gaps_preenchidos: int = 0
    gaps_total: int = 0
    placeholders_preenchidos: Dict[str, Any] = field(default_factory=dict)
    log: List[Dict] = field(default_factory=list)
    tempo_total: float = 0.0
    erros: List[str] = field(default_factory=list)
    
    @property
    def cobertura(self) -> float:
        """Percentual de gaps preenchidos."""
        if self.gaps_total == 0:
            return 1.0
        return self.gaps_preenchidos / self.gaps_total


# ============================================================
# EXECUTOR
# ============================================================

class Executor:
    """Orquestrador que preenche gaps de criacao."""
    
    def __init__(self):
        self._estrategias = get_estrategias()
    
    def executar(self, tipo_npc: str, contexto: Optional[Dict] = None,
                 placeholders_iniciais: Optional[Dict] = None,
                 gaps_personalizados: Optional[List[Gap]] = None,
                 lim_estrategias: int = 3) -> ExecutorResult:
        """Executa o pipeline completo de preenchimento.
        
        Args:
            tipo_npc: Tipo do NPC (shop, quest, etc)
            contexto: Contexto adicional (profissao, local, etc)
            placeholders_iniciais: Placeholders fornecidos pelo usuario
            gaps_personalizados: Gaps fornecidos externamente
            lim_estrategias: Maximo de estrategias a tentar por gap (0 = todas)
        
        Returns:
            ExecutorResult com gaps preenchidos
        """
        inicio = time.time()
        contexto = contexto or {}
        contexto['tipo_npc'] = tipo_npc
        
        resultado = ExecutorResult(
            sucesso=True,
            placeholders_preenchidos=placeholders_iniciais or {},
        )
        
        # 1. Detectar gaps
        if gaps_personalizados:
            gaps = gaps_personalizados
        else:
            gaps = detectar_gaps(tipo_npc)
        
        resultado.gaps_total = len(gaps)
        
        if not gaps:
            resultado.tempo_total = time.time() - inicio
            return resultado
        
        # 2. Preencher cada gap
        estrategias_usaveis = self._estrategias[:lim_estrategias] if lim_estrategias > 0 else self._estrategias
        
        for gap in gaps:
            self._preencher_gap(gap, contexto, estrategias_usaveis, resultado)
        
        resultado.tempo_total = time.time() - inicio
        resultado.sucesso = resultado.cobertura >= 0.5
        
        return resultado
    
    def _preencher_gap(self, gap: Gap, contexto: Dict,
                        estrategias: List[BaseStrategy], resultado: ExecutorResult):
        """Tenta preencher um gap com as estrategias disponiveis."""
        entry = {
            'campo': gap.campo,
            'tipo': gap.tipo_lacuna.value,
            'tentativas': [],
            'sucesso': False,
        }
        
        # Estrategias que podem preencher este gap
        caps = get_estrategias_para_gap(gap)
        # Intercalar com as estrategias globais
        caps = caps or estrategias
        
        for estrategia in caps:
            try:
                resultado_estrategia = estrategia.preencher(gap, contexto)
                
                tentativa = {
                    'estrategia': estrategia.nome,
                    'sucesso': resultado_estrategia.sucesso,
                    'valor': str(resultado_estrategia.valor)[:80] if resultado_estrategia.valor else None,
                    'confianca': resultado_estrategia.confianca,
                    'detalhes': resultado_estrategia.detalhes[:150],
                }
                entry['tentativas'].append(tentativa)
                
                # Aceitar se confianca > 0.5
                if resultado_estrategia.sucesso and resultado_estrategia.confianca >= 0.5:
                    resultado.placeholders_preenchidos[gap.campo] = resultado_estrategia.valor
                    resultado.gaps_preenchidos += 1
                    entry['sucesso'] = True
                    entry['estrategia_vencedora'] = estrategia.nome
                    entry['valor_final'] = str(resultado_estrategia.valor)[:80]
                    break
            
            except Exception as e:
                entry['tentativas'].append({
                    'estrategia': estrategia.nome,
                    'sucesso': False,
                    'erro': str(e)[:100],
                })
        
        # Se nenhuma estrategia funcionou, manter valor atual
        if not entry['sucesso']:
            resultado.erros.append(
                f"Nao foi possivel preencher '{gap.campo}' ({gap.tipo_lacuna.value})"
            )
            if gap.valor_atual is not None:
                resultado.placeholders_preenchidos[gap.campo] = gap.valor_atual
        
        resultado.log.append(entry)
    
    def preencher_especifico(self, gap: Gap, contexto: Dict) -> Optional[StrategyResult]:
        """Preenche um gap especifico (para uso direto)."""
        caps = get_estrategias_para_gap(gap)
        
        for estrategia in caps:
            try:
                resultado = estrategia.preencher(gap, contexto)
                if resultado.sucesso and resultado.confianca >= 0.5:
                    return resultado
            except Exception:
                continue
        
        return None


# ============================================================
# FUNCAO UNICA DE ENTRADA
# ============================================================

def executar_pipeline(tipo_npc: str, contexto: Optional[Dict] = None,
                       placeholders: Optional[Dict] = None) -> ExecutorResult:
    """Executa o pipeline completo."""
    exec = Executor()
    return exec.executar(tipo_npc, contexto, placeholders)


# ============================================================
# TESTE
# ============================================================

if __name__ == '__main__':
    import json
    
    print("=== TESTE EXECUTOR ===\n")
    
    # Garantir que estrategias estao carregadas
    import strategies.local
    import strategies.items_xml
    import strategies.web
    import strategies.llm
    import strategies.human
    
    contexto = {
        'profissao': 'ferreiro',
        'local': 'Eridanus',
        'tipo_npc': 'shop',
    }
    
    resultado = executar_pipeline('shop', contexto)
    
    print(f"Sucesso: {resultado.sucesso}")
    print(f"Gaps: {resultado.gaps_preenchidos}/{resultado.gaps_total} "
          f"({resultado.cobertura*100:.0f}%)")
    print(f"Tempo: {resultado.tempo_total:.2f}s")
    print(f"Erros: {len(resultado.erros)}")
    
    print("\n--- Placeholders preenchidos ---")
    for campo, valor in resultado.placeholders_preenchidos.items():
        print(f"  {campo}: {str(valor)[:60]}")
    
    print("\n--- Log de preenchimento (primeiros 5) ---")
    for entry in resultado.log[:5]:
        v = entry.get('valor_final', '')
        e = entry.get('estrategia_vencedora', '')
        print(f"  {entry['campo']}: {v}")
        print(f"    Estrategia vencedora: {e}")
