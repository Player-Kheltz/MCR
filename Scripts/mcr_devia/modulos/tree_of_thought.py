"""Tree of Thought — Arvore de Pensamento para o MCR-DevIA.
Gera multiplas perspectivas em paralelo e sintetiza em resposta final.

Arquitetura:
1. PERGUNTA → 3 caminhos de pensamento PARALELOS (threads)
2. Cada caminho usa o Orquestrador com perspectiva diferente
3. SINTESE: junta as 3 perspectivas em resposta unica
"""
import os, sys, json, time, threading, re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

def _gerar(prompt, temp=0.4, tarefa="texto"):
    """Chamada ao modelo via router padronizado."""
    try:
        from modulos.util import gerar as _util_gerar
        return _util_gerar(prompt, temp, tarefa) or ""
    except:
        return ""

# Direcoes de pensamento (perspectivas)
_CAMINHOS = [
    {
        "nome": "analitico",
        "instrucao": "Pense como um ANALISTA. Foque em dados, fatos, numeros, versoes, metricas e detalhes tecnicos. Seja especifico e preciso."
    },
    {
        "nome": "criativo",
        "instrucao": "Pense como um CONTADOR DE HISTORIAS. Use exemplos concretos, analogias, cenarios praticos e aplicacoes reais. Torne o conceito vivido."
    },
    {
        "nome": "critico",
        "instrucao": "Pense como um REVISOR. Analise contra-pontos, limitacoes, contextos diferentes e nuances. Evite generalizacoes."
    },
]


class TreeOfThought:
    """Arvore de Pensamento com 3 perspectivas paralelas + sintese."""
    
    def __init__(self, orquestrador=None):
        self.orquestrador = orquestrador
    
    def _chamar_perspectiva(self, pergunta: str, perspectiva: dict, 
                           params_extra: dict = None) -> str:
        """Chama uma perspectiva de pensamento."""
        nome = perspectiva["nome"]
        instrucao = perspectiva["instrucao"]
        
        prompt = (
            f"{instrucao}\n\n"
            f"Pergunta: {pergunta}\n\n"
            f"Resposta da perspectiva {nome}:"
        )
        
        if self.orquestrador:
            params = {
                'pergunta': prompt,
                'identidade': '',
                'instrucao_contexto': params_extra.get('instrucao_contexto', '') if params_extra else '',
                'contexto_enriquecido': params_extra.get('contexto_enriquecido', '') if params_extra else '',
                'contexto_extra': params_extra.get('contexto_extra', '') if params_extra else '',
                'ctx_infinity': params_extra.get('ctx_infinity', '') if params_extra else '',
            }
            resultado = self.orquestrador.executar('perguntar', params, consulta=prompt, temp=0.5)
            if resultado and resultado.get('sucesso'):
                return resultado['resposta']
        
        # Fallback: chamada direta
        return _gerar(prompt, 0.5, "texto") or ""
    
    def pensar(self, pergunta: str, params_extra: dict = None) -> dict:
        """Executa arvore de pensamento completa.
        
        Args:
            pergunta: Pergunta enriquecida (ja com CR + Enricher)
            params_extra: Params extras para repassar ao Orquestrador
        
        Returns:
            dict: {resposta, perspectivas, tempo_total}
        """
        t0 = time.time()
        perspectivas = [None] * len(_CAMINHOS)
        erros = [None] * len(_CAMINHOS)
        
        def executar(i, cam):
            try:
                resp = self._chamar_perspectiva(pergunta, cam, params_extra)
                perspectivas[i] = resp
                print(f'  [ToT] Perspectiva {cam["nome"]} OK ({len(resp or "")} chars)')
            except Exception as e:
                erros[i] = str(e)
                print(f'  [ToT] Perspectiva {cam["nome"]} ERRO: {e}')
        
        # 3 perspectivas EM PARALELO
        threads = []
        for i, cam in enumerate(_CAMINHOS):
            t = threading.Thread(target=executar, args=(i, cam), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join(timeout=45)  # timeout por thread
        
        perspectivas_validas = []
        for i, p in enumerate(perspectivas):
            if p and len(p) > 30:
                # Filtra alucinacoes
                pl = p.lower()
                proibidos = ['minecraft', 'wotc', 'd&d', 'wizards of the coast']
                if any(proib in pl for proib in proibidos):
                    print(f'  [ToT] Perspectiva {_CAMINHOS[i]["nome"]} FILTRADA (alucinacao)')
                    continue
                perspectivas_validas.append({
                    'nome': _CAMINHOS[i]['nome'],
                    'texto': p
                })
        
        if not perspectivas_validas:
            return {
                'resposta': '',
                'perspectivas': [],
                'tempo_total': round(time.time() - t0, 1),
                'erro': 'Todas as perspectivas falharam ou foram filtradas'
            }
        
        # SINTESE: junta as perspectivas em resposta unica
        perspectivas_texto = '\n\n'.join([
            f"=== PERSPECTIVA {p['nome'].upper()} ===\n{p['texto']}"
            for p in perspectivas_validas
        ])
        
        prompt_sintese = (
            "O projeto MCR e um servidor customizado de Tibia baseado em Canary (OTServ).\n"
            "Nao e Minecraft, nem D&D, nem qualquer outro sistema.\n\n"
            "Voce recebeu 3 perspectivas diferentes sobre a mesma pergunta.\n"
            "SINTETIZE em uma resposta unica, coesa e completa.\n"
            "INCORPORE o melhor de cada perspectiva.\n"
            "Estruture em paragrafos fluidos.\n"
            "Use linguagem natural e direta.\n\n"
            f"{perspectivas_texto}\n\n"
            "Resposta sintetizada (apenas fatos do projeto MCR - Tibia):"
        )
        
        sintese = _gerar(prompt_sintese, 0.3, "texto") or perspectivas_validas[0]
        
        tempo_total = round(time.time() - t0, 1)
        print(f'  [ToT] Sintese OK ({len(sintese)} chars, {tempo_total}s)')
        
        return {
            'resposta': sintese,
            'perspectivas': [p['texto'] for p in perspectivas_validas],
            'tempo_total': tempo_total,
            'erro': None
        }
