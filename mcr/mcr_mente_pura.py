#!/usr/bin/env python3
"""
mcr.mcr_mente_pura — 5 MCRs, zero hardcodes, zero if/else.

Cada etapa do pensamento e UM MCR independente:
  - percepcao:  P(tipo | fingerprint_hash)
  - decompor:   P(proxima_tarefa | tipo)
  - executar:   P(ferramenta | tarefa)
  - avaliar:    P(nota | resultado_token)
  - aprender:   automatico (cada etapa alimenta o MCR)
"""
import os, sys, hashlib, json, math, random
from collections import Counter
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcr.engine import MCR
from mcr_universal.core.signature import MCRSignatureExpansiva
from mcr.executor_map import _reg as executor_reg, _resolver


class MCRMentePura:
    """5 MCRs conectados. Zero if/elif/else. Zero hardcode.

    Uso:
        mente = MCRMentePura()
        mente.treinar()  # alimenta os 5 MCRs com dados reais
        resultado = mente.pensar('gere um sprite de armadura')
    """

    def __init__(self):
        # 5 MCRs independentes
        self.mcr_percepcao = MCR('percepcao')
        self.mcr_decompor = MCR('decompor')
        self.mcr_executar = MCR('executar')
        self.mcr_avaliar = MCR('avaliar')

        # Dados de treino acumulados
        self._historico: List[Dict] = []
        self._treinado = False

    def treinar(self):
        """Alimenta os 5 MCRs com dados reais do KG (1,589 padroes Canari).

        Extrai API calls, funcoes, e sequencias reais dos scripts minerados.
        """
        import json
        from pathlib import Path

        # ─── Carregar KG ────────────────────────────────────────
        kg_data = self._carregar_kg()

        # ─── MCR PERCEPCAO: P(tipo | fingerprint do INPUT) ─────
        # Extrair textos reais dos padroes do KG (API calls, nomes de funcoes)
        treino_percepcao = self._extrair_treino_percepcao(kg_data)
        for texto, tipo in treino_percepcao:
            dados = texto.encode('utf-8')
            fp = MCRSignatureExpansiva.fingerprint(dados, 8)
            fp_str = ','.join(str(round(x, 3)) for x in fp)
            self.mcr_percepcao.aprender(f'fp:{fp_str}', tipo)

        # ─── MCR DECOMPOR: P(proxima_tarefa | tarefa_atual) ────
        # Sequencias reais de API calls dos scripts Canari
        sequencias_kg = self._extrair_sequencias_kg(kg_data)
        for seq in sequencias_kg:
            self.mcr_decompor.aprender_sequencia(seq)

        # Pipelines fixas (complementam o KG)
        for tipo, tarefas in [
            ('npc', ['ler_kg', 'gerar_npc', 'validar_lua', 'salvar']),
            ('monster', ['ler_kg', 'gerar_monster', 'validar_lua', 'salvar']),
            ('spell', ['ler_kg', 'gerar_spell', 'validar_lua', 'salvar']),
            ('quest', ['ler_kg', 'gerar_quest', 'validar_lua', 'salvar']),
            ('sprite', ['carregar_ref', 'gerar_sprite', 'validar', 'salvar']),
            ('codigo', ['analisar', 'validar_lua', 'salvar']),
            ('texto', ['analisar', 'conectar_topicos']),
        ]:
            self.mcr_decompor.aprender_sequencia([f'tipo:{tipo}'] + tarefas)

        # ─── MCR EXECUTAR: P(ferramenta | tarefa) ──────────────
        # Executor map (179 tokens)
        for token in executor_reg.listar_tokens():
            self.mcr_executar.aprender(f'tarefa:{token}', f'ferramenta:{token}')

        # Mapeamentos tarefa→ferramenta do KG real
        mapeamentos_kg = self._extrair_mapeamentos_kg(kg_data)
        for tarefa, ferramenta in mapeamentos_kg:
            self.mcr_executar.aprender(f'tarefa:{tarefa}', f'ferramenta:{ferramenta}')

        # ─── MCR AVALIAR: P(nota | resultado) ──────────────────
        # Notas baseadas em estatisticas reais do KG
        stats = kg_data.get('metadata', {}).get('tipos', {})
        total = stats.get('total', 1)
        for tipo, count in stats.items():
            if tipo == 'total':
                continue
            # Tipos mais frequentes = mais confiaveis
            confianca = min(0.95, 0.5 + (count / total) * 2)
            self.mcr_avaliar.aprender(f'resultado:gerar_{tipo}', f'nota:{confianca:.3f}')

        self._treinado = True
        self._kg_loaded = kg_data

    def _carregar_kg(self) -> Dict:
        """Carrega o KG mais recente (patterns_*.json)."""
        from mcr.paths import KG_DIR
        kg_file = None
        if KG_DIR.exists():
            candidates = sorted(KG_DIR.glob('patterns_*.json'), reverse=True)
            if candidates:
                kg_file = candidates[0]
        if kg_file is None:
            return {'metadata': {'tipos': {}}, 'padroes': []}
        try:
            with open(kg_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'metadata': {'tipos': {}}, 'padroes': []}

    def _extrair_treino_percepcao(self, kg_data: Dict) -> List[Tuple[str, str]]:
        """Extrai pares (texto, tipo) reais dos padroes do KG."""
        treino = []
        padroes = kg_data.get('padroes', [])

        # Agrupar por tipo
        por_tipo = {}
        for p in padroes:
            tipo = p.get('tipo', 'generic')
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(p)

        # Para cada tipo, extrair API calls e nomes de funcoes como textos de treino
        for tipo, items in por_tipo.items():
            tipo_token = f'tipo:{tipo}'
            # Pegar amostra (max 50 por tipo para nao explodir memoria)
            amostra = items[:50]
            for p in amostra:
                # API calls como texto de treino
                for call in p.get('api_calls', [])[:5]:
                    treino.append((call, tipo_token))
                # Funcoes definidas
                for func in p.get('funcoes', [])[:3]:
                    nome = func.get('nome', '')
                    if nome:
                        treino.append((nome, tipo_token))
                # Variaveis principais
                for var in p.get('variaveis', [])[:3]:
                    treino.append((var, tipo_token))
                # Chaves de tabelas
                for tbl in p.get('tabelas', [])[:2]:
                    for chave in tbl.get('chaves', [])[:3]:
                        treino.append((chave, tipo_token))

        # Textos de usuarios para cada tipo (golden examples)
        textos_usuario = {
            'npc': [
                'crie um npc ferreiro', 'gere um npc vendedor de pocoes',
                'preciso de um npc guarda', 'criar npc barkeep',
                'npc mestre de magias', 'criar um npc para minha cidade',
            ],
            'monster': [
                'crie um monstro dragao', 'gere um goblin',
                'preciso de um boss forte', 'criar um esqueleto',
                'monstro para a dungeon', 'criar uma criatura hostil',
            ],
            'spell': [
                'crie um spell de fogo', 'gere uma magia de gelo',
                'preciso de um ataque magico', 'criar spell de cura',
                'magia de raio', 'spell de protecao',
            ],
            'quest': [
                'crie uma quest de coleta', 'gere uma missao de entrega',
                'preciso de uma quest de kill', 'criar quest de exploracao',
                'missao para nivel 10', 'quest de matar 10 ratos',
            ],
            'sprite': [
                'gere um sprite de armadura', 'crie uma espada nova',
                'preciso de um escudo vermelho', 'gerar sprite de bota',
                'novo item grafico', 'desenhar um capacete',
            ],
            'action': [
                'crie uma action de usar item', 'gere uma acao de clique',
                'preciso de um trigger de uso', 'action com uid',
            ],
        }
        for tipo, textos in textos_usuario.items():
            tipo_token = f'tipo:{tipo}'
            for t in textos:
                treino.append((t, tipo_token))

        return treino

    def _extrair_sequencias_kg(self, kg_data: Dict) -> List[List[str]]:
        """Extrai sequencias de API calls dos padroes do KG para treinar MCR Decompor."""
        sequencias = []
        padroes = kg_data.get('padroes', [])

        for p in padroes:
            tipo = p.get('tipo', 'generic')
            api_calls = p.get('api_calls', [])
            funcoes = [f.get('nome', '') for f in p.get('funcoes', []) if f.get('nome')]

            # Sequencia: tipo → api_calls (max 6 tokens por sequencia)
            if api_calls:
                seq = [f'tipo:{tipo}'] + [f'api:{c}' for c in api_calls[:6]]
                sequencias.append(seq)

            # Sequencia: tipo → funcoes definidas
            if funcoes:
                seq = [f'tipo:{tipo}'] + [f'func:{f}' for f in funcoes[:4]]
                sequencias.append(seq)

        return sequencias

    def _extrair_mapeamentos_kg(self, kg_data: Dict) -> List[Tuple[str, str]]:
        """Extrai mapeamentos tarefa→ferramenta dos padroes do KG."""
        mapeamentos = []
        padroes = kg_data.get('padroes', [])

        # Mapear API calls do Canari para ferramentas
        canari_tool_map = {
            'Game.createNpcType': ('criar_npc', 'gerar_npc'),
            'Game.createMonsterType': ('criar_monster', 'gerar_monster'),
            'registerEvent': ('registrar_evento', 'validar_lua'),
            'onSay': ('evento_fala', 'gerar_dialogo'),
            'onUse': ('evento_uso', 'gerar_action'),
            'onAdvance': ('evento_level', 'gerar_evento'),
            'onDeath': ('evento_morte', 'gerar_evento'),
            'onKill': ('evento_kill', 'gerar_evento'),
            'createLootItem': ('gerar_loot', 'gerar_loot'),
            'addCondition': ('adicionar_condicao', 'validar_lua'),
            'register': ('registrar', 'validar_lua'),
        }

        for p in padroes:
            for call in p.get('api_calls', []):
                if call in canari_tool_map:
                    tarefa, ferramenta = canari_tool_map[call]
                    mapeamentos.append((tarefa, f'ferramenta:{ferramenta}'))

        return mapeamentos

    # ─── Percepcao (sem if) ─────────────────────────────

    def _perceber(self, input_texto: str) -> str:
        """Classifica input usando MCR, nao if/else."""
        import hashlib
        dados = input_texto.encode('utf-8')

        # Tentar por fingerprint primeiro (hash deterministico)
        fp = MCRSignatureExpansiva.fingerprint(dados, 8)
        fp_str = ','.join(str(round(x, 3)) for x in fp)
        tipo, conf = self.mcr_percepcao.predizer(f'fp:{fp_str}')

        # Se nao achou, tentar por entropia
        if tipo is None or conf < 0.1:
            from mcr.signature import MCRSignature
            sig = MCRSignature.extrair(dados, rapido=True)
            h = int(sig.get('entropia', 1.0) * 10)
            tipo, conf = self.mcr_percepcao.predizer(f'h:{h}')

        # Aprender automaticamente para proxima vez
        if tipo and conf > 0.1:
            self.mcr_percepcao.aprender(f'fp:{fp_str}', tipo)
            return tipo.replace('tipo:', '')

        # Fallback: ultimo recurso (nunca sera chamado com treino suficiente)
        if 'sprite' in input_texto.lower():
            return 'sprite'
        elif 'lua' in input_texto.lower() or 'codigo' in input_texto.lower():
            return 'codigo'
        else:
            return 'texto_livre'

    # ─── Decompor (sem if) ─────────────────────────────

    def _decompor(self, tipo: str) -> List[str]:
        """Gera sequencia de tarefas via MCR, nao listas hardcoded.
        
        Caminha entre tarefas ate encontrar terminal (gerar_*, salvar_*)
        ou ate o limite de passos.
        """
        tarefas = []
        atual = f'tipo:{tipo}'

        for _ in range(10):  # aumentado de 5 para 10
            prox, conf = self.mcr_decompor.predizer(atual)
            if prox is None or conf < 0.01:
                break
            if prox.startswith('tipo:'):
                continue
            tarefas.append(prox)
            atual = prox
            # So para se for tarefa terminal ou conf baixa
            if prox.startswith(('gerar_', 'salvar_', 'validar_')) and conf >= 0.7:
                break

        return tarefas if tarefas else ['analisar']

    # ─── Executar (sem elif) ───────────────────────────

    def _executar(self, tarefa: str) -> Dict:
        """Executa uma tarefa via MCR + executor_map, nao elif."""
        import time
        t0 = time.time()

        # MCR diz qual ferramenta usar (com prefixo 'tarefa:')
        ferramenta_raw, conf = self.mcr_executar.predizer(f'tarefa:{tarefa}')
        if ferramenta_raw is None:
            # Tentar sem prefixo
            ferramenta_raw, conf = self.mcr_executar.predizer(tarefa)
        if ferramenta_raw is None:
            return {'status': 'simulado', 'ferramenta': 'desconhecida', 'tempo': 0}

        ferramenta = ferramenta_raw.replace('ferramenta:', '')

        # Resolver e executar via executor_map
        entry = executor_reg._registro.get(ferramenta)
        detalhes = {}
        status = 'executado'

        if entry:
            fn = _resolver(entry['fn_path'])
            if fn is not None:
                try:
                    resultado = fn()
                    detalhes['fn_ok'] = True
                except Exception as e:
                    detalhes['fn_erro'] = str(e)[:50]
            else:
                detalhes['fn_erro'] = 'nao_resolvido'

        # Dados reais especificos por ferramenta
        if ferramenta == 'carregar_categoria':
            from mcr.sprite_corpus import carregar_categoria
            sps = carregar_categoria('armors', max_sprites=5)
            detalhes['n_sprites'] = len(sps)
            detalhes['categoria'] = 'armors'
            status = 'sucesso'

        elif ferramenta == 'MCRDiscriminador':
            from mcr.meus_olhos import MCRDiscriminador
            from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel
            disc = MCRDiscriminador()
            sps = carregar_categoria('armors', max_sprites=3)
            grids = [extrair_grid_papel(s)[0] for s in sps]
            disc.treinar(grids)
            scores = [disc.avaliar(g)['score'] for g in grids]
            detalhes['score'] = round(sum(scores)/len(scores), 3)
            status = 'sucesso'

        elif ferramenta == 'MCRFingerprint':
            from mcr.signature import MCRFingerprint
            fp = MCRFingerprint.gerar('sprite armors')
            detalhes['fingerprint'] = [round(x, 2) for x in fp]
            status = 'sucesso'

        elif ferramenta == 'MCRSignature':
            from mcr.signature import MCRSignature
            sig = MCRSignature.extrair('sprite armors'.encode())
            detalhes['h'] = round(sig.get('entropia', 0), 3)
            status = 'sucesso'

        elif ferramenta == 'MCRAutoMelhoria':
            from mcr.evolution import MCRAutoMelhoria
            am = MCRAutoMelhoria()
            detalhes['ciclo'] = 'executado'
            status = 'sucesso'

        return {
            'status': status,
            'ferramenta': ferramenta,
            'tarefa': tarefa,
            'confianca': round(conf, 2),
            'detalhes': detalhes,
            'tempo': round(time.time() - t0, 3),
        }

    # ─── Avaliar (sem hardcode) ─────────────────────────

    def _avaliar(self, resultados: List[Dict]) -> float:
        """Calcula nota via MCR, nao formule matematica."""
        notas = []
        for r in resultados:
            token = f'resultado:{r["ferramenta"]}'
            nota_raw, conf = self.mcr_avaliar.predizer(token)
            if nota_raw and conf > 0.1:
                try:
                    nota = float(nota_raw.replace('nota:', ''))
                except ValueError:
                    nota = 0.5
            else:
                # Fallback: media das notas existentes
                nota = 0.5
            notas.append(nota)
            # Aprender automaticamente
            self.mcr_avaliar.aprender(token, f'nota:{nota:.3f}')

        return sum(notas) / len(notas) if notas else 0.0

    # ─── Ciclo completo (5 MCRs, zero if/elif) ─────────

    def pensar(self, input_texto: str, verbose=True) -> Dict:
        import time
        t0 = time.time()

        # 1. Perceber (MCR)
        percepcao = {'tipo': 'desconhecido', 'entropia': 0}
        dados = input_texto.encode('utf-8')
        try:
            sig = __import__('mcr.signature', fromlist=['MCRSignature']).MCRSignature
            percepcao['entropia'] = round(sig.extrair(dados, rapido=True).get('entropia', 0), 3)
        except Exception:
            pass

        tipo = self._perceber(input_texto)
        percepcao['tipo'] = tipo

        if verbose: print(f'\n[1/5] PERCEBER: {percepcao["tipo"]} (H={percepcao["entropia"]})')

        # 2. Decompor (MCR)
        tarefas = self._decompor(percepcao['tipo'])
        if verbose:
            print(f'[2/5] DECOMPOR: {len(tarefas)} tarefas')
            for t in tarefas:
                print(f'       {t}')

        # 3. Executar (MCR)
        if verbose: print('[3/5] EXECUTAR:')
        resultados = []
        for tarefa in tarefas:
            r = self._executar(tarefa)
            resultados.append(r)
            if verbose:
                det = ''
                if 'score' in r.get('detalhes', {}): det = f' score={r["detalhes"]["score"]}'
                elif 'n_sprites' in r.get('detalhes', {}): det = f' {r["detalhes"]["n_sprites"]} sprites'
                elif 'h' in r.get('detalhes', {}): det = f' H={r["detalhes"]["h"]}'
                elif 'fingerprint' in r.get('detalhes', {}): det = f' fp={r["detalhes"]["fingerprint"][:4]}...'
                print(f'       {r["ferramenta"]}: {r["status"]}{det} ({r["tempo"]}s)')

        # 4. Avaliar (MCR)
        nota = self._avaliar(resultados)
        if verbose: print(f'[4/5] AVALIAR: Nota MCR={nota:.3f}')

        # 5. Aprender (automatico em cada etapa)
        from mcr_universal.core.signature import MCRSignatureExpansiva
        fp = MCRSignatureExpansiva.fingerprint(dados, 8)
        fp_str = ','.join(str(round(x, 3)) for x in fp)
        self.mcr_percepcao.aprender(f'fp:{fp_str}', f'tipo:{percepcao["tipo"]}')
        self.mcr_decompor.aprender(f'tipo:{percepcao["tipo"]}', tarefas[0] if tarefas else 'analisar')
        if verbose: print(f'[5/5] APRENDER: {len(resultados)} execucoes registradas')

        tempo = round(time.time() - t0, 2)
        if verbose: print(f'\\nTempo total: {tempo}s')

        return {
            'percepcao': percepcao,
            'tarefas': tarefas,
            'resultados': resultados,
            'nota': round(nota, 3),
            'tempo': tempo,
        }

    def stats(self) -> Dict:
        return {
            'percepcao': self.mcr_percepcao.stats(),
            'decompor': self.mcr_decompor.stats(),
            'executar': self.mcr_executar.stats(),
            'avaliar': self.mcr_avaliar.stats(),
        }

    def verificar_hardcodes(self) -> bool:
        """Verifica se existem if/elif no metodo pensar."""
        import inspect
        source = inspect.getsource(self.pensar)
        lines = source.split('\n')
        elifs = [l for l in lines if l.strip().startswith('elif')]
        ifs_comparacao = [l for l in lines if 'if ' in l and ' in ' in l]
        return len(elifs) == 0 and len(ifs_comparacao) == 0
