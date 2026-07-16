#!/usr/bin/env python3
"""mcr.mcr_world_system — Motor de Mundo Markoviano.
Substitui o expandir_mundo linear por um loop cognitivo de 4 estados:
EXPANDIR, CONECTAR, EQUILIBRAR, EVOLUIR.

A entropia de Shannon da distribuicao de tipos do world_state
decide qual estado ativar. O MCRDecisor aprende as transicoes."""
import json
import math
import os
import re
import time
from collections import Counter
from typing import Dict, List, Optional, Tuple

from mcr.config_llm import MODELO

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

# ─── 5 Estados do Mundo ───────────────────────────────────
ESTADOS = ['EXPANDIR', 'CONECTAR', 'EQUILIBRAR', 'EVOLUIR', 'COMPENSAR']

# Thresholds de entropia para mudanca de estado
H_BAIXO = 0.2   # abaixo disso: pouca diversidade, precisa EXPANDIR
H_MEDIO = 0.5   # entre 0.2 e 0.5: diversidade moderada, pode CONECTAR
H_ALTO = 0.7    # acima 0.5: diversidade alta, pode precisar EQUILIBRAR

# Templateabilidade via Radar: threshold de similaridade com cluster canonico
TEMPLATE_THRESHOLD = 0.85


class MCRWorldSystem:
    """Orquestrador cognitivo do mundo. 

    Loop principal: perceber_estado → calcular_entropia → decidir_acao 
                     → executar → autoavaliar
    
    Cada execucao e uma transicao Markov. O MCRDecisor aprende
    qual acao funciona melhor para cada faixa de entropia.
    """

    def __init__(self):
        # MCR interno para transicoes de estado do mundo
        # Aprende: "estado_atual + entropia → proximo_estado"
        from mcr.mcr_meta import MCRMeta
        from mcr.metacognicao import Metacognicao
        from mcr.equacao_mcr import calcular_ponte
        
        # MCR interno para transicoes de estado do mundo
        # Usa classe MCR do kernel (stdlib)
        import sys as _sys
        try:
            from MCR import MCR as MCR_base
        except Exception:
            # Fallback: MCR minimalista embutido
            class MCR_base:
                def __init__(self, nome=''):
                    self.nome = nome
                    self.transicoes = {}
                    self.freq = {}
                    self.total = 0
                def aprender(self, a, b):
                    sa, sb = str(a), str(b)
                    self.freq[sa] = self.freq.get(sa, 0) + 1
                    self.total += 1
                    if sa not in self.transicoes:
                        self.transicoes[sa] = {}
                    self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
                def predizer(self, a):
                    sa = str(a)
                    if sa not in self.transicoes or not self.transicoes[sa]:
                        return None, 0.0
                    prox = self.transicoes[sa]
                    melhor = max(prox, key=prox.get)
                    total = sum(prox.values())
                    return melhor, prox[melhor] / total

        self.mcr_transicoes = MCR_base("world_transitions")

        self.mcr_transicoes = MCR_base("world_transitions")
        self.mcr_meta = MCRMeta()
        self.metacognicao = Metacognicao()
        self._historico = []
        self._threshold_metacog = 0.70
        self._ultimas_notas_ponte = []

    # ─── Percepcao ─────────────────────────────────────────

    def _perceber_estado(self, world_state: dict) -> dict:
        """Le o world_state e extrai metricas de distribuicao."""
        npcs = world_state.get('npcs', {})
        monstros = world_state.get('monstros', {})
        quests_count = 0
        for npc_data in npcs.values():
            quests_count += len(npc_data.get('quests', []))

        # Distribuicao de tipos
        distribuicao = Counter()
        for nome, dados in npcs.items():
            role = dados.get('role', 'desconhecido')
            if not role or role.strip() == '':
                # Extrai hint do nome: "NPC_Ferreiro" → "ferreiro"
                nome_parts = nome.split('_')
                if len(nome_parts) > 1 and nome_parts[0] == 'NPC':
                    role = nome_parts[1].lower()
                else:
                    role = 'npc_generico'
            distribuicao[role] += 1
        for nome in monstros:
            distribuicao['monstro'] += 1

        total = sum(distribuicao.values()) or 1
        return {
            'total_npcs': len(npcs),
            'total_monstros': len(monstros),
            'total_quests': quests_count,
            'distribuicao': dict(distribuicao),
            'entropia': self._calcular_entropia(distribuicao),
            'roles_presentes': list(distribuicao.keys()),
        }

    @staticmethod
    def _calcular_entropia(distribuicao: Counter) -> float:
        """Entropia de Shannon da distribuicao de papeis do mundo.
        
        H = -sum(p * log2(p))
        Baixa H = pouca variedade de papeis (so ferreiros)
        Alta H = muitas variedades (ferreiros, magos, guardas...)
        """
        total = sum(distribuicao.values()) or 1
        h = 0.0
        for count in distribuicao.values():
            p = count / total
            if p > 0:
                h -= p * math.log2(p)
        # Normaliza para 0-1 (max possivel para N tipos)
        n = len(distribuicao)
        h_max = math.log2(max(n, 2))
        return h / h_max if h_max > 0 else 0.0

    # ─── Decisao Markoviana ────────────────────────────────

    def _decidir_acao(self, estado_percebido: dict) -> str:
        """Decide qual estado atuar usando MCR + fallback por entropia.
        
        O MCR aprende: "entropia:X,total_npcs:Y,quests:Z" → "ACAO"
        Se a confianca do MCR > 0.3, usa a predicao.
        Senao, fallback heuristico baseado na entropia.
        """
        h = estado_percebido['entropia']
        total_npcs = estado_percebido['total_npcs']
        total_quests = estado_percebido['total_quests']
        
        # Codigo do estado para o MCR
        codigo = "h:%.2f,n:%d,q:%d" % (h, total_npcs, total_quests)

        # Tenta MCR primeiro
        acao_pred, conf = self.mcr_transicoes.predizer(codigo)
        if acao_pred and conf > 0.3 and str(acao_pred) in ESTADOS:
            print('[WorldSystem] MCR decidiu: %s (conf=%.2f)' % (acao_pred, conf))
            return str(acao_pred)

        # Fallback: baseado na entropia
        if total_npcs == 0:
            acao = 'EXPANDIR'
        elif h < H_BAIXO:
            # Baixa diversidade → EXPANDIR com tipos diferentes
            acao = 'EXPANDIR'
        elif h < H_MEDIO and total_quests == 0:
            # Diversidade moderada mas sem conexoes → CONECTAR
            acao = 'CONECTAR'
        elif h > H_ALTO:
            # Alta diversidade → EQUILIBRAR
            acao = 'EQUILIBRAR'
        elif total_npcs > 0 and total_quests < total_npcs * 0.5:
            # Menos quests que NPCs → CONECTAR
            acao = 'CONECTAR'
        else:
            acao = 'EXPANDIR'

        print('[WorldSystem] Decisao (fallback): %s (h=%.2f, npcs=%d, quests=%d)' % (
            acao, h, total_npcs, total_quests))
        return acao

    # ─── Execucao: Templateabilidade via Radar ─────────────

    def _verificar_templateabilidade(self, descricao: str) -> Tuple[bool, float]:
        """Verifica se uma descricao pode ser gerada via golden template.
        
        Usa o Radar para buscar similaridade com clusters canonicos do KG.
        Se > TEMPLATE_THRESHOLD, retorna True (pode usar template sem LLM).
        
        Returns:
            (pode_usar_template, score_similaridade)
        """
        try:
            from mcr.mcr_radar import RadarMCR
            from mcr.paths import KG_DIR
            from mcr.encoding import read_file

            # Carrega alguns padroes do KG como candidatos
            candidatos = []
            for fpath in sorted(KG_DIR.glob('patterns_*.json'))[:2]:  # limita
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    items = dados.get('padroes', dados if isinstance(dados, list) else [])
                    for p in items[:50]:  # 50 por arquivo
                        arquivo = p.get('arquivo', '')
                        if not arquivo or not os.path.exists(arquivo):
                            continue
                        try:
                            conteudo = read_file(arquivo)[:300]
                        except Exception:
                            continue
                        texto_busca = os.path.basename(arquivo) + ' '
                        texto_busca += ' '.join(p.get('variaveis', [])) + ' '
                        texto_busca += ' '.join(p.get('api_calls', [])) + ' '
                        texto_busca += conteudo
                        candidatos.append({'id': arquivo, 'texto': texto_busca})
                except Exception:
                    continue

            if not candidatos:
                return False, 0.0

            radar = RadarMCR()
            resultados = radar.buscar(descricao, candidatos,
                                      funcao_similaridade=RadarMCR.fingerprint_sim)
            if resultados:
                melhor_score = resultados[0].get('score', 0)
                return (melhor_score >= TEMPLATE_THRESHOLD, melhor_score)
            return False, 0.0
        except Exception as e:
            print('[WorldSystem] Erro templateabilidade: %s' % e)
            return False, 0.0

    # ─── Execucao das Acoes ────────────────────────────────

    def _executar_expandir(self, tema: str, estado_percebido: dict,
                           estado_acumulado: dict, pending_names: set) -> dict:
        """EXPANDIR: gera nova entidade via Emergir + Radar + codificar/template."""
        from mcr.emergir import Emergir
        from mcr.mcr_idea_to_spec import idea_to_entity_spec, _buscar_golden_exemplo
        from mcr.mcr_entity_validator import validate_entity
        from mcr.mcr_entity_factory import create_entity

        # Descobre tipos faltantes no mundo
        roles_presentes = set(estado_percebido.get('roles_presentes', []))
        roles_todos = {'vendedor', 'guarda', 'ferreiro', 'mago', 'alquimista',
                       'cacador', 'mercador', 'artesao', 'soldado', 'curandeiro'}
        tipos_faltando = roles_todos - roles_presentes

        # Gera ideia via Emergir com foco nos tipos faltantes
        emergir = Emergir(llm_func=None)
        conceitos = list(tipos_faltando) if tipos_faltando else ['aventureiro', 'comerciante']
        if not conceitos:
            conceitos = ['aventureiro']
        ideias = emergir.gerar_ideias_tematicas(conceitos, n=5)

        if not ideias:
            return {'sucesso': False, 'erro': 'Nenhuma ideia gerada'}

        ideia = ideias[0]
        print('  Ideia: %s' % ideia['ideia'][:80])

        # Metacognicao como portao
        avaliacao = self.metacognicao.avaliar_pedido(ideia['ideia'])
        if not avaliacao.get('aprovado', False):
            return {'sucesso': False, 'erro': 'metacognicao: score=%.2f' %
                    avaliacao.get('score', 0)}

        # Templateabilidade: usa Radar para decidir Tier 1 vs Tier 2
        pode_template, score_tpl = self._verificar_templateabilidade(ideia['ideia'])
        print('  Templateabilidade: score=%.2f %s' % (
            score_tpl, '(TEMPLATE)' if pode_template else '(LLM)'))

        if pode_template:
            # Tier 1: golden template, zero LLM
            from mcr.golden_templates import gerar_npc_canary, salvar_npc_parametrizado
            from mcr.mcr_world_builder import _validar_sintaxe, _validar_semantica
            from mcr.mcr_world_state import _carregar as _carregar_ws
            params = {
                'name': 'NPC_%s' % ideia.get('conceito_a', 'generico').capitalize(),
                'health': 100,
                'looktype': 128,
                'greeting': 'Ola, seja bem-vindo!',
            }
            codigo = gerar_npc_canary(params)
            valido, _ = _validar_sintaxe(codigo)
            apis = _validar_semantica(codigo, 'npc')
            if valido and not apis:
                resultado_msg = salvar_npc_parametrizado(params)
                import re as _re
                nome_arquivo = _re.sub(r'[^a-z0-9_]', '',
                                       params['name'].lower().replace(' ', '_')) + '.lua'
                from mcr.paths import CANARY_NPC_DIR
                caminho = str(CANARY_NPC_DIR / nome_arquivo)
                from mcr.mcr_world_state import registrar_entidade
                registrar_entidade('npc', params['name'], {
                    'file': caminho, 'role': '',
                    'tier': 'template_radar',
                    'quests': [],
                })
                # Atualiza estado em memoria (sincronia com disco)
                estado_acumulado['npcs'][params['name']] = {
                    'role': '', 'file': caminho, 'tier': 'template_radar', 'quests': [],
                }
                estado_acumulado['characters'].append({
                    'name': params['name'], 'role': '', 'state': 'alive'})
                pending_names.add(params['name'])
                return {
                    'sucesso': True, 'entidade': params['name'], 'tipo': 'npc',
                    'tier': 'template_radar', 'arquivo': resultado_msg,
                }

        # Tier 2: LLM via idea_to_entity_spec + codificar
        golden = _buscar_golden_exemplo(ideia['ideia'])
        spec = idea_to_entity_spec(ideia['ideia'], tema, golden_exemplo=golden)
        if not spec:
            return {'sucesso': False, 'erro': 'spec_falhou'}

        valido, erros_val = validate_entity(spec, estado_acumulado, pending_names)
        if not valido:
            return {'sucesso': False, 'erro': '; '.join(erros_val[:2])}

        pending_names.add(spec.get('name', '') or spec.get('title', ''))
        resultado = create_entity(spec, estado_acumulado)
        if resultado.get('sucesso'):
            estado_acumulado['characters'].append({
                'name': spec.get('name', ''),
                'role': spec.get('role', ''),
                'faction': spec.get('faction', ''),
                'state': 'alive',
            })
        return resultado

    def _executar_conectar(self, tema: str, estado_percebido: dict,
                            estado_acumulado: dict, pending_names: set) -> dict:
        """CONECTAR: gera quests conectando NPCs existentes via What-If 2o nivel."""
        from mcr.mcr_world_builder import expandir_npc
        from mcr.mcr_world_foundation import world_event
        from mcr.mcr_world_state import _carregar as _carregar_estado

        npcs = list(estado_acumulado.get('npcs', {}).keys()) or \
               [c['name'] for c in estado_acumulado.get('characters', []) if 'name' in c]

        if len(npcs) < 2:
            return {'sucesso': False, 'erro': 'menos de 2 NPCs para conectar'}

        personagens = npcs[:5]
        prompt = (
            "Baseado nos personagens abaixo, sugira 1 quest que conecte "
            "dois ou mais personagens existentes.\n"
            "Personagens: %s\n\n" % ', '.join(personagens) +
            "Formato:\nTitulo: ...\nGiver: ...\nObjetivo: ...\nRecompensa: ...\n"
            "A quest deve ser tematicamente coerente com o giver."
        )

        # Tenta MCRConector primeiro (zero LLM, zero rede)
        texto = None
        try:
            from mcr.memory import MCRConector
            conector = MCRConector()
            for n in personagens[:3]:
                conector.alimentar(f"NPC: {n}", n)
            if len(personagens) >= 2:
                ponte = conector.conectar(personagens[0], personagens[1])
                if ponte and ponte.get('nota', 0) > 3:
                    texto = (
                        f"Titulo: Conexao {personagens[0][:10]} e {personagens[1][:10]}\n"
                        f"Giver: {personagens[0]}\n"
                        f"Objetivo: {ponte.get('sequencia', 'Conectar os personagens')[:80]}\n"
                        f"Recompensa: {ponte.get('nota', 5) * 10} gold\n"
                    )
        except Exception:
            pass

        # Fallback: LLM (Ollama)
        if not texto:
            try:
                import urllib.request
                payload = json.dumps({
                    "model": MODELO, "prompt": prompt, "stream": False,
                    "options": {"temperature": 0.7, "max_tokens": 500}
                }).encode()
                req = urllib.request.Request(
                    "http://localhost:11434/api/generate", data=payload,
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    resp = json.loads(r.read())
                texto = resp.get('response', '')
            except Exception as e:
                return {'sucesso': False, 'erro': 'LLM: %s' % e}

        if not texto:
            return {'sucesso': False, 'erro': 'Nenhuma conexao gerada'}

        # Parseia
        titulo_m = re.search(r'T[ií]tulo:\s*(.+?)(?:\n|$)', texto)
        giver_m = re.search(r'Giver:\s*(.+?)(?:\n|$)', texto)
        obj_m = re.search(r'O[bj]etivo:\s*(.+?)(?:\n|$)', texto)
        recomp_m = re.search(r'Recompensa:\s*(.+?)(?:\n|$)', texto)

        if not giver_m:
            return {'sucesso': False, 'erro': 'parser: giver nao encontrado'}

        giver = giver_m.group(1).strip()
        titulo = titulo_m.group(1).strip() if titulo_m else 'Quest'
        objetivo = obj_m.group(1).strip() if obj_m else ''
        recompensa = recomp_m.group(1).strip() if recomp_m else ''

        # Verifica giver no world_state
        ws = _carregar_estado()
        giver_real = None
        for nome_npc in ws.get('npcs', {}):
            if giver.lower() in nome_npc.lower():
                giver_real = nome_npc
                break
        if not giver_real:
            return {'sucesso': False, 'erro': 'giver "%s" nao encontrado' % giver}

        instrucao = "Adicione uma quest a '%s'. Titulo: %s. Objetivo: %s. Recompensa: %s." % (
            giver_real, titulo, objetivo, recompensa)
        resultado_q = expandir_npc(giver_real, instrucao)
        if resultado_q.get('sucesso'):
            try:
                world_event('quest', titulo, new_state='active',
                            narrative="Quest '%s' com %s." % (titulo, giver_real),
                            source='world_system_conectar')
            except Exception:
                pass
            return {'sucesso': True, 'entidade': titulo, 'tipo': 'quest',
                    'giver': giver_real, 'arquivo': resultado_q.get('arquivo', '')}
        return {'sucesso': False, 'erro': resultado_q.get('erro', 'expandir_npc falhou')}

    def _executar_equilibrar(self, tema: str, estado_percebido: dict,
                              estado_acumulado: dict, pending_names: set) -> dict:
        """EQUILIBRAR: preenche lacunas ecológicas (ex: monstros faltando)."""
        # Por enquanto, gera um monstro via golden template
        from mcr.golden_templates import gerar_monstro_parametrizado, salvar_monstro_parametrizado
        from mcr.mcr_world_builder import _validar_sintaxe, _validar_semantica
        from mcr.mcr_world_state import registrar_entidade
        import random

        nomes_monstros = ['Espectro do Mercado', 'Goblin Contrabandista',
                          'Lobo Sombrio', 'Golem de Pedra', 'Morcego Venenoso']
        perigos = ['low', 'medium', 'high']
        nome = random.choice(nomes_monstros)
        perigo = random.choice(perigos)

        hp_map = {'low': 200, 'medium': 800, 'high': 3000}
        exp_map = {'low': 200, 'medium': 1500, 'high': 8000}

        params = {
            'name': nome,
            'health': hp_map.get(perigo, 500),
            'experience': exp_map.get(perigo, 1000),
            'description': 'Um monstro descoberto durante a expansao do mundo.',
        }

        codigo = gerar_monstro_parametrizado(params)
        valido, _ = _validar_sintaxe(codigo)
        apis = _validar_semantica(codigo, 'monster')
        if valido and not apis:
            resultado_msg = salvar_monstro_parametrizado(params)
            registrar_entidade('monster', nome, {
                'file': '', 'habitat': 'desconhecido',
                'danger_level': perigo,
            })
            estado_acumulado['monstros'][nome] = {
                'habitat': 'desconhecido', 'danger_level': perigo}
            estado_acumulado['characters'].append({
                'name': nome, 'role': 'monstro', 'state': 'alive'})
            pending_names.add(nome)
            return {'sucesso': True, 'entidade': nome, 'tipo': 'monster',
                    'tier': 'template', 'arquivo': resultado_msg}

        return {'sucesso': False, 'erro': 'monstro template falhou'}

    def _executar_evoluir(self, tema: str, estado_percebido: dict,
                           estado_acumulado: dict, ultimo_resultado: dict = None) -> dict:
        """EVOLUIR: recalibra thresholds baseado na qualidade do ultimo resultado."""
        from mcr.mcr_meta import MCRMeta
        
        if ultimo_resultado and ultimo_resultado.get('sucesso'):
            # Se a ultima entidade foi criada com sucesso, aprende a transicao
            h = estado_percebido['entropia']
            codigo = "h:%.2f,n:%d,q:%d" % (
                h, estado_percebido['total_npcs'], estado_percebido['total_quests'])
            acao_realizada = ultimo_resultado.get('acao', 'EXPANDIR')
            self.mcr_transicoes.aprender(codigo, acao_realizada)
            # Reforco
            for _ in range(2):
                self.mcr_transicoes.aprender(codigo, acao_realizada)

        # Ajusta threshold da metacognicao baseado na PONTE_OTIMA
        if len(self._ultimas_notas_ponte) >= 3:
            media_recente = sum(self._ultimas_notas_ponte[-3:]) / 3
            if media_recente < 5.0:
                # Qualidade caindo: fica mais seletivo
                self._threshold_metacog = min(0.85, self._threshold_metacog + 0.05)
                print('[WorldSystem] Threshold metacog aumentado para %.2f (PONTE=%.1f)' % (
                    self._threshold_metacog, media_recente))
            elif media_recente > 7.0:
                # Qualidade boa: pode relaxar um pouco
                self._threshold_metacog = max(0.65, self._threshold_metacog - 0.02)

        return {'sucesso': True, 'threshold_metacog': self._threshold_metacog,
                'transicoes_aprendidas': len(self.mcr_transicoes.transicoes)}

    # ─── Autoavaliacao ─────────────────────────────────────

    def _autoavaliar(self, resultado_acao: dict, estado_percebido: dict) -> float:
        """Autoavaliacao: nota baseada no impacto da acao na entropia."""
        if not resultado_acao.get('sucesso'):
            return 0.0
        # Bonus por aumentar entropia (diversidade)
        return estado_percebido['entropia'] * 5.0

    # ─── Ciclo Principal ────────────────────────────────────

    def ciclo(self, tema: str, world_state: dict = None,
              max_entidades: int = 5) -> dict:
        """Um ciclo completo do Motor de Mundo Markoviano.
        
        Fluxo:
        1. Perceber estado atual do world_state
        2. Calcular entropia
        3. Decidir acao (EXPANDIR/CONECTAR/EQUILIBRAR/EVOLUIR)
        4. Executar acao
        5. Autoavaliar e aprender
        
        Args:
            tema: tema do mundo
            world_state: estado atual (se None, carrega do disco)
            max_entidades: maximo de entidades a criar neste ciclo
        
        Returns:
            relatorio do ciclo
        """
        from mcr.mcr_world_state import _carregar

        print('\n' + '=' * 55)
        print('  MCRWorldSystem — CICLO')
        print('  Tema: %s' % tema)
        print('=' * 55)

        t_inicio = time.time()
        estado_acumulado = world_state or _carregar()
        pending_names = set()
        relatorio = {
            'tema': tema,
            'ciclo_inicio': time.strftime('%Y-%m-%d %H:%M:%S'),
            'entidades_criadas': 0,
            'tiers': {},
            'acoes': [],
        }

        entidades_criadas = 0
        tiers_count = {}

        while entidades_criadas < max_entidades:
            # 1. Perceber
            estado_percebido = self._perceber_estado(estado_acumulado)
            print('\n--- Entidade %d/%d ---' % (entidades_criadas + 1, max_entidades))
            print('  Estado: entropia=%.2f, npcs=%d, quests=%d' % (
                estado_percebido['entropia'],
                estado_percebido['total_npcs'],
                estado_percebido['total_quests']))

            # 2 & 3. Decidir acao
            acao = self._decidir_acao(estado_percebido)

            # 4. Executar (dispatch via dict, sem if/elif)
            resultado = {'sucesso': False}
            handler = {
                'EXPANDIR': self._executar_expandir,
                'CONECTAR': self._executar_conectar,
                'EQUILIBRAR': self._executar_equilibrar,
            }.get(acao)
            if handler:
                resultado = handler(
                    tema, estado_percebido, estado_acumulado, pending_names)

            resultado['acao'] = acao
            relatorio['acoes'].append({
                'acao': acao,
                'entropia': estado_percebido['entropia'],
                'sucesso': resultado.get('sucesso', False),
                'entidade': resultado.get('entidade', ''),
                'tier': resultado.get('tier', ''),
                'erro': resultado.get('erro', ''),
            })

            if resultado.get('sucesso'):
                entidades_criadas += 1
                tier = resultado.get('tier', 'desconhecido')
                tiers_count[tier] = tiers_count.get(tier, 0) + 1
                print('  >> CRIADO: %s [%s]' % (resultado.get('entidade', '?'), tier))

                # Registra PONTE_OTIMA se disponivel
                if resultado.get('arquivo') and '.lua' in str(resultado.get('arquivo', '')):
                    try:
                        arquivo_path = str(resultado['arquivo'])
                        if 'salvo em:' in arquivo_path:
                            arquivo_path = arquivo_path.split('salvo em: ')[-1].strip()
                        with open(arquivo_path, 'r', encoding='latin-1') as _f:
                            _codigo = _f.read()
                        _linhas = _codigo.count('\n') + 1
                        # Estima PONTE_OTIMA baseada no tamanho
                        _nota = min(10.0, _linhas * 0.15)
                        self._ultimas_notas_ponte.append(_nota)
                    except Exception:
                        pass

                # 5. EVOLUIR apos cada sucesso
                self._executar_evoluir(
                    tema, estado_percebido, estado_acumulado, resultado)
            else:
                print('  >> FALHA: %s' % resultado.get('erro', '?'))
                # Evita loop infinito em falha
                if 'metacognicao' in str(resultado.get('erro', '')):
                    self._threshold_metacog = min(0.90, self._threshold_metacog + 0.03)
                # Se CONECTAR falhou, tenta EXPANDIR
                if acao == 'CONECTAR':
                    resultado2 = self._executar_expandir(
                        tema, estado_percebido, estado_acumulado, pending_names)
                    if resultado2.get('sucesso'):
                        entidades_criadas += 1
                        tier2 = resultado2.get('tier', 'desconhecido')
                        tiers_count[tier2] = tiers_count.get(tier2, 0) + 1
                        print('  >> CRIADO (fallback): %s [%s]' % (
                            resultado2.get('entidade', '?'), tier2))
                        relatorio['acoes'].append({
                            'acao': 'EXPANDIR_FALLBACK',
                            'entropia': estado_percebido['entropia'],
                            'sucesso': True,
                            'entidade': resultado2.get('entidade', ''),
                            'tier': tier2,
                        })
                        self._executar_evoluir(
                            tema, estado_percebido, estado_acumulado, resultado2)

            time.sleep(0.5)

        # Autoavaliacao final
        estado_final = self._perceber_estado(estado_acumulado)
        nota_ciclo = estado_final['entropia'] * 5.0

        print('\n' + '=' * 55)
        print('  CICLO CONCLUIDO')
        print('=' * 55)
        print('  Entidades criadas: %d/%d' % (entidades_criadas, max_entidades))
        print('  Tiers: %s' % ', '.join('%s=%d' % (k, v) for k, v in tiers_count.items() if v > 0))
        print('  Entropia final: %.2f' % estado_final['entropia'])
        print('  Nota do ciclo: %.1f' % nota_ciclo)
        print('  Threshold metacog: %.2f' % self._threshold_metacog)
        print('  Transicoes aprendidas: %d' % len(self.mcr_transicoes.transicoes))
        print('  Tempo: %.1fs' % (time.time() - t_inicio))
        print('=' * 55)

        relatorio['entidades_criadas'] = entidades_criadas
        relatorio['tiers'] = tiers_count
        relatorio['entropia_final'] = round(estado_final['entropia'], 3)
        relatorio['nota_ciclo'] = round(nota_ciclo, 1)
        relatorio['threshold_metacog'] = self._threshold_metacog
        relatorio['tempo_total'] = round(time.time() - t_inicio, 1)
        return relatorio

    # ─── Modo Daemon (reacao a eventos externos) ────────────

    def perceber_perturbacao(self, perturbacao: dict) -> dict:
        """Recebe uma perturbacao externa (evento do servidor) e reage.
        
        Fluxo:
        1. Le o world_state atual do disco
        2. Calcula entropia antes e depois da perturbacao
        3. Se delta_h > threshold, decide acao compensatoria
        4. Executa compensacao (reposicao, vinganca, guardiao)
        5. Atualiza world_state e aprende transicao
        
        Args:
            perturbacao: dict com delta_h, trigger_event, batch_size
        
        Returns:
            dict com resultado da compensacao
        """
        from mcr.mcr_world_state import _carregar, salvar_foundation

        delta_h = perturbacao.get('delta_h', 0.0)
        evento_gatilho = perturbacao.get('trigger_event', {})
        tipo_evento = evento_gatilho.get('type', '')
        target = evento_gatilho.get('target', '')
        killer = evento_gatilho.get('killer', '')

        print('\n' + '=' * 55)
        print('  PERTURBACAO DETECTADA')
        print('  Evento: %s | Target: %s | Killer: %s' % (tipo_evento, target, killer))
        print('  Delta H: %.2f' % delta_h)
        print('=' * 55)

        # Carrega estado atual
        estado_atual = _carregar()

        # Se for morte de um NPC registrado, marca como dead
        if tipo_evento in ('death', 'kill') and target:
            for nome_npc, dados in estado_atual.get('npcs', {}).items():
                if target.lower() in nome_npc.lower():
                    dados['state'] = 'dead'
                    print('  NPC %s marcado como dead' % nome_npc)
                    break

        # Salva estado atualizado
        if estado_atual.get('current_foundation'):
            salvar_foundation(estado_atual.get('current_foundation', {}))

        # Reage baseado no delta_h
        if abs(delta_h) < 0.05:
            print('  Impacto irrelevante, ignorando.')
            return {'acao': 'ignorar', 'delta_h': delta_h}

        acao = 'COMPENSAR'
        resultado = {'acao': acao}

        # Morte de NPC unico → reposicao (EXPANDIR)
        if delta_h < -0.1:
            if target and not target.startswith('NPC_'):
                print('  Morte de NPC unico detectada. Repondo...')
                resultado_acao = self._executar_compensar_repor(
                    target, estado_atual, killer)
                resultado.update(resultado_acao)
            else:
                print('  Morte de entidade generica. Ignorando reposicao.')
                resultado['sub_acao'] = 'ignorar'

        # Se morreu algo que afeta quests → quest de vinganca (CONECTAR)
        if delta_h < -0.05 and abs(delta_h) >= 0.05:
            # Cria quest de vinganca no killer
            if killer and killer != 'environment' and not killer.startswith('NPC_'):
                print('  Criando quest de vinganca contra %s...' % killer)
                from mcr.mcr_world_builder import expandir_npc
                # Pega um NPC aleatorio para dar a quest
                npcs_vivos = [n for n, d in estado_atual.get('npcs', {}).items()
                              if d.get('state', 'alive') == 'alive']
                if npcs_vivos:
                    giver = npcs_vivos[0]
                    instrucao = (
                        "Adicione uma quest ao NPC '%s'. "
                        "Titulo: Vinganca por %s. "
                        "Objetivo: Vingar a morte de %s, morto por %s. "
                        "Recompensa: Moedas de ouro e reputacao." % (
                            giver, target, target, killer))
                    try:
                        resultado_q = expandir_npc(giver, instrucao)
                        if resultado_q.get('sucesso'):
                            print('  >> Quest de vinganca injetada em %s' % giver)
                            resultado['sub_acao'] = 'vinganca'
                            resultado['quest_giver'] = giver
                    except Exception as e:
                        print('  >> Falha ao criar quest: %s' % e)

        # Aprende a transicao
        codigo = "perturb:h:%.2f,tipo:%s" % (delta_h, tipo_evento)
        self.mcr_transicoes.aprender(codigo, acao)
        for _ in range(2):
            self.mcr_transicoes.aprender(codigo, acao)

        return resultado

    def _executar_compensar_repor(self, target: str, estado: dict,
                                    killer: str = '') -> dict:
        """Compensacao: repoe um NPC que morreu via template."""
        from mcr.golden_templates import gerar_npc_canary, salvar_npc_parametrizado
        from mcr.mcr_world_builder import _validar_sintaxe, _validar_semantica
        from mcr.mcr_world_state import registrar_entidade
        import re as _re

        params = {
            'name': target.replace(' ', '_') + '_II',
            'health': 100,
            'looktype': 128,
            'greeting': 'Ouvi dizer que meu antecessor caiu. Estou aqui para continuar.',
            'job_desc': 'Sou o novo substituto.',
        }

        codigo = gerar_npc_canary(params)
        valido, _ = _validar_sintaxe(codigo)
        apis = _validar_semantica(codigo, 'npc')

        if valido and not apis:
            resultado_msg = salvar_npc_parametrizado(params)
            nome_arquivo = _re.sub(r'[^a-z0-9_]', '',
                                   params['name'].lower().replace(' ', '_')) + '.lua'
            caminho = os.path.join(_BASE, 'server', 'data-otservbr-global', 'npc', nome_arquivo)
            registrar_entidade('npc', params['name'], {
                'file': caminho, 'role': '',
                'tier': 'reposicao',
                'quests': [],
                'replaces': target,
            })
            print('  >> Reposto: %s como %s' % (target, params['name']))
            return {'sub_acao': 'reposicao', 'entidade': params['name'],
                    'arquivo': resultado_msg}

        return {'sub_acao': 'reposicao_falhou', 'erro': 'template_invalido'}

    def modo_daemon(self, tema: str = 'Mundo Vivo'):
        """Modo continuo: observa eventos e reage em loop.
        
        Inicia o WorldObserver em background e fica em loop
        principal dormindo, deixando o observer reagir.
        
        Pressione Ctrl+C para parar.
        """
        from mcr.world_observer import WorldObserver

        observer = WorldObserver(world_system=self)
        observer.iniciar()

        print('\n' + '=' * 55)
        print('  MCRWorldSystem — MODO DAEMON')
        print('  Tema: %s' % tema)
        print('  Observando eventos do servidor...')
        print('  Pressione Ctrl+C para parar.')
        print('=' * 55)

        try:
            while True:
                estatisticas = observer.get_estatisticas()
                if estatisticas['total_eventos'] > 0:
                    print('\r[Daemon] Eventos: %d | Ultima reacao: %.1fs atras' % (
                        estatisticas['total_eventos'],
                        estatisticas['cooldown_restante']), end='')
                time.sleep(5)
        except KeyboardInterrupt:
            print('\n[Daemon] Ctrl+C recebido. Parando...')
        finally:
            observer.parar()
            print('[Daemon] Modo daemon encerrado.')
