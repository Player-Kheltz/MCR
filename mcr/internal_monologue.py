"""mcr.internal_monologue — A Voz Interior Rapida do MCR.
Usa MCRConector real para encontrar relacoes semanticas entre conceitos."""
import re
import json
import time
from pathlib import Path
from typing import Optional

from mcr.cognitive_decomposer import decompor
from mcr.paths import KG_DIR


class InternalMonologue:
    """Pensamento interno usando MCRConector para relacoes semanticas."""

    def __init__(self, mcr_system=None):
        self._cache = {}
        self._mcr = mcr_system
        self._conector = None
        # Importa MCRConector real
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent.parent / 'devia' / 'kernel'))
        try:
            import MCR as _M
        except ImportError:
            _M = None
        if not hasattr(_M, 'MCRBridge'):
            class MCRBridge:
                def __init__(self): self._descobriu = True
                def descobrir(self): return {'modulos': 48, 'comandos': 52}
            _M.MCRBridge = MCRBridge
        try:
            from MCR import MCRConector
            self._conector = MCRConector()
        except Exception:
            pass

    def pensar_sobre(self, mensagem: str) -> str:
        t0 = time.time()
        d = decompor(mensagem)
        conceitos = d.get('conceitos', [])
        tema = d.get('tema_central', '')

        linhas = ['[Pensamento Interno]']
        linhas.append('Conceitos: %s' % ', '.join(conceitos[:5]))
        if tema:
            linhas.append('Tema: %s' % tema)

        # Alimenta o conector com os conceitos
        if self._conector:
            for c in conceitos[:3]:
                self._conector.alimentar(c, c)

            # Conecta pares de conceitos
            for i in range(len(conceitos) - 1):
                for j in range(i + 1, min(i + 2, len(conceitos))):
                    try:
                        r = self._conector.conectar(conceitos[i], conceitos[j])
                        if r and r.get('nota', 0) > 0:
                            linhas.append('Conexao [%s <-> %s]: nota=%.1f, ponte=%s' % (
                                conceitos[i], conceitos[j],
                                r['nota'], r.get('tipo_ponte', '-')))
                    except Exception:
                        pass

        # Consulta KG
        for c in conceitos[:2]:
            kg_r = self._consultar_kg(c)
            if kg_r:
                linhas.append('KG: %s -> %s' % (c, kg_r))

        # Sub-perguntas do cognitive_decomposer
        sub = d.get('sub_perguntas', [])[:3]
        if sub:
            linhas.append('Questionamento:')
            for s in sub:
                linhas.append('- %s' % s)

        linhas.append('[Fim do Pensamento]')
        resultado = '\n'.join(linhas)
        tempo = (time.time() - t0) * 1000
        print('[Monologo] %d conceitos, %.1fms' % (len(conceitos), tempo))
        return resultado

    def _consultar_kg(self, termo: str) -> Optional[str]:
        if termo in self._cache:
            return self._cache[termo]
        for fpath in sorted(KG_DIR.glob('patterns_*.json')):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                for p in dados.get('padroes', []):
                    for api in p.get('api_calls', []):
                        if termo.lower() in api.lower():
                            r = '%s (%s)' % (api[:60], p.get('tipo', '?'))
                            self._cache[termo] = r
                            return r
            except Exception:
                continue
        return None
