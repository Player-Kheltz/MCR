#!/usr/bin/env python3
"""pipeline_completo.py v2 — Pipeline com Worldbuilding Continuo.

Fluxo:
  1. MarkovDecider.classificar()
  2. Cache Hierarquico (L1→L2→L3)
  3. VERIFICAR_EXISTENTE (world_state.json)
  4. INJETAR_CONTEXTO_GLOBAL (KG)
  5. Geracao (LLM simples ou Ensemble)
  6. CoVe + Validador Estrutural
  7. CANONIZAR (salvar no mundo)
"""
import time, json, urllib.request
from typing import Dict, Optional

OLLAMA_URL = "http://localhost:11434/api/generate"


def _verificar_existente(pergunta: str, classe: str) -> Dict:
    """Verifica se entidade similar ja existe no mundo.

    Returns:
        dict com existe, entidade, sugestao
    """
    try:
        from mcr.mcr_world_state import _carregar
        estado = _carregar()
        
        # Extrai possiveis nomes da pergunta
        import re
        palavras = re.findall(r'\b[A-Z][a-zA-ZÀ-ÿ]{2,}\b', pergunta)
        
        # Verifica nos NPCs
        for nome, dados in estado.get('npcs', {}).items():
            # Match por nome
            if nome.lower() in pergunta.lower():
                return {'existe': True, 'tipo': 'npc', 'entidade': nome, 'dados': dados}
            # Match por palavra-chave na pergunta
            for p in palavras:
                if p.lower() in nome.lower():
                    return {'existe': True, 'tipo': 'npc', 'entidade': nome, 'dados': dados}
        
        # Verifica nas lores
        for nome, dados in estado.get('lores', {}).items():
            if nome.lower() in pergunta.lower():
                return {'existe': True, 'tipo': 'lore', 'entidade': nome, 'dados': dados}
        
        return {'existe': False, 'tipo': None, 'entidade': None, 'dados': None}
    except Exception:
        return {'existe': False, 'tipo': None, 'entidade': None, 'dados': None}


def _injetar_contexto(pergunta: str, classe: str) -> str:
    """Busca entidades relacionadas no mundo para enriquecer o prompt.

    Returns:
        string com contexto global para injetar no prompt
    """
    try:
        from mcr.mcr_world_state import _carregar
        estado = _carregar()
        partes = []

        # Busca NPCs relacionados
        npcs = list(estado.get('npcs', {}).keys())[:5]
        if npcs:
            partes.append('NPCs existentes no mundo: ' + ', '.join(npcs))

        # Busca lores relacionados
        lores = list(estado.get('lores', {}).keys())[:3]
        if lores:
            partes.append('Lores do mundo: ' + ', '.join(lores))

        if partes:
            return '\n'.join(partes)
        return ''
    except Exception:
        return ''


def _canonizar(pergunta: str, resposta: str, classe: str, modelo: str):
    """Salva entidade gerada no mundo (world_state + chronicle)."""
    try:
        import re
        from mcr.mcr_world_state import registrar_entidade

        # Extrai nome da entidade gerada
        nome_match = re.search(r'NOME:\s*(.+)', resposta)
        if nome_match:
            nome = nome_match.group(1).strip()
            if classe == 'criar_npc':
                registrar_entidade('npc', nome, {
                    'file': f'npc_{nome.lower().replace(" ", "_")}.lua',
                    'role': 'gerado_por_pipeline',
                    'tier': 'rascunho',
                })
                # Registra na cronica
                try:
                    from mcr.mcr_world_chronicle import append_chronicle
                    append_chronicle(
                        f'{nome} chegou ao mundo. {resposta[:200]}',
                        {'type': 'npc_arrival', 'entity': nome, 'classe': classe}
                    )
                except Exception:
                    pass
            elif classe == 'criar_lore' or classe == 'explicar_conceito':
                # Extrai titulo da lore (primeira linha substantiva)
                linhas = resposta.strip().split('\n')
                titulo = linhas[0][:80] if linhas else 'Lore Sem Titulo'
                registrar_entidade('lore', titulo, {
                    'tipo': 'gerado_por_pipeline',
                    'resumo': resposta[:300],
                    'tier': 'rascunho',
                })
    except Exception:
        pass


