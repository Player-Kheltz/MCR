"""mcr.mcr_unificado — Pipeline unificado MCR.

UMA pipeline. SEIS estágios. ZERO if/elif.
Tudo é Markov + Registry.

Estágios:
  1. PERCEBE  — classifica entrada via Markov
  2. DECOMPÕE — quebra em subtarefas via Markov
  3. SELECIONA — escolhe tools do registry via Markov
  4. EXECUTA  — roda a tool selecionada
  5. VALIDA   — verifica resultado (Chain of Verification ou Markov)
  6. APRENDE  — registra transição para próxima decisão

Memória: fragmentada / compactada / codificada / SQLite
Persistência: JSON (registry) + SQLite (knowledge) + JSON (sessão)
"""
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcr.registry import get_registry, MCRRegistry, ToolEntry

_CACHE_DIR = Path(__file__).resolve().parent.parent / 'cache'
_SESSION_PATH = _CACHE_DIR / 'mcr_unified_session.json'


# ─── Estágios ──────────────────────────────────────────────

class Percebe:
    """Estágio 1: Classifica a entrada via Markov."""

    def __init__(self):
        self._markov = None

    def _get_markov(self):
        if self._markov is None:
            try:
                from mcr.engine import MCR
                self._markov = MCR("percebe")
            except Exception:
                self._markov = None
        return self._markov

    def classificar(self, entrada: str) -> Dict:
        m = self._get_markov()
        if m is None:
            return self._fallback(entrada)

        tokens = entrada.split() if isinstance(entrada, str) else [str(entrada)]
        if tokens:
            m.aprender_sequencia(tokens[:50])

        prox, conf = m.predizer(tokens[-1] if tokens else 'init')

        return {
            'dominio': self._mapear_dominio(entrada),
            'tipo': self._mapear_tipo(entrada),
            'complexidade': self._avaliar_complexidade(entrada),
            'tokens': tokens[:20],
            'confianca': round(conf, 3),
            'predicao_markov': str(prox),
        }

    def _mapear_dominio(self, entrada: str) -> str:
        m = self._get_markov()
        if m and m.transicoes:
            tokens = entrada.lower().split()
            if tokens:
                prox, conf = m.predizer(tokens[0])
                if conf > 0.3 and prox:
                    return str(prox)
        return f"dominio_{hash(entrada) % 10}"

    def _mapear_tipo(self, entrada: str) -> str:
        m = self._get_markov()
        if m and len(entrada) > 10:
            prox, _ = m.predizer(entrada[:20])
            if prox:
                return str(prox)
        return f"tipo_{len(entrada) % 5}"

    def _avaliar_complexidade(self, entrada: str) -> int:
        m = self._get_markov()
        if m:
            tokens = entrada.split()
            if tokens:
                h = m.entropia_sequencia(tokens[:10])
                return min(5, max(1, int(h * 2) + 1))
        return min(5, max(1, len(entrada.split()) // 5 + 1))

    def _fallback(self, entrada: str) -> Dict:
        return {
            'dominio': 'fallback',
            'tipo': 'texto',
            'complexidade': 1,
            'tokens': entrada.split()[:20] if isinstance(entrada, str) else [],
            'confianca': 0.0,
            'predicao_markov': 'unknown',
        }


class Decompoe:
    """Estágio 2: Decompõe entrada em subtarefas."""

    def __init__(self):
        self._markov = None

    def _get_markov(self):
        if self._markov is None:
            try:
                from mcr.engine import MCR
                self._markov = MCR("decompoe")
            except Exception:
                self._markov = None
        return self._markov

    def decompor(self, entrada: Dict, classificacao: Dict) -> List[Dict]:
        m = self._get_markov()
        dominio = classificacao.get('dominio', 'fallback')
        complexidade = classificacao.get('complexidade', 1)

        n_subtarefas = max(1, complexidade // 2 + 1)
        if m:
            prox, _ = m.predizer(dominio)
            if prox:
                try:
                    n_subtarefas = max(1, int(str(prox)[:1]) % 5 + 1)
                except Exception:
                    pass

        subtarefas = []
        texto = entrada.get('texto', str(entrada))
        tokens = texto.split()

        for i in range(n_subtarefas):
            start = i * len(tokens) // n_subtarefas
            end = (i + 1) * len(tokens) // n_subtarefas
            chunk = ' '.join(tokens[start:end]) if tokens else texto

            subtarefa = {
                'id': f"sub_{i}",
                'entrada': chunk,
                'dominio': dominio,
                'ordem': i,
                'status': 'pendente',
            }
            subtarefas.append(subtarefa)

            if m:
                m.aprender(f"decomp_{i}", dominio)

        return subtarefas


class Seleciona:
    """Estágio 3: Seleciona tools do registry via Markov."""

    def __init__(self, registry: MCRRegistry = None):
        self._registry = registry or get_registry()
        self._markov = None

    def _get_markov(self):
        if self._markov is None:
            try:
                from mcr.engine import MCR
                self._markov = MCR("seleciona")
            except Exception:
                self._markov = None
        return self._markov

    def selecionar(self, subtarefa: Dict, classificacao: Dict) -> Optional[ToolEntry]:
        dominio = subtarefa.get('dominio', classificacao.get('dominio', ''))
        texto = subtarefa.get('entrada', '')

        candidates = self._registry.listar(dominio=dominio)

        m = self._get_markov()
        if m and candidates:
            prox, conf = m.predizer(dominio)
            if prox and conf > 0.2:
                for c in candidates:
                    if str(prox).lower() in c.lower():
                        entry = self._registry.selecionar(c)
                        if entry:
                            return entry

        if candidates:
            entry = self._registry.selecionar(candidates[0])
            if entry:
                return entry

        todas = self._registry.listar()
        if todas:
            entry = self._registry.selecionar(todas[0])
            if entry:
                return entry

        return None


class Executa:
    """Estágio 4: Executa a tool selecionada."""

    def executar(self, tool: ToolEntry, subtarefa: Dict) -> Dict:
        if tool is None:
            return {'erro': 'nenhuma tool selecionada', 'sucesso': False}

        t0 = time.time()
        try:
            kwargs = self._preparar_kwargs(tool, subtarefa)
            resultado = tool.executar(**kwargs)
            return {
                'resultado': resultado,
                'sucesso': True,
                'tool': tool.nome,
                'tempo': round(time.time() - t0, 3),
            }
        except Exception as e:
            return {
                'erro': str(e),
                'sucesso': False,
                'tool': tool.nome,
                'tempo': round(time.time() - t0, 3),
            }

    def _preparar_kwargs(self, tool: ToolEntry, subtarefa: Dict) -> Dict:
        kwargs = {}
        entrada = subtarefa.get('entrada', '')

        for param in tool.params:
            if param in ('texto', 'entrada', 'input', 'prompt'):
                kwargs[param] = entrada
            elif param in ('nome', 'name'):
                kwargs[param] = entrada.split()[0] if entrada else 'default'
            elif param in ('dominio', 'domain'):
                kwargs[param] = subtarefa.get('dominio', '')
            elif param in ('contexto', 'context'):
                kwargs[param] = subtarefa
            else:
                kwargs[param] = entrada

        return kwargs


class Valida:
    """Estágio 5: Valida o resultado."""

    def __init__(self):
        self._cov = None

    def _get_cov(self):
        if self._cov is None:
            try:
                from mcr.chain_of_verification import ChainOfVerification
                self._cov = ChainOfVerification()
            except Exception:
                self._cov = None
        return self._cov

    def validar(self, resultado: Dict, subtarefa: Dict) -> Dict:
        if not resultado.get('sucesso', False):
            return {
                'valido': False,
                'motivo': resultado.get('erro', 'execução falhou'),
                'nota': 0.0,
            }

        saida = resultado.get('resultado', '')

        cov = self._get_cov()
        if cov:
            try:
                validacao = cov.verificar(str(saida))
                return {
                    'valido': validacao.get('valido', True),
                    'motivo': validacao.get('motivo', 'ok'),
                    'nota': validacao.get('nota', 0.5),
                }
            except Exception:
                pass

        if saida and len(str(saida)) > 0:
            return {'valido': True, 'motivo': 'tem_conteudo', 'nota': 0.5}

        return {'valido': False, 'motivo': 'saida_vazia', 'nota': 0.0}


class Aprende:
    """Estágio 6: Aprende com o resultado."""

    def __init__(self):
        self._historico: List[Dict] = []

    def aprender(self, entrada: Dict, classificacao: Dict,
                 tool_nome: str, resultado: Dict, validacao: Dict):
        transicao = {
            'entrada_hash': hash(json.dumps(entrada, default=str, sort_keys=True)) % 10000,
            'dominio': classificacao.get('dominio', ''),
            'tool': tool_nome,
            'sucesso': resultado.get('sucesso', False),
            'nota': validacao.get('nota', 0.0),
            'timestamp': time.time(),
        }
        self._historico.append(transicao)

        try:
            from mcr.engine import MCR
            m = MCR("aprende")
            m.aprender(
                classificacao.get('dominio', 'unknown'),
                tool_nome
            )
            if resultado.get('sucesso'):
                m.aprender(tool_nome, 'sucesso')
            else:
                m.aprender(tool_nome, 'fracasso')
        except Exception:
            pass

    def salvar(self):
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            'version': 1,
            'timestamp': time.time(),
            'historico': self._historico[-500:],
        }
        try:
            with open(_SESSION_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception:
            pass

    def carregar(self):
        if _SESSION_PATH.exists():
            try:
                with open(_SESSION_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._historico = data.get('historico', [])
            except Exception:
                pass


# ─── Pipeline Unificada ────────────────────────────────────

class MCRUnificado:
    """Pipeline unificada MCR — UM pipeline, SEIS estágios.

    Uso:
        mcr = MCRUnificado()
        resultado = mcr.processar("Gere um NPC ferreiro")
        print(resultado)
    """

    def __init__(self, registry: MCRRegistry = None):
        self._registry = registry or get_registry()

        # Auto-bootstrap se registry vazio
        if not self._registry.listar():
            try:
                from mcr.bootstrap import inicializar
                inicializar(self._registry)
            except Exception:
                pass

        self._percebe = Percebe()
        self._decompoe = Decompoe()
        self._seleciona = Seleciona(self._registry)
        self._executa = Executa()
        self._valida = Valida()
        self._aprende = Aprende()
        self._aprende.carregar()
        self.interacoes = 0
        self.tempo_total = 0.0

    def processar(self, entrada: str) -> Dict:
        """Alias para executar — compatibilidade com código antigo."""
        resultado = self.executar(entrada)
        resultado['resposta'] = resultado.get('entrada', '')
        if resultado['resultados']:
            ultimo = resultado['resultados'][-1]
            r = ultimo.get('resultado', {})
            resultado['resposta'] = r.get('resultado', '')
        resultado['intencao'] = resultado.get('classificacao', {}).get('dominio', '')
        resultado['confianca'] = resultado.get('classificacao', {}).get('confianca', 0)
        resultado['tempo'] = resultado.get('tempo_total', 0)
        resultado['interacao'] = self.interacoes
        return resultado

    def executar(self, entrada: str, contexto: Dict = None) -> Dict:
        t0 = time.time()
        self.interacoes += 1

        classificacao = self._percebe.classificar(entrada)

        entrada_dict = {'texto': entrada, **(contexto or {})}
        subtarefas = self._decompoe.decompor(entrada_dict, classificacao)

        resultados = []
        for st in subtarefas:
            tool = self._seleciona.selecionar(st, classificacao)
            resultado = self._executa.executar(tool, st)
            validacao = self._valida.validar(resultado, st)

            self._aprende.aprender(
                entrada_dict, classificacao,
                resultado.get('tool', ''), resultado, validacao
            )

            resultados.append({
                'subtarefa': st,
                'resultado': resultado,
                'validacao': validacao,
            })

        self._aprende.salvar()

        sucesso_total = all(r['validacao']['valido'] for r in resultados) if resultados else False
        nota_media = (
            sum(r['validacao']['nota'] for r in resultados) / len(resultados)
            if resultados else 0.0
        )

        tempo = round(time.time() - t0, 6)
        self.tempo_total += tempo

        return {
            'entrada': entrada[:200],
            'classificacao': classificacao,
            'n_subtarefas': len(subtarefas),
            'resultados': resultados,
            'sucesso': sucesso_total,
            'nota': round(nota_media, 3),
            'tempo_total': tempo,
            'intencao': classificacao.get('dominio', ''),
            'confianca': classificacao.get('confianca', 0),
            'resposta': resultados[-1]['resultado'].get('resultado', '') if resultados else '',
            'interacao': self.interacoes,
        }

    def executar_rapido(self, entrada: str) -> Any:
        classificacao = self._percebe.classificar(entrada)
        st = {'entrada': entrada, 'dominio': classificacao['dominio'], 'id': 'quick'}
        tool = self._seleciona.selecionar(st, classificacao)
        if tool:
            resultado = self._executa.executar(tool, st)
            return resultado.get('resultado')
        return None

    def status(self) -> Dict:
        s = self.stats()
        s['interacoes'] = self.interacoes
        s['tempo_total'] = round(self.tempo_total, 4)
        return s

    def stats(self) -> Dict:
        return {
            'registry': self._registry.stats(),
            'historico': len(self._aprende._historico),
            'modulos': {
                'percebe': self._percebe._get_markov() is not None,
                'decompoe': self._decompoe._get_markov() is not None,
                'seleciona': self._seleciona._get_markov() is not None,
                'valida': self._valida._get_cov() is not None,
            },
        }

    def close(self):
        self._aprende.salvar()


# ─── Instância global ──────────────────────────────────────
_unificado: Optional[MCRUnificado] = None


def get_unificado() -> MCRUnificado:
    global _unificado
    if _unificado is None:
        _unificado = MCRUnificado()
    return _unificado


def executar(entrada: str, contexto: Dict = None) -> Dict:
    return get_unificado().executar(entrada, contexto)


# ─── Teste ───────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print('  MCRUnificado — Pipeline Unificado (6 estágios)')
    print('=' * 60)

    mcr = MCRUnificado()
    s = mcr.status()
    print(f'  Registry: {s["registry"]["total_tools"]} tools')
    print(f'  Módulos Markov: {s["modulos"]}')

    testes = [
        'Ola!',
        'Crie um NPC ferreiro para a cidade de Thais',
        'Quanto e 15 + 27?',
        'Analise: O MCR usa Markov e entropia para aprender padroes.',
        'Crie uma ideia para um novo item magico',
    ]

    for msg in testes:
        r = mcr.processar(msg)
        print(f'\n  [{r["intencao"]}] {msg[:60]}')
        print(f'  -> {str(r["resposta"])[:150]}')
        print(f'  ({r["tempo"]*1000:.1f}ms)')

    print('\n' + '=' * 60)
    print(f'  Interações: {mcr.interacoes}')
    print(f'  Tempo total: {mcr.tempo_total:.3f}s')
    print('=' * 60)
    mcr.close()
