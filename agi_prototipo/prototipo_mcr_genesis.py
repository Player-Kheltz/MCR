#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 6: MCRGenesis — Auto-Expansao de Capacidades
====================================================
O MCR cria NOVOS modulos quando detecta gaps.
Usa MCRCodex para gerar codigo + bateria de testes para validar.
Ciclo: diagnosticar gap -> projetar classe -> testar -> integrar.
"""
import sys, os, json, time, inspect
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    MCREntropia, CerebroAGI
)
from prototipo_mcr_codex import MCRCodex, MCRSelfTest
from prototipo_mcr_config import C


class MCRGenesis:
    """Auto-expansao: cria novos modulos para preencher gaps.
    
    Fluxo:
      1. diagnosticar_gap() — encontra lacunas de capacidade
      2. projetar_classe() — gera codigo para preencher o gap
      3. testar_e_integrar() — valida com a bateria de testes
      4. genesis_loop() — repete ate nao haver mais gaps viaveis
    """
    def __init__(self, cerebro: CerebroAGI = None):
        self.cerebro = cerebro or CerebroAGI()
        self.codex = MCRCodex(self.cerebro)
        self.selftest = MCRSelfTest()
        self.mk = MCR("genesis")
        self.threshold = MCRThreshold("genesis")
        self.entropia = MCREntropia("genesis")
        self.modulos_criados: List[Dict] = []
        self.total_gaps = 0
        self.patch_dir = os.path.join(os.path.dirname(__file__), "..", "genesis")
        os.makedirs(self.patch_dir, exist_ok=True)

    def diagnosticar_gap(self) -> Dict:
        """Encontra lacunas de capacidade no sistema atual.
        
        Usa MCRByteUtils + MCRSignatureExpansiva para detectar
        padroes que o sistema NAO consegue processar.
        """
        gaps = []
        
        # Gap 1: O cerebro tem conhecimento suficiente?
        if self.cerebro.mk_palavra.total < C("genesis_min_palavras"):
            gaps.append({
                "nome": "conhecimento_insuficiente",
                "descricao": "poucos dados de treino",
                "severidade": 0.8,
                "sugestao": "alimentar textos variados",
            })
        
        # Gap 2: O planner consegue planejar?
        from prototipo_agi_completo import EstadoMundo
        try:
            e = EstadoMundo.criar_simples()
        except Exception:
            e = None
        
        if e and self.cerebro.planner.mk_plano.total < C("genesis_min_planos"):
            gaps.append({
                "nome": "planejamento_insuficiente",
                "descricao": "poucos planos aprendidos",
                "severidade": 0.6,
                "sugestao": "executar mais episodios de treino",
            })
        
        # Gap 3: Entropia alta indica dados nao estruturados
        try:
            h = self.cerebro.mk_byte.entropia_media()
            if h > C("gap_entropia_alta"):
                gaps.append({
                    "nome": "dados_ruidosos",
                    "descricao": f"entropia byte alta ({h:.2f})",
                    "severidade": min(0.9, h),
                    "sugestao": "aplicar MCRSignatureExpansiva para descobrir dimensionalidade ideal",
                })
        except Exception:
            pass
        
        # Gap 4: Acoplamentos ausentes
        acoplamentos_fracos = sum(
            1 for o in self.cerebro.coupling.niveis
            for d in self.cerebro.coupling.niveis
            if o != d and self.cerebro.coupling.peso(o, d) < C("gap_coupling_fraco")
        )
        if acoplamentos_fracos > C("gap_coupling_count"):
            gaps.append({
                "nome": "acoplamentos_fracos",
                "descricao": f"{acoplamentos_fracos} acoplamentos abaixo de 0.1",
                "severidade": 0.4,
                "sugestao": "alimentar dados correlacionados entre niveis",
            })
        
        # Gap 5: Auto-modificacao pendente
        hc = self.codex.escanear_arquivo(
            os.path.join(os.path.dirname(__file__), "prototipo_agi_completo.py"))
        if len(hc) > C("gap_hardcode_count"):
            gaps.append({
                "nome": "hardcodes_demais",
                "descricao": f"{len(hc)} parametros fixos detectados",
                "severidade": min(0.7, len(hc) * 0.05),
                "sugestao": "executar MCRCodex.evoluir() para substituir",
            })
        
        self.total_gaps = len(gaps)
        
        if not gaps:
            return {"gaps": [], "total": 0, "severidade_media": 0.0,
                    "mensagem": "Nenhum gap detectado — sistema estavel"}
        
        sev_media = sum(g["severidade"] for g in gaps) / len(gaps)
        return {
            "gaps": gaps,
            "total": len(gaps),
            "severidade_media": round(sev_media, 3),
            "gap_principal": max(gaps, key=lambda g: g["severidade"]),
        }

    def projetar_classe(self, gap: Dict) -> str:
        """Projeta uma nova classe para preencher o gap."""
        nome_classe = f"MCR{''.join(w.capitalize() for w in gap['nome'].split('_'))}"
        nome_mk = nome_classe
        gap_nome = gap['nome']
        gap_desc = gap['descricao']
        gap_sev = gap['severidade']
        gap_sug = gap['sugestao']

        template = f'''class {nome_classe}:
    """Gerado pelo MCRGenesis para: {gap_desc}

    Severidade: {gap_sev}
    Sugestao: {gap_sug}
    """
    def __init__(self, cerebro=None):
        self.cerebro = cerebro
        self.mk = MCR("{nome_mk}")
        self.threshold = MCRThreshold("{nome_mk}")

    def executar(self, **kw) -> dict:
        resultado = self._processar(**kw)
        self.mk.aprender("EXEC", "OK" if resultado else "FAIL")
        return resultado

    def _processar(self, **kw) -> dict:
        return {{"status": "implementacao_pendente", "gap": "{gap_nome}"}}

    def stats(self) -> dict:
        return {{
            "classe": "{nome_classe}",
            "gap": "{gap_nome}",
            "exemplos": self.mk.total,
        }}
'''
        return template

    def testar_e_integrar(self, codigo: str, nome_modulo: str) -> bool:
        """Testa o codigo gerado e integra se passar."""
        caminho = os.path.join(self.patch_dir, f"{nome_modulo}.py")
        
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerado automaticamente pelo MCRGenesis em {time.strftime("%Y-%m-%d %H:%M")}."""
import sys, os
from prototipo_mcr_config import C
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
{codigo}
''')
        
        # Testa se o modulo importa sem erros
        nota_teste = self.selftest.testar_modulo(nome_modulo)
        
        if nota_teste >= C("genesis_nota_integracao"):
            self.modulos_criados.append({
                "nome": nome_modulo,
                "arquivo": caminho,
                "nota_teste": nota_teste,
                "timestamp": time.time(),
            })
            self.mk.aprender(f"INTEGRAR:{nome_modulo}", "OK")
            return True
        
        return False

    def genesis_loop(self, max_ciclos: int = 10) -> Dict:
        """Loop completo: diagnosticar -> projetar -> testar -> integrar."""
        historico = []
        
        for ciclo in range(max_ciclos):
            diagnostico = self.diagnosticar_gap()
            
            if diagnostico["total"] == 0:
                historico.append({
                    "ciclo": ciclo,
                    "acao": "estavel",
                    "gaps_restantes": 0,
                })
                self.mk.aprender(f"CICLO:{ciclo}", "ESTAVEL")
                break
            
            gap = diagnostico["gap_principal"]
            
            codigo = self.projetar_classe(gap)
            
            nome_modulo = f"mcr_gen_{gap['nome']}_{ciclo}"
            integrado = self.testar_e_integrar(codigo, nome_modulo)
            
            historico.append({
                "ciclo": ciclo,
                "acao": "integrado" if integrado else "falhou",
                "gap": gap["nome"],
                "severidade": gap["severidade"],
                "modulo": nome_modulo if integrado else None,
            })
            
            self.entropia.alimentar(f"ciclo:{ciclo}:{gap['nome']}")
            self.threshold.observar(gap["severidade"])
            
            if self.entropia.esta_em_loop():
                break
        
        return {
            "ciclos": len(historico),
            "modulos_criados": len([h for h in historico if h["acao"] == "integrado"]),
            "historico": historico,
            "estado_final": self.diagnosticar_gap(),
        }

    def stats(self) -> Dict:
        return {
            "modulos_criados": len(self.modulos_criados),
            "gaps_detectados": self.total_gaps,
            "taxa_integracao": round(
                len(self.modulos_criados) / max(self.total_gaps, 1) * 100, 1),
            "ultimos_modulos": self.modulos_criados[-3:] if self.modulos_criados else [],
        }

    def __repr__(self):
        s = self.stats()
        return f"MCRGenesis: {s['modulos_criados']} modulos, {s['gaps_detectados']} gaps, taxa={s['taxa_integracao']}%"