class PipelineCompleto:
    """Pipeline completo com worldbuilding continuo."""

    def __init__(self):
        self._stats = {
            'total': 0, 'cache_hit': 0, 'llm_simples': 0,
            'ensemble': 0, 'cove_falhas': 0, 'canonizados': 0,
            'anomalias_detectadas': 0, 'regeracoes': 0,
            'tempo_total': 0.0,
        }
        # Detector de anomalias (corpus + entropia adaptativa)
        self._detector = None
        try:
            from mcr.world_anomaly_detector import WorldAnomalyDetector
            from mcr.paths import SERVER_DIR, DEVIA_DIR
            scripts = str(SERVER_DIR / 'data' / 'scripts') if SERVER_DIR else None
            ws_path = str(DEVIA_DIR / 'world_state.json') if DEVIA_DIR else None
            chronicle_path = str(DEVIA_DIR / 'world_chronicle.md') if DEVIA_DIR else None
            kg_dir = str(DEVIA_DIR / 'knowledge') if DEVIA_DIR else None
            self._detector = WorldAnomalyDetector()
            self._detector.carregar(scripts_dir=scripts, world_state_path=ws_path,
                                    chronicle_path=chronicle_path, kg_dir=kg_dir)
        except Exception as e:
            print(f'[Pipeline] Detector nao carregado: {e}')

    def processar(self, pergunta: str, contexto: str = "") -> Dict:
        t0 = time.time()
        self._stats['total'] += 1

        # 1. MarkovDecider
        from mcr_devia_v2 import MarkovDecider
        md = MarkovDecider()
        classe, conf = md.classificar(pergunta)

        # 2. Cache
        if conf > 0.3:
            from mcr.cache_hierarquico import CacheHierarquico
            cache = CacheHierarquico()
            resposta_cache = cache.buscar(pergunta)
            if resposta_cache:
                self._stats['cache_hit'] += 1
                return {
                    'resposta': resposta_cache, 'rota': 'cache',
                    'classe': classe, 'confianca': conf,
                    'tempo': round(time.time() - t0, 3),
                }

        # 3. VERIFICAR_EXISTENTE
        existente = _verificar_existente(pergunta, classe)
        if existente['existe']:
            print(f'[Worldbuilding] Entidade existente encontrada: {existente["entidade"]}')

        # 4. INJETAR_CONTEXTO_GLOBAL
        contexto_global = _injetar_contexto(pergunta, classe)
        if contexto_global:
            print(f'[Worldbuilding] Contexto global injetado')

        # 5. Monta prompt
        from mcr.prompts_criativos import obter_prompt, obter_modelo
        prompt = obter_prompt(classe, pergunta, tipo=classe, npc='NPC', resumo=pergunta)
        if contexto_global:
            prompt = prompt.replace('Comece agora.',
                f'Contexto do mundo:\n{contexto_global}\n\nComece agora.')
        modelo = obter_modelo(classe)

        # 6. Gera
        classes_complexas = ['criar_codigo', 'criar_npc', 'criar_quest',
                             'criar_sistema', 'criar_habilidade_spa', 'criar_monster']
        is_complexa = classe in classes_complexas or conf < 0.15

        if is_complexa:
            from mcr.ensemble_7b import Ensemble7B
            ens = Ensemble7B()
            resultado_ens = ens.gerar(prompt)
            resposta = resultado_ens['resposta']
            self._stats['ensemble'] += 1

            # ─── World Anomaly Detector ─────────────────────────
            self._validar_anomalias_e_regerar(prompt, resposta, classe, modelo,
                                               lambda r, m: self._llm_gerar(r, m))

            from mcr.chain_of_verification import ChainOfVerification
            cov = ChainOfVerification()
            verificacao = cov.verificar(pergunta, resposta)
            if not verificacao['valida']:
                self._stats['cove_falhas'] += 1
                resposta = cov.corrigir(pergunta, resposta)

            # 7. CANONIZAR
            _canonizar(pergunta, resposta, classe, modelo)
            self._stats['canonizados'] += 1

            try:
                from mcr.cache_hierarquico import CacheHierarquico
                CacheHierarquico().aprender(pergunta, resposta, classe)
            except Exception:
                pass

            return {
                'resposta': resposta, 'rota': 'ensemble',
                'classe': classe, 'confianca': conf, 'modelo': modelo,
                'tempo': round(time.time() - t0, 3),
                'verificacao': verificacao,
                'existente': existente,
                'ensemble_detalhes': resultado_ens.get('detalhes', []),
            }
        else:
            resposta = self._llm_gerar(prompt, modelo)
            self._stats['llm_simples'] += 1

            # ─── World Anomaly Detector ─────────────────────────
            resposta = self._validar_anomalias_e_regerar(prompt, resposta, classe, modelo,
                                                         lambda r, m: self._llm_gerar(r, m))

            from mcr.chain_of_verification import ChainOfVerification
            cov = ChainOfVerification()
            verificacao = cov.verificar(pergunta, resposta)

            # 7. CANONIZAR
            _canonizar(pergunta, resposta, classe, modelo)
            self._stats['canonizados'] += 1

            try:
                from mcr.cache_hierarquico import CacheHierarquico
                CacheHierarquico().aprender(pergunta, resposta, classe)
            except Exception:
                pass

            return {
                'resposta': resposta, 'rota': 'llm_simples',
                'classe': classe, 'confianca': conf, 'modelo': modelo,
                'tempo': round(time.time() - t0, 3),
                'verificacao': verificacao,
                'existente': existente,
            }

    def _validar_anomalias_e_regerar(
        self, prompt: str, resposta: str, classe: str, modelo: str,
        gerador: callable, max_tentativas: int = 2,
    ) -> str:
        """Valida resposta contra o detector de anomalias.
        
        O limiar de anomalia emerge da entropia do corpus (Ponte Otima).
        Se detectar anomalias, ajusta o prompt e regenera.
        
        Apos sucesso, atualiza o detector com o novo texto validado.
        
        Returns:
            resposta corrigida (ou original se OK)
        """
        if not self._detector:
            return resposta

        resultado = self._detector.validar(resposta)
        tentativa = 0

        while resultado['exige_regeneracao'] and tentativa < max_tentativas:
            tentativa += 1
            self._stats['anomalias_detectadas'] += 1
            self._stats['regeracoes'] += 1

            termos = [a['token'] for a in resultado['anomalias'][:3]]
            print(f'[AnomalyDetector] Anomalias: {termos} '
                  f'(H={self._detector.entropia:.3f}, limiar={self._detector.limiar_anomalia:.3f}) '
                  f'tentativa {tentativa}')

            prompt_corrigido = (
                f"{prompt}\n\n"
                f"IMPORTANTE: O texto gerado anteriormente continha conceitos "
                f"incompativeis com o universo de fantasia medieval. "
                f"{resultado['instrucao']}"
            )

            resposta = gerador(prompt_corrigido, modelo)
            resultado = self._detector.validar(resposta)

        if tentativa > 0:
            print(f'[AnomalyDetector] Resposta regenerada {tentativa}x. OK')

        # Atualiza o detector com o texto validado (expande o corpus)
        self._detector.atualizar(resposta)

        return resposta

    def _llm_gerar(self, prompt: str, modelo: str = None) -> str:
        modelo_atual = modelo or "mistral:7b-32k"
        try:
            payload = json.dumps({
                "model": modelo_atual, "prompt": prompt, "stream": False,
                "options": {"num_predict": 1024, "temperature": 0.7, "num_ctx": 32768}
            }).encode()
            req = urllib.request.Request(OLLAMA_URL, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read()).get("response", "")
        except Exception as e:
            return f"[Erro LLM: {e}]"

    def expandir(self, nome_entidade: str,
                 prompt_adicional: str = "expanda a historia deste personagem") -> Dict:
        """Expande uma entidade existente no mundo.
        
        Args:
            nome_entidade: nome da entidade a expandir
            prompt_adicional: instrucao adicional para a expansao
        
        Returns:
            dict com resposta expandida, entidade, tipo
        """
        from mcr.mcr_world_state import obter_entidade, _carregar

        # Tenta encontrar nos NPCs
        dados = obter_entidade('npc', nome_entidade)
        tipo = 'npc'
        if not dados:
            dados = obter_entidade('lore', nome_entidade)
            tipo = 'lore'

        if not dados:
            return {'erro': f'Entidade "{nome_entidade}" nao encontrada no mundo',
                    'sugestao': 'Use processar() para criar uma nova'}

        t0 = time.time()
        prompt = (
            f'Expanda a historia de {nome_entidade}.\n\n'
            f'Dados atuais:\n{json.dumps(dados, ensure_ascii=False, indent=2)}\n\n'
            f'Instrucao: {prompt_adicional}\n\n'
            f'Escreva um paragrafo expandindo a historia, mantendo coerencia '
            f'com o que ja foi estabelecido. Nao contradiga os dados existentes.'
        )

        from mcr.prompts_criativos import obter_modelo
        modelo = obter_modelo('criar_npc')
        resposta = self._llm_gerar(prompt, modelo)
        tempo = round(time.time() - t0, 3)

        # Atualiza no mundo
        from mcr.mcr_world_state import registrar_entidade
        from mcr.mcr_world_chronicle import append_chronicle

        if tipo == 'npc':
            dados.setdefault('expansoes', [])
            dados['expansoes'].append(resposta[:500])
            registrar_entidade('npc', nome_entidade, {'expansoes': dados['expansoes']})
        else:
            dados.setdefault('expansoes', [])
            dados['expansoes'].append(resposta[:500])
            registrar_entidade('lore', nome_entidade, {'expansoes': dados['expansoes']})

        append_chronicle(
            f'A historia de {nome_entidade} foi expandida: {resposta[:200]}',
            {'type': 'expansion', 'entity': nome_entidade, 'entity_type': tipo}
        )

        return {
            'resposta': resposta,
            'entidade': nome_entidade,
            'tipo': tipo,
            'modelo': modelo,
            'tempo': tempo,
        }

    def estatisticas(self) -> Dict:
        total = max(self._stats['total'], 1)
        return {**self._stats,
                'taxa_cache': round(self._stats['cache_hit'] / total * 100, 1),
                'tempo_medio': round(self._stats['tempo_total'] / total, 1)}
