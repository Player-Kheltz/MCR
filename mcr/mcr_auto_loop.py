"""MCR Auto-Loop — Executa, avalia, expande até 10/10.

Conceito:
  1. Carrega dados iniciais (8 lessons)
  2. Tenta conectar topicos distantes (ex: spa + arvore_natal)
  3. Autoavalia por Jaccard + Markov coherence
  4. Se nota < 10: expande conhecimento com novos dados
  5. Loop até nota 10/10 ou max_iteracoes
  6. Mostra EVOLUÇÃO: nota cresce a cada ciclo

Diferente do auto-loop anterior:
  - Usa Markov coherence (não entropia de Shannon)
  - Penaliza strings aleatórias ('xyz')
  - Expansão é incremental: cada ciclo adiciona mais dados
"""
import os, sys, json, math

sys.path.insert(0, os.path.dirname(__file__))

from core.markov_universal import MarkovUniversal
from core.mcr_emergir import MCREmergir
from core.jaccard_byte import jaccard_bytes


class MCRAutoLoop:
    """Auto-Loop MCR: executa → avalia → expande → até 10/10."""
    
    def __init__(self, dados_base: str, expansoes: str):
        self.mcr = MCREmergir()
        self.dados_base = dados_base
        self.expansoes = expansoes
        self.historico = []
        self._cache_expansoes = None
    
    def carregar_base(self) -> int:
        """Carrega dados iniciais."""
        return self.mcr.alimentar_json(self.dados_base)
    
    def _carregar_expansoes(self) -> list:
        """Carrega expansoes do JSON."""
        if self._cache_expansoes is not None:
            return self._cache_expansoes
        with open(self.expansoes, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        self._cache_expansoes = dados.get('topicos', [])
        return self._cache_expansoes
    
    def expandir(self, n: int = 1) -> int:
        """Adiciona N expansoes ao MCR."""
        expansoes = self._carregar_expansoes()
        inicio = len(self.mcr.topicos) - 8  # desconsidera os 8 iniciais
        # As expansoes tem nomes como spa_expansao_1, spa_expansao_2 etc.
        # Ja estao todas carregadas pelo alimentar_json, mas vamos verificar
        adicionadas = 0
        for item in expansoes[:n]:
            nome = item.get('nome', '')
            texto = item.get('texto', '')
            if nome not in self.mcr.topicos:
                self.mcr.alimentar(texto, nome)
                adicionadas += 1
        return adicionadas
    
    def tentar_conexao(self, topico_a: str, topico_b: str) -> dict:
        """Tenta conectar dois topicos e retorna resultado completo."""
        resultado = self.mcr.conectar(topico_a, topico_b)
        if resultado is None:
            return {
                'conectou': False,
                'nota': 0.0,
                'topico_a': topico_a,
                'topico_b': topico_b,
                'sequencia': '(sem conexao)',
                'jaccard_a': 0.0,
                'jaccard_b': 0.0,
                'coerencia': 0.0,
            }
        
        # Calcula coerencia markov extra
        coer = self.mcr._coerencia_markov(resultado['sequencia'])
        
        return {
            'conectou': True,
            'nota': resultado['nota'],
            'topico_a': resultado['topico_a'],
            'topico_b': resultado['topico_b'],
            'sequencia': resultado['sequencia'],
            'jaccard_a': resultado['jaccard_a'],
            'jaccard_b': resultado['jaccard_b'],
            'coerencia': coer,
            'ponte': resultado.get('ponte', '?'),
        }
    
    def loop(self, topico_a: str, topico_b: str,
             max_iteracoes: int = 12, max_expansoes: int = 14) -> dict:
        """Loop principal: executa, avalia, expande até 10/10.
        
        Args:
            topico_a: primeiro topico para conectar
            topico_b: segundo topico para conectar
            max_iteracoes: limite de ciclos
            max_expansoes: quantas expansoes carregar no total
        Returns:
            dict com historico completo da evolucao
        """
        print(f"\n  Loop: {topico_a} <-> {topico_b}")
        print(f"  Max iteracoes: {max_iteracoes}")
        print(f"  Expansoes disponiveis: {max_expansoes}")
        print()
        
        # Carrega dados base
        n_base = self.carregar_base()
        print(f"  Base carregada: {n_base} topicos")
        
        # Carrega todas as expansoes de uma vez (mas nao alimenta ainda)
        self._carregar_expansoes()
        
        melhor_nota = 0.0
        iteracao = 0
        
        for ciclo in range(max_iteracoes):
            iteracao += 1
            print(f"\n  ─── Ciclo {iteracao} ───")
            
            # Tenta conectar
            resultado = self.tentar_conexao(topico_a, topico_b)
            nota = resultado['nota']
            
            # Registra no historico
            entrada = {
                'ciclo': ciclo + 1,
                'nota': nota,
                'conectou': resultado['conectou'],
                'sequencia': resultado['sequencia'][:80] if resultado['conectou'] else '(sem)',
                'jaccard_a': resultado['jaccard_a'],
                'jaccard_b': resultado['jaccard_b'],
                'coerencia': resultado['coerencia'],
                'topicos_carregados': len(self.mcr.topicos),
            }
            self.historico.append(entrada)
            
            # Status
            status = f"  Nota: {nota:.1f}/10"
            if resultado['conectou']:
                status += f" | Jaccard A={resultado['jaccard_a']:.3f} B={resultado['jaccard_b']:.3f}" \
                          f" | Coerencia Markov: {resultado['coerencia']:.2f}"
            else:
                status += " | Sem conexao"
            print(status)
            
            if resultado['conectou']:
                print(f"  Seq: {resultado['sequencia'][:80]}")
            
            if nota > melhor_nota:
                melhor_nota = nota
                print(f"  >>> NOVA MELHOR NOTA: {melhor_nota:.1f}/10")
            
            # Se atingiu 10/10, entrega
            if nota >= 10.0:
                print(f"\n  {'=' * 50}")
                print(f"  >>> 10/10 ATINGIDO no ciclo {ciclo + 1}! <<<")
                print(f"  {'=' * 50}")
                print(f"\n  Conexao final:")
                print(f"  {resultado['sequencia']}")
                break
            
            # Se não atingiu, expande
            if ciclo < max_expansoes:
                n_exp = self.expandir(1)
                if n_exp > 0:
                    print(f"  Expandindo: +{n_exp} topico(s) ({len(self.mcr.topicos)} total)")
                else:
                    # Se todas as expansoes ja foram carregadas, tenta com dados diferentes
                    print(f"  Todas as expansoes carregadas. Re-tentando com mais contexto...")
                    # Alimenta com combinacoes dos proprios topicos existentes
                    self._alimentar_combinacoes()
            else:
                print(f"  Limite de expansoes atingido.")
                break
        
        # Relatorio final
        print(f"\n  {'=' * 50}")
        print(f"  RESUMO DO AUTO-LOOP")
        print(f"  {'=' * 50}")
        print(f"  Ciclos: {iteracao}")
        print(f"  Melhor nota: {melhor_nota:.1f}/10")
        print(f"  Topicos ao final: {len(self.mcr.topicos)}")
        print(f"  Conexao final: {self.historico[-1]['sequencia'][:100] if self.historico else '(nenhuma)'}")
        
        # Evolucao
        print(f"\n  Evolucao das notas:")
        barras = []
        for h in self.historico:
            barra = '█' * max(0, min(10, int(h['nota'])))
            barra += '░' * max(0, 10 - max(0, min(10, int(h['nota']))))
            barras.append(f"    C{h['ciclo']:2d}: [{barra}] {h['nota']:.1f}")
        print('\n'.join(barras))
        
        return {
            'historico': self.historico,
            'melhor_nota': melhor_nota,
            'ciclos': iteracao,
            'conexao_final': self.historico[-1] if self.historico else None,
            'atingiu_10': self.historico[-1]['nota'] >= 10.0 if self.historico else False,
        }
    
    def _alimentar_combinacoes(self):
        """Gera conhecimento sintetico combinando topicos existentes.
        
        Isso simula o 'aprender fazendo' — o sistema cria novos dados
        a partir do que ja conhece.
        """
        topicos = list(self.mcr.topicos.keys())
        
        # Pega ultimos 4 topicos e combina
        if len(topicos) >= 4:
            recentes = topicos[-4:]
            for i in range(0, len(recentes) - 1, 2):
                a = recentes[i]
                b = recentes[i + 1]
                texto_a = self.mcr.topicos[a]['texto']
                texto_b = self.mcr.topicos[b]['texto']
                # Cria uma combinacao simples: metade de cada
                metade_a = texto_a[:len(texto_a)//2]
                metade_b = texto_b[len(texto_b)//2:]
                combinado = f"{metade_a} {metade_b}"
                nome = f"combinado_{a}_{b}"
                if nome not in self.mcr.topicos:
                    self.mcr.alimentar(combinado, nome)
                    print(f"  Alimentando combinado: {nome}")
                    return  # 1 por ciclo


def main():
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   MCR AUTO-LOOP — Executa, avalia, expande até 10/10    ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    print("  Conceito:")
    print("  - Carrega 8 lessons base (SPA, SHC, NPC, Natal, etc.)")
    print("  - Tenta conectar topicos distantes por MarkovByte")
    print("  - Autoavalia por Jaccard + Markov coherence")
    print("  - Se < 10/10: expande conhecimento com novos dados")
    print("  - Loop ate 10/10 ou 12 ciclos")
    print()
    
    dados_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dados')
    dados_base = os.path.join(dados_dir, 'lessons_exemplo.json')
    expansoes = os.path.join(dados_dir, 'expansoes.json')
    
    if not os.path.exists(dados_base) or not os.path.exists(expansoes):
        print("  ERRO: arquivos de dados nao encontrados.")
        print(f"  Esperado: {dados_base}")
        print(f"  Esperado: {expansoes}")
        sys.exit(1)
    
    # ─── TESTE 1: SPA + Arvore de Natal ─────────────────────────
    print()
    print("=" * 60)
    print("  TESTE 1: CONECTAR SPA + ARVORE DE NATAL")
    print("  (topicos muito distantes, conexao nao-obvia)")
    print("=" * 60)
    
    loop1 = MCRAutoLoop(dados_base, expansoes)
    resultado1 = loop1.loop("spa", "arvore_natal")
    
    # ─── TESTE 2: NPC Ferreiro + MountSummon ────────────────────
    print()
    print("=" * 60)
    print("  TESTE 2: CONECTAR NPC FERREIRO + MOUNTSUMMON")
    print("  (topicos de domacios, conexao via forja)")
    print("=" * 60)
    
    loop2 = MCRAutoLoop(dados_base, expansoes)
    resultado2 = loop2.loop("npc_ferreiro", "mount_summon")
    
    # ─── TESTE 3: Eridanus + Quest Primeiro Metal ────────────────
    print()
    print("=" * 60)
    print("  TESTE 3: CONECTAR ERIDANUS + QUEST PRIMEIRO METAL")
    print("  (topicos de localizacao, conexao via NPCs)")
    print("=" * 60)
    
    loop3 = MCRAutoLoop(dados_base, expansoes)
    resultado3 = loop3.loop("eridanus_cidade", "quest_primeiro_metal")
    
    # ─── RESUMO GERAL ────────────────────────────────────────────
    print()
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   RESUMO GERAL DOS AUTO-LOOPS                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    for nome, res in [("SPA + Natal", resultado1),
                       ("Ferreiro + Mount", resultado2),
                       ("Eridanus + Quest", resultado3)]:
        print(f"  {nome:25s}: {res['ciclos']:2d} ciclos, nota final {res['melhor_nota']:.1f}/10, "
              f"{'10/10!' if res['atingiu_10'] else 'maximo'}")
    
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   AUTO-LOOP CONCLUIDO                                    ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()


if __name__ == '__main__':
    main()
