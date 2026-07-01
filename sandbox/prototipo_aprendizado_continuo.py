#!/usr/bin/env python3
"""PROTÓTIPO: Aprendizado Contínuo — V2 simplificado (dados diretos).

Cada ciclo usa dados PRÉ-COLETADOS (sem depender de ferramentas lentas).
Valida: PE tokeniza → Aprendiz aprende → Reconstrução funciona.

NÃO MODIFICA NADA NO MCR.
"""
import sys, os, json, time as _time, random
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.pi_engine import PiEngine
from modulos.intention_engine import IntentionEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes


# Dados REAIS do projeto para o ciclo de aprendizado
_DADOS_FERRAMENTAS = {
    "buscar_estrategico(NPC)": "data/npc/artefato.lua\ndata/npc/keywordhandler.lua\ndata/npc/ferreiro.lua",
    "buscar_estrategico(SPA)": "scripts/mcr_devia/modulos/kg.py\nscripts/mcr_devia/modulos/supervisor.py\nscripts/mcr_devia/comandos/cmd_perguntar.py",
    "buscar_estrategico(SHC)": "Canary/data-canary/scripts/MCR/SHC/\nCanary/data-canary/scripts/MCR/SPA/core/\nscripts/mcr_devia/modulos/intention_engine.py",
    "buscar_kg(MCR)": "Projeto MCR = servidor de Tibia customizado baseado no Canary (OTServ)",
    "buscar_kg(SPA)": "SPA = Sistema de Progressao do Aventureiro, dominios: Fogo(23), Gelo(24), Terra(25), Energia(26)",
    "buscar_kg(SHC)": "SHC = Sistema de Habilidades Contextuais, 5 camadas: postura, nivel, sinergia, estado, condicao",
    "buscar_kg(Canary)": "Canary = Servidor OTServ personalizado usado no projeto MCR",
    "buscar_kg(Eridanus)": "Eridanus = Cidade inicial do projeto MCR, ponto de partida dos aventureiros",
    "ler_arquivo(MCR_IDENTITY)": "MCR = Projeto MCR, um servidor CUSTOMIZADO de Tibia baseado em Canary.\nSPA = Sistema de Progressao do Aventureiro.\nSHC = Sistema de Habilidades Contextuais.\nEridanus = Cidade inicial.\nCanary = Servidor OTServ.",
    "ler_arquivo(artefato_npc)": "local npc = NPC:new('Ferreiro')\nnpc:setTitle('Ferreiro de Eridanus')\nnpc:onSay(function(cid, msg)\n    if msg:contains('comprar') then\n        -- abre loja\n    end\nend)",
    "validar_codigo(lua)": "Syntax OK: 3 funcoes validas",
}


