#!/usr/bin/env python3
"""
carregar_sessao.py — Carrega e interpreta a sessao mais recente.
O prototipo AGI (ou qualquer modulo MCR) pode importar este modulo
para entender o que foi feito, quais gaps existem, e o que fazer a seguir.

Uso:
    from carregar_sessao import Sessao
    sessao = Sessao()
    print(sessao.gaps_urgentes())
    print(sessao.proximo_passo_recomendado())
"""
import os, json, sys

CAMINHO_PADRAO = os.path.join(os.path.dirname(__file__), "sessao_2026-07-02_completa.json")

class Sessao:
    """Carrega e interpreta o relatorio de sessao."""

    def __init__(self, caminho: str = None):
        self.caminho = caminho or CAMINHO_PADRAO
        self.dados = {}
        self._carregar()

    def _carregar(self):
        if not os.path.exists(self.caminho):
            print(f"[Sessao] Arquivo nao encontrado: {self.caminho}")
            return
        with open(self.caminho, "r", encoding="utf-8") as f:
            self.dados = json.load(f)
        print(f"[Sessao] Carregada: {self.dados.get('meta', {}).get('sessao', '?')}")
        print(f"[Sessao] {len(self.dados.get('acoes', []))} acoes registradas")

    @property
    def acoes(self) -> list:
        return self.dados.get("acoes", [])

    @property
    def gaps(self) -> dict:
        return self.dados.get("gaps_identificados", {})

    def gaps_urgentes(self) -> list:
        """Retorna gaps com prioridade 'urgente'."""
        todos = []
        for categoria, lista in self.gaps.items():
            for g in lista:
                if g.get("prioridade") == "urgente":
                    todos.append(g)
        return todos

    def gaps_por_categoria(self, categoria: str) -> list:
        return self.gaps.get(categoria, [])

    def proximo_passo_recomendado(self, n: int = 3) -> list:
        """Retorna os N proximos passos recomendados."""
        return self.dados.get("ordem_de_prioridade_recomendada", [])[:n]

    def provas_metaobserver(self) -> dict:
        return self.dados.get("provas_metaobserver", {})

    def licoes(self) -> list:
        return self.dados.get("licoes_aprendidas", [])

    def integracoes_pendentes(self) -> dict:
        return self.dados.get("integracoes_pendentes", {})

    def melhorias_mcr_chat(self) -> dict:
        return self.dados.get("mcr_chat_melhorias", {})

    def acoes_por_ator(self, ator: str) -> list:
        return [a for a in self.acoes if a.get("ator") == ator]

    def resumo_textual(self) -> str:
        """Gera resumo legivel para debugging."""
        meta = self.dados.get("meta", {})
        gaps_u = self.gaps_urgentes()
        prox = self.proximo_passo_recomendado(3)
        licoes = self.licoes()
        provas = self.provas_metaobserver()

        linhas = []
        linhas.append("=" * 55)
        linhas.append(f"  SESSAO: {meta.get('sessao', '?')}")
        linhas.append(f"  DATA: {meta.get('data', '?')}")
        linhas.append(f"  ACOES: {len(self.acoes)}")
        linhas.append("=" * 55)
        linhas.append("")

        linhas.append("[PROVAS METAOBSERVER]")
        for nome, dados in provas.items():
            if isinstance(dados, dict):
                status = dados.get("status", "?")
            else:
                status = str(dados)[:40]
            linhas.append(f"  {nome}: {status}")
        linhas.append("")

        linhas.append("[GAPS URGENTES]")
        for g in gaps_u:
            linhas.append(f"  {g['id']}: {g['descricao'][:70]}")
        linhas.append("")

        linhas.append("[PROXIMOS PASSOS]")
        for p in prox:
            linhas.append(f"  {p['ordem']}. {p['acao'][:70]}")
        linhas.append("")

        linhas.append("[LICOES]")
        for l in licoes[:3]:
            linhas.append(f"  - {l[:80]}")
        linhas.append("")

        return "\n".join(linhas)


# ─── AUTO-TESTE ────────────────────────────────────────────

if __name__ == "__main__":
    s = Sessao()
    print(s.resumo_textual())
    print()
    print("Gaps urgentes encontrados:")
    for g in s.gaps_urgentes():
        print(f"  {g['id']}: {g['descricao']} -> {g.get('solucao', '?')[:60]}")
    print()
    print("Proximo passo imediato:")
    prox = s.proximo_passo_recomendado(1)
    if prox:
        print(f"  {prox[0]['acao']}")
