"""mcr.registry — Tool Registry Central.

Tudo é registry. MCR decide qual entrada usar.
Substitui TODAS as cadeias if/elif por lookup em dict.

O registry é:
- Auto-expansível: MCR pode registrar novas tools em runtime
- Persistente: salva em JSON entre sessões
- Auto-descritivo: cada entry tem metadados para MCR decidir
"""
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ─── Caminhos ──────────────────────────────────────────────
_CACHE_DIR = Path(__file__).resolve().parent.parent / 'cache'
_REGISTRY_PATH = _CACHE_DIR / 'mcr_registry.json'
_KNOWLEDGE_PATH = _CACHE_DIR / 'mcr_knowledge.db'
_SESSION_PATH = _CACHE_DIR / 'mcr_session.json'


class ToolEntry:
    """Uma tool registrada no registry."""
    __slots__ = ('nome', 'fn', 'params', 'dominio', 'nivel', 'descricao',
                 'usos', 'sucessos', 'ultimo_uso', 'meta')

    def __init__(self, nome: str, fn: Callable, params: list = None,
                 dominio: str = '', nivel: int = 0, descricao: str = '',
                 meta: dict = None):
        self.nome = nome
        self.fn = fn
        self.params = params or []
        self.dominio = dominio
        self.nivel = nivel  # 0=auto, 1=template, 2=markov, 3=llm
        self.descricao = descricao
        self.usos = 0
        self.sucessos = 0
        self.ultimo_uso = 0.0
        self.meta = meta or {}

    def executar(self, **kwargs) -> Any:
        """Executa a tool com params."""
        t0 = time.time()
        try:
            resultado = self.fn(**kwargs)
            self.usos += 1
            if isinstance(resultado, dict) and resultado.get('sucesso', True):
                self.sucessos += 1
            self.ultimo_uso = time.time()
            return resultado
        except Exception as e:
            self.usos += 1
            self.ultimo_uso = time.time()
            raise e

    def taxa_sucesso(self) -> float:
        return self.sucessos / self.usos if self.usos > 0 else 0.0

    def to_dict(self) -> dict:
        """Serializa metadados (não a fn)."""
        return {
            'nome': self.nome,
            'params': self.params,
            'dominio': self.dominio,
            'nivel': self.nivel,
            'descricao': self.descricao,
            'usos': self.usos,
            'sucessos': self.sucessos,
            'meta': self.meta,
        }

    @classmethod
    def from_dict(cls, d: dict, fn: Callable = None) -> 'ToolEntry':
        """Desserializa metadados."""
        return cls(
            nome=d['nome'], fn=fn or (lambda **kw: None),
            params=d.get('params', []),
            dominio=d.get('dominio', ''),
            nivel=d.get('nivel', 0),
            descricao=d.get('descricao', ''),
            meta=d.get('meta', {}),
        )


class MCRRegistry:
    """Tool Registry Central — substitui TODAS as cadeias if/elif.

    Uso:
        registry = MCRRegistry()
        registry.registrar('gerar_npc', gerar_npc_fn, dominio='lua', nivel=1)
        tool = registry.selecionar('gerar_npc')
        resultado = tool.executar(nome='Ferreiro', tipo='shop')
    """

    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}
        self._por_dominio: Dict[str, List[str]] = {}
        self._historico: List[dict] = []

    def registrar(self, nome: str, fn: Callable, params: list = None,
                  dominio: str = '', nivel: int = 0, descricao: str = '',
                  meta: dict = None) -> ToolEntry:
        """Registra uma tool no registry."""
        entry = ToolEntry(nome=nome, fn=fn, params=params,
                          dominio=dominio, nivel=nivel,
                          descricao=descricao, meta=meta)
        self._tools[nome] = entry
        if dominio:
            self._por_dominio.setdefault(dominio, [])
            if nome not in self._por_dominio[dominio]:
                self._por_dominio[dominio].append(nome)
        return entry

    def selecionar(self, nome: str) -> Optional[ToolEntry]:
        """Seleciona uma tool pelo nome."""
        return self._tools.get(nome)

    def listar(self, dominio: str = None) -> List[str]:
        """Lista tools disponíveis."""
        if dominio:
            return list(self._por_dominio.get(dominio, []))
        return sorted(self._tools.keys())

    def executar(self, nome: str, **kwargs) -> Any:
        """Executa uma tool pelo nome."""
        entry = self._tools.get(nome)
        if not entry:
            return {'erro': f'tool "{nome}" não encontrada'}
        try:
            return entry.executar(**kwargs)
        except Exception as e:
            return {'erro': str(e), 'tool': nome}

    def registrar_historico(self, entrada: str, ferramenta: str,
                            resultado: Any, nota: float):
        """Registra transição no histórico para MCR aprender."""
        self._historico.append({
            'entrada': entrada,
            'ferramenta': ferramenta,
            'nota': nota,
            'timestamp': time.time(),
        })

    def stats(self) -> dict:
        """Estatísticas do registry."""
        tools = list(self._tools.values())
        return {
            'total_tools': len(tools),
            'dominios': list(self._por_dominio.keys()),
            'mais_usadas': sorted(
                [(t.nome, t.usos) for t in tools],
                key=lambda x: -x[1]
            )[:10],
            'taxa_sucesso_media': (
                sum(t.taxa_sucesso() for t in tools) / len(tools)
                if tools else 0.0
            ),
        }

    def salvar(self):
        """Salva metadados do registry em JSON."""
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            'version': 1,
            'timestamp': time.time(),
            'tools': {nome: entry.to_dict()
                      for nome, entry in self._tools.items()},
            'historico': self._historico[-1000:],  # últimos 1000
        }
        with open(_REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def carregar(self):
        """Carrega metadados do registry de JSON.
        Não substitui functions — apenas metadados.
        """
        if not _REGISTRY_PATH.exists():
            return
        try:
            with open(_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for nome, td in data.get('tools', {}).items():
                if nome in self._tools:
                    entry = self._tools[nome]
                    entry.usos = td.get('usos', 0)
                    entry.sucessos = td.get('sucessos', 0)
                    entry.meta.update(td.get('meta', {}))
            self._historico = data.get('historico', [])
        except Exception:
            pass


# ─── Instância global ──────────────────────────────────────
_registry: Optional[MCRRegistry] = None


def get_registry() -> MCRRegistry:
    """Retorna a instância global do registry (singleton)."""
    global _registry
    if _registry is None:
        _registry = MCRRegistry()
    return _registry


def registrar(nome: str, fn: Callable, **kwargs) -> ToolEntry:
    """Atalho para registrar no registry global."""
    return get_registry().registrar(nome, fn, **kwargs)


def executar(nome: str, **kwargs) -> Any:
    """Atalho para executar do registry global."""
    return get_registry().executar(nome, **kwargs)


def selecionar(nome: str) -> Optional[ToolEntry]:
    """Atalho para selecionar do registry global."""
    return get_registry().selecionar(nome)


def listar(dominio: str = None) -> List[str]:
    """Atalho para listar do registry global."""
    return get_registry().listar(dominio)
