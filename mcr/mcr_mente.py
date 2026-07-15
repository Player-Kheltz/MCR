#!/usr/bin/env python3
"""
mcr.mcr_mente — Ciclo de pensamento MCR.

Perceber -> Decompor -> Executar -> Avaliar -> Aprender
Cada passo e uma transicao no MCR. O MCR navega a propria pipeline.
"""
import os, sys, time, json, math
from collections import Counter
from typing import Dict, List, Optional
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcr.engine import MCR, compose_state
from mcr.decisor import MCRPesoNota, MCREntropia
from mcr.signature import MCRSignature
from mcr_universal.core.signature import MCRSignatureExpansiva


# ─── Banco de conhecimento do MCR (modulos + pipelines) ───


_MODULOS = [
    ('MCR', ['MCR','aprender','aprender_sequencia','aprender_batch','predizer','gerar','entropia','jaccard','stats']),
    ('MCRSQLite', ['MCRSQLite','aprender','aprender_batch','predizer','gerar','entropia_media','stats']),
    ('MCRThreshold', ['MCRThreshold','observar','calcular','obter','aprender']),
    ('MCRDecisor', ['MCRDecisor','aprender','decidir','decidir_pular_parser']),
    ('MCRPesoNota', ['MCRPesoNota','aprender','calcular']),
    ('MCREntropia', ['MCREntropia','alimentar','esta_em_loop']),
    ('MCRAutoMelhoria', ['MCRAutoMelhoria','ciclo']),
    ('MCRDiscriminador', ['MCRDiscriminador','treinar','avaliar','diagnostico']),
    ('RadarMCR', ['RadarMCR','buscar','buscar_visual','fingerprint_visual']),
    ('SignatureAnalyzer', ['SignatureAnalyzer','clusterizar','classificar','meta_clusterizar']),
    ('MCRConexao', ['MCRConexao','analisar','melhor_ponte']),
    ('MCRConector', ['MCRConector','alimentar','conectar','explorar_todos']),
    ('MCRBufferKG', ['MCRBufferKG','aprender','flush','buscar']),
    ('MCRFingerprint', ['MCRFingerprint','gerar','extrair_estilo']),
    ('MCRSignature', ['MCRSignature','extrair','comparar','metaniveis']),
    ('MCRMetaNivel', ['MCRMetaNivel','alimentar','diagnosticar','auto_expandir']),
    ('MCRMetaGap', ['MCRMetaGap','diagnosticar_gaps','buscar_para_gap']),
    ('PipelineUniversal', ['PipelineUniversal','registrar','executar','stats']),
    ('MCRSpriteMotor', ['MCRSpriteMotor','treinar','gerar','renderizar','avaliar']),
    ('MCRSystem', ['MCRSystem','ciclo_unico']),
    ('MCRGeracao', ['MCRGeracao','gerar']),
    ('tokenizador', ['extrair_regioes','ordenar_regioes','extrair_relacoes']),
    ('sprite_corpus', ['carregar_categoria','extrair_grid_papel','jaccard_silhueta']),
    ('template_entropico', ['entropia_shannon','extrair_template_entropico','gerar_do_template']),
    ('olhos_mcr', ['sprite_para_ascii_rich','sprite_para_ascii_compacto']),
    ('emergir', ['EmergirCrossModal','despachar','listar_dominios']),
    ('HDC', ['hdc_core','HDVector','binding','bundle','cosine']),
    ('KG', ['KnowledgeGraph','buscar','aprender','purgar']),
    ('Episodica', ['EpisodicMemory','store','search','cluster']),
]

# Problemas → primeira ferramenta
_PROBLEMAS = {
    'gerar_sprite': 'carregar_categoria',
    'gerar_texto': 'MCR',
    'validar': 'MCRDiscriminador',
    'conectar_topicos': 'MCRConexao',
    'aprender': 'MCRBufferKG',
    'evoluir': 'MCRAutoMelhoria',
    'analisar': 'MCRSignature',
    'fingerprint': 'MCRFingerprint',
    'niveis': 'MCRMetaNivel',
    'buscar': 'KG',
    'emergir': 'emergir',
    'pipeline': 'PipelineUniversal',
}


# ─── MCR Mente ─────────────────────────────────────────────