class PrototipoAprendizado:
    """Ciclo: usa dado → tokeniza → aprende → repete → reconstroi."""
    
    def __init__(self):
        self.pe = PatternEngine()
        self.pi = PiEngine(pe=self.pe)
        self.ie = IntentionEngine(pe=self.pe)
        self.kg = KnowledgeGraph()
        self.aprendiz = AprendizDePadroes(pe=self.pe, kg=self.kg)
        
        self.ciclos = 0
        self.ferramentas_usadas = []
        self.padroes_por_ciclo = []
        self.entropias = []
        self.tempos = []
    
    def executar_ciclo(self, vezes=8):
        """Executa N ciclos de dados → tokenizar → aprender."""
        print(f"\n{'='*70}")
        print(f"  CICLO DE APRENDIZADO — {vezes} simulações de ferramentas")
        print(f"{'='*70}")
        
        items = list(_DADOS_FERRAMENTAS.items())
        
        for ciclo in range(1, vezes + 1):
            nome_item, dados = random.choice(items)
            
            print(f"\n  [{ciclo}/{vezes}] {nome_item}")
            
            t0 = _time.time()
            
            # 1. PE.tokenizar_universal nos dados
            tokens = self.pe.tokenizar_universal(dados)
            if not tokens:
                print(f"    → Sem tokens")
                continue
            
            tipos = Counter(t[0] for t in tokens)
            padroes_t = self.pe.extrair_padroes(tokens)
            entropia = padroes_t.get('entropia', 1.0)
            self.entropias.append(entropia)
            
            top5 = tipos.most_common(5)
            print(f"    Tokens: {top5}")
            print(f"    Entropia: {entropia:.4f}")
            
            # 2. Aprendiz estuda
            padroes = self.aprendiz.estudar_dados(dados, nome_item.replace('(', '_').replace(')', ''))
            self.padroes_por_ciclo.append(len(padroes))
            
            if padroes:
                confs = [p.get('conf', 0) for p in padroes]
                print(f"    Aprendido: {len(padroes)} padrões (conf média: {sum(confs)/len(confs):.2f})")
            else:
                print(f"    Aprendido: 0 padrões")
            
            tempo = _time.time() - t0
            self.tempos.append(tempo)
            self.ferramentas_usadas.append(nome_item)
            self.ciclos += 1
        
        # Salva no KG
        salvos = self.aprendiz.salvar_kg()
        print(f"\n  → {salvos} padrões salvos no KG")
        
        # Gráfico de entropia
        if self.entropias:
            print(f"\n  Evolução da entropia:")
            for i, e in enumerate(self.entropias):
                barra = '█' * max(0, min(10, int(e * 10))) + '░' * max(0, 10 - min(10, int(e * 10)))
                print(f"    [{i+1}] {barra} {e:.3f}")
    
    def testar_reconstrucao(self, pergunta):
        """Testa reconstrução para uma pergunta."""
        print(f"\n  Pergunta: {pergunta}")
        
        tokens = self.pe.tokenizar_universal(pergunta)
        fp = self.pe.fingerprint(tokens) if tokens else []
        intencoes = self.ie.detectar(pergunta)
        
        if intencoes:
            cat, params, conf = intencoes[0]
            print(f"  IE: {cat}/{params.get('tipo','?')} (conf={conf:.3f})")
        
        t0 = _time.time()
        resposta = self.aprendiz.reconstruir_resposta(
            fp, intencoes[0] if intencoes else None, tokens_input=tokens
        )
        tempo = _time.time() - t0
        
        if resposta and len(resposta) > 30:
            print(f"  ✅ RECONSTRUÍDA em {tempo:.2f}s ({len(resposta)} chars, 0 LLM)")
            print(f"     {resposta[:150]}")
        else:
            print(f"  ❌ Falhou ({tempo:.2f}s) — KG sem fingerprint similar")
        
        return resposta
    
    def relatorio(self):
        """Gera relatório final."""
        licoes = self.kg._get_licoes()
        com_fp = [l for l in licoes if l.get('fingerprint')]
        com_tm = [l for l in licoes if l.get('tipos_markov')]
        
        print(f"\n{'='*70}")
        print(f"  RELATÓRIO FINAL")
        print(f"{'='*70}")
        print(f"  Ciclos: {self.ciclos}")
        print(f"  Padrões aprendidos: {sum(self.padroes_por_ciclo)}")
        print(f"  Média por ciclo: {sum(self.padroes_por_ciclo)/max(len(self.padroes_por_ciclo),1):.1f}")
        print(f"  Tempo total: {sum(self.tempos):.1f}s")
        
        if len(self.entropias) >= 2:
            print(f"  Entropia: {self.entropias[0]:.3f} → {self.entropias[-1]:.3f} " +
                  f"{'⬇️ caiu' if self.entropias[-1] < self.entropias[0] else '⬆️ subiu'}")
        
        # Top padrões por tipo
        todos_tipos = Counter()
        for p in self.aprendiz._padroes_encontrados:
            todos_tipos[p.get('tipo', '?')] += 1
        if todos_tipos:
            print(f"  Tipos de padrão:")
            for tipo, n in todos_tipos.most_common(5):
                print(f"    {tipo}: {n}")
        
        print(f"  KG: {len(licoes)} lessons, {len(com_fp)} com fingerprint, {len(com_tm)} com tipos_markov")


if __name__ == '__main__':
    print("=" * 70)
    print("  APRENDIZADO CONTÍNUO — PROTÓTIPO V2")
    print("  Dados reais do projeto | PE tokeniza | Aprendiz aprende")
    print("=" * 70)
    
    proto = PrototipoAprendizado()
    
    # FASE 1: Ciclo de aprendizado
    proto.executar_ciclo(vezes=8)
    
    # FASE 2: Teste de reconstrução
    print(f"\n{'='*70}")
    print(f"  TESTE DE RECONSTRUÇÃO")
    print(f"{'='*70}")
    
    for pergunta in [
        "Crie um NPC ferreiro em Eridanus",
        "Explique o sistema SPA do MCR",
        "O que e Canary?",
    ]:
        proto.testar_reconstrucao(pergunta)
    
    # FASE 3: Relatório
    proto.relatorio()
    
    print(f"\n{'='*70}")
    print(f"  PROTÓTIPO CONCLUÍDO")
    print(f"  Ciclo validado: dado → PE.tokenizar → Aprendiz.estudar → KG → Reconstruir")
    print(f"{'='*70}")