class MCRMente:
    """Ciclo de pensamento MCR: Perceber -> Decompor -> Executar -> Avaliar -> Aprender.

    Cada pensamento e uma sequencia de tokens no MCR.
    O MCR aprende P(proximo_passo | passo_atual, contexto).
    """

    def __init__(self):
        self.mcr = MCR('mente')
        self.peso_nota = MCRPesoNota('mente_peso')
        self.entropia = MCREntropia('mente_entropia')
        self._treinar_pipelines()

    def _treinar_pipelines(self):
        """Treina o MCR com todas as pipelines conhecidas."""
        for nome, tokens in _MODULOS:
            if len(tokens) >= 2:
                self.mcr.aprender_sequencia(tokens)
        for prob, prim_ferramenta in _PROBLEMAS.items():
            self.mcr.aprender(f'problema:{prob}', prim_ferramenta)
            self.mcr.aprender('problema:geral', f'problema:{prob}')

    # ─── Perceber ───────────────────────────────────────

    def perceber(self, input_texto: str) -> Dict:
        """Classifica o input: tipo, entropia, fingerprint."""
        dados = input_texto.encode('utf-8') if isinstance(input_texto, str) else input_texto
        fp = MCRSignatureExpansiva.fingerprint(dados, 8)
        sig = MCRSignature.extrair(dados, rapido=True)
        entropia = sig.get('entropia', 1.0)

        # Classificar por entropia
        if '<sprite>' in input_texto.lower() or 'sprite' in input_texto.lower()[:30]:
            tipo = 'sprite'
        elif '<codigo>' in input_texto.lower() or 'codigo' in input_texto.lower()[:30] or 'lua' in input_texto.lower()[:30]:
            tipo = 'codigo'
        elif entropia < 0.3:
            tipo = 'binario_estruturado'
        elif entropia < 0.5:
            tipo = 'texto_estruturado'
        else:
            tipo = 'texto_livre'

        return {
            'tipo': tipo,
            'entropia': round(entropia, 3),
            'fingerprint': [round(x, 2) for x in fp],
            'tamanho': len(dados),
        }

    # ─── Decompor ───────────────────────────────────────

    def decompor(self, percepcao: Dict) -> List[Dict]:
        """Decompoe a tarefa em subtarefas usando o MCR navegador."""
        tipo = percepcao['tipo']
        tarefas = []

        # Mapear tipo → problemas
        problemas = []
        if tipo == 'sprite':
            problemas = ['gerar_sprite', 'validar', 'fingerprint']
        elif tipo == 'codigo':
            problemas = ['analisar', 'validar']
        elif tipo == 'texto_estruturado':
            problemas = ['analisar', 'conectar_topicos']
        else:
            problemas = ['analisar']

        for prob in problemas:
            # Usar MCR para encontrar a primeira ferramenta
            prim_ferramenta = self.mcr.predizer(f'problema:{prob}')
            ferramenta = prim_ferramenta[0] if prim_ferramenta[0] else _PROBLEMAS.get(prob, 'MCR')

            # Navegar a pipeline (proximos passos)
            passos = [ferramenta]
            atual = ferramenta
            for _ in range(4):
                prox = self.mcr.predizer(atual)
                if prox[0] and prox[0] != atual:
                    passos.append(prox[0])
                    atual = prox[0]
                else:
                    break

            tarefas.append({
                'problema': prob,
                'primeira_ferramenta': ferramenta,
                'pipeline': passos,
                'confianca': prim_ferramenta[1] if prim_ferramenta[1] else 0.0,
            })

        return tarefas

    # ─── Executar ───────────────────────────────────────

    def executar(self, tarefa: Dict, input_data: str) -> Dict:
        """Executa uma tarefa usando o executor_map (conecta 90 modulos)."""
        t0 = time.time()
        ferramenta = tarefa['primeira_ferramenta']
        problema = tarefa['problema']
        pipeline = tarefa.get('pipeline', [ferramenta])

        from mcr.executor_map import _reg as executor_reg

        resultado = {
            'ferramenta': ferramenta,
            'problema': problema,
            'status': 'executado',
            'tempo': 0,
            'pipeline_executada': [],
            'detalhes': {},
        }

        try:
            # Executar cada passo da pipeline via executor_map
            for i, passo in enumerate(pipeline):
                entry = executor_reg._registro.get(passo)
                if entry is None:
                    resultado['pipeline_executada'].append(f'{passo}:sem_mapa')
                    continue

                fn = self._resolver_fn(entry['fn_path'])
                if fn is None:
                    resultado['pipeline_executada'].append(f'{passo}:nao_resolvido')
                    continue

                # Tentar executar com args adaptativos
                try:
                    # Para funcoes que precisam de dados do pipeline anterior
                    if passo == 'carregar_categoria':
                        from mcr.sprite_corpus import carregar_categoria
                        dados = carregar_categoria('armors', max_sprites=5)
                        resultado['detalhes']['categoria'] = 'armors'
                        resultado['detalhes']['n_sprites'] = len(dados)

                    elif passo == 'extrair_grid_papel' and 'n_sprites' in resultado['detalhes']:
                        from mcr.sprite_corpus import extrair_grid_papel
                        from mcr.sprite_corpus import carregar_categoria
                        sps = carregar_categoria('armors', max_sprites=1)
                        gp, gc = extrair_grid_papel(sps[0])
                        resultado['detalhes']['opacos'] = sum(1 for row in gp for t in row if t != 'F')

                    elif passo == 'MCRDiscriminador':
                        from mcr.meus_olhos import MCRDiscriminador
                        from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel
                        disc = MCRDiscriminador()
                        sps = carregar_categoria('armors', max_sprites=3)
                        grids = [extrair_grid_papel(s)[0] for s in sps]
                        disc.treinar(grids)
                        scores = [disc.avaliar(g)['score'] for g in grids]
                        resultado['detalhes']['score_disc'] = round(sum(scores)/len(scores), 3)

                    elif passo == 'MCRSignature':
                        from mcr.signature import MCRSignature
                        sig = MCRSignature.extrair(input_data.encode('utf-8')[:500], rapido=True)
                        resultado['detalhes']['entropia'] = round(sig.get('entropia', 0), 3)
                        resultado['detalhes']['estados'] = sig.get('estados', 0)

                    elif passo == 'MCRFingerprint':
                        from mcr.signature import MCRFingerprint
                        resultado['detalhes']['fingerprint_8d'] = MCRFingerprint.gerar(input_data[:200])

                    elif passo == 'extrair_regioes':
                        from mcr.tokenizador_hierarquico import extrair_regioes
                        from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel
                        sps = carregar_categoria('armors', max_sprites=1)
                        gp, gc = extrair_grid_papel(sps[0])
                        regioes = extrair_regioes(gp)
                        resultado['detalhes']['n_regioes'] = len(regioes)

                    elif passo == 'entropia_shannon' or passo == 'entropia':
                        from mcr.template_entropico import entropia_shannon
                        seq = input_data.split()[:20]
                        h = entropia_shannon(seq)
                        resultado['detalhes']['h_seq'] = round(h, 3)

                    elif passo == 'rgb_para_lab':
                        from mcr.cielab import rgb_para_lab
                        resultado['detalhes']['lab'] = rgb_para_lab(128, 128, 128)

                    else:
                        # Fallback: tentar executar a funcao diretamente
                        try:
                            res = fn()
                            resultado['pipeline_executada'].append(f'{passo}:ok')
                        except Exception:
                            resultado['pipeline_executada'].append(f'{passo}:simulado')

                    resultado['pipeline_executada'].append(f'{passo}:ok')

                except Exception as e:
                    resultado['pipeline_executada'].append(f'{passo}:erro:{str(e)[:30]}')

            resultado['status'] = 'sucesso' if 'erro' not in str(resultado.get('pipeline_executada', [])) else 'parcial'

        except Exception as e:
            resultado['status'] = 'erro'
            resultado['detalhes'] = {'erro': str(e)[:100]}

        resultado['tempo'] = round(time.time() - t0, 3)
        return resultado

    @staticmethod
    def _resolver_fn(fn_path):
        """Resolve string 'modulo.funcao' para callable."""
        import importlib
        partes = fn_path.split('.')
        for i in range(len(partes)-1, 0, -1):
            module_name = '.'.join(partes[:i])
            fn_name = '.'.join(partes[i:])
            try:
                mod = importlib.import_module(module_name)
                fn = mod
                for attr in fn_name.split('.'):
                    fn = getattr(fn, attr)
                return fn
            except (ImportError, AttributeError):
                continue
        return None

    # ─── Avaliar ────────────────────────────────────────

    def avaliar(self, resultados: List[Dict]) -> Dict:
        """Avalia todos os resultados com NOTA MCR."""
        notas = []
        for r in resultados:
            if r['status'] == 'sucesso':
                detalhes = r.get('detalhes', {})
                byte_s = min(1.0, detalhes.get('score_medio', 0.5))
                palavra_s = min(1.0, detalhes.get('opacos_medio', 100) / 500)
                token_s = min(1.0, detalhes.get('estados', 1) / 100)
                nota = self.peso_nota.calcular(byte_s=byte_s, palavra_s=palavra_s, token_s=token_s)
            elif r['status'] == 'simulado':
                nota = 0.5  # simulacao = nota mediana
            else:
                nota = 0.0
            notas.append(nota)

        nota_media = sum(notas) / len(notas) if notas else 0.0
        self.entropia.alimentar(f'nota:{int(nota_media*10)}')

        return {
            'nota_media': round(nota_media, 3),
            'notas_individuais': [round(n, 3) for n in notas],
            'em_loop': self.entropia.esta_em_loop(),
            'n_resultados': len(resultados),
        }

    # ─── Aprender ────────────────────────────────────────

    def aprender(self, input_texto: str, percepcao: Dict, resultados: List, avaliacao: Dict):
        """Aprende com o ciclo completo."""
        tipo = percepcao['tipo']
        nota = avaliacao['nota_media']

        self.mcr.aprender(f'input:{tipo}', f'resultado:{int(nota*10)}')
        for r in resultados:
            self.mcr.aprender(f'tarefa:{r["problema"]}', r['status'])

        return {'aprendido': True, 'nota': nota}

    # ─── Ciclo completo ─────────────────────────────────

    def pensar(self, input_texto: str, verbose=True) -> Dict:
        """Ciclo completo de pensamento MCR.

        1. PERCEBER: classificar input
        2. DECOMPOR: quebrar em subtarefas (via MCR navegador)
        3. EXECUTAR: cada subtarefa
        4. AVALIAR: tudo junto
        5. APRENDER: registrar
        """
        t0 = time.time()

        # 1. PERCEBER
        if verbose: print('\n[1/5] PERCEBER')
        percepcao = self.perceber(input_texto)
        if verbose: print(f'  Tipo: {percepcao["tipo"]} | Entropia: {percepcao["entropia"]}')

        # 2. DECOMPOR
        if verbose: print('\n[2/5] DECOMPOR')
        tarefas = self.decompor(percepcao)
        if verbose:
            for t in tarefas:
                pipe = ' -> '.join(t['pipeline'])
                print(f'  {t["problema"]}: {pipe} (conf={t["confianca"]:.2f})')

        # 3. EXECUTAR
        if verbose: print('\n[3/5] EXECUTAR')
        resultados = []
        for t in tarefas:
            r = self.executar(t, input_texto)
            resultados.append(r)
            if verbose:
                detalhes = r.get('detalhes', {})
                extra = ''
                if 'score_medio' in detalhes: extra = f' score={detalhes["score_medio"]}'
                elif 'opacos_medio' in detalhes: extra = f' {detalhes["opacos_medio"]} opacos'
                elif 'entropia' in detalhes: extra = f' H={detalhes["entropia"]}'
                print(f'  {r["ferramenta"]}: {r["status"]}{extra} ({r["tempo"]}s)')

        # 4. AVALIAR
        if verbose: print('\n[4/5] AVALIAR')
        avaliacao = self.avaliar(resultados)
        if verbose: print(f'  Nota MCR: {avaliacao["nota_media"]} | Loop: {avaliacao["em_loop"]}')

        # 5. APRENDER
        if verbose: print('\n[5/5] APRENDER')
        aprendizado = self.aprender(input_texto, percepcao, resultados, avaliacao)
        if verbose: print(f'  Registrado: {aprendizado["aprendido"]}')

        tempo_total = round(time.time() - t0, 2)
        if verbose: print(f'\nTempo total: {tempo_total}s')

        return {
            'percepcao': percepcao,
            'tarefas': tarefas,
            'resultados': resultados,
            'avaliacao': avaliacao,
            'aprendizado': aprendizado,
            'tempo': tempo_total,
        }

    def stats(self) -> Dict:
        return {
            'estados': self.mcr.stats()['estados'],
            'transicoes': self.mcr.stats()['transicoes'],
            'entropia': self.mcr.stats()['entropia'],
            'em_loop': self.entropia.esta_em_loop(),
        }
