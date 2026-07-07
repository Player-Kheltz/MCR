"""mcr.auto_curiosidade — A Mente Inquieta.
Usa MCRMeta (equacao PONTE_OTIMA) para detectar gaps reais no KG.
Toda saida vai para mcr_background.log (nao invade stdout)."""
import json
import time
import threading
from pathlib import Path
from typing import Dict, Optional

from mcr.mcr_meta import MCRMeta
from mcr.paths import KG_DIR
from mcr.encoding import read_file
from mcr.pattern_miner import miner_arquivo_lua, miner_arquivo_cpp
from mcr.silent_log import log


class AutoCuriosidade:
    """Mente Inquieta: usa MCRMeta para detectar gaps e estuda."""

    def __init__(self, llm_func=None):
        self.llm_func = llm_func
        self._ciclo_count = 0
        self._licoes_aprendidas = 0
        self._ultimo_diagnostico = {}
        KG_DIR.mkdir(parents=True, exist_ok=True)

    def ciclo_de_estudo(self) -> int:
        """Diagnostica gaps via MCRMeta -> estuda -> aprende."""
        self._ciclo_count += 1
        log('[AutoCuriosidade] Ciclo #%d' % self._ciclo_count)

        diag = MCRMeta.diagnosticar()
        self._ultimo_diagnostico = diag
        log('[AutoCuriosidade] KG: nota_geral=%.2f, gaps=%d' % (
            diag['nota_geral'], diag['conexoes_fracas']))

        if diag['nota_geral'] >= 9.0 and diag['conexoes_fracas'] == 0:
            log('[AutoCuriosidade] KG em excelencia.')
            return 0

        gap = diag['gap_principal']
        if not gap or gap in ('(nenhum)', 'KG vazio'):
            return 0

        topico_info = diag.get('topicos', {}).get(gap, {})
        arquivo = topico_info.get('arquivo', '')
        log('[AutoCuriosidade] Gap: "%s" (nota=%.2f)' % (gap, topico_info.get('nota', 0)))

        if arquivo and Path(arquivo).exists():
            licao = self._estudar(Path(arquivo))
            if licao:
                return 1
        return 0

    def _estudar(self, caminho: Path) -> Optional[Dict]:
        log('[AutoCuriosidade] Estudando: %s' % caminho.name)
        ext = caminho.suffix.lower()
        padrao = None
        if ext == '.lua':
            padrao = miner_arquivo_lua(caminho)
        elif ext in ('.cpp', '.h', '.hpp'):
            padrao = miner_arquivo_cpp(caminho)
        if not padrao:
            return None
        licao = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'arquivo': str(caminho),
            'linguagem': padrao.get('linguagem', 'unknown'),
            'tipo': padrao.get('tipo', 'generic'),
            'api_calls': padrao.get('api_calls', [])[:20],
            'variaveis': padrao.get('variaveis', [])[:10],
            'tamanho_linhas': padrao.get('tamanho_linhas', 0),
            'estudado_por': 'auto_curiosidade_mcr_meta',
        }
        if self._salvar(licao):
            self._licoes_aprendidas += 1
            return licao
        return None

    def _salvar(self, licao: Dict) -> bool:
        if not licao:
            return False
        padroes = []
        kg_path = self._get_kg_path()
        if kg_path.exists():
            try:
                with open(kg_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                padroes = dados.get('padroes', dados if isinstance(dados, list) else [])
            except Exception:
                padroes = []
        for p in padroes:
            if p.get('arquivo') == licao.get('arquivo', ''):
                p.update(licao)
                break
        else:
            padroes.append(licao)
        with open(kg_path, 'w', encoding='utf-8') as f:
            json.dump({'metadata': {'total': len(padroes)}, 'padroes': padroes}, f, ensure_ascii=False, indent=2)
        return True

    def _get_kg_path(self) -> Path:
        arquivos = sorted(KG_DIR.glob('patterns_*.json'))
        return arquivos[-1] if arquivos else KG_DIR / 'patterns_%s.json' % time.strftime('%Y%m%d_%H%M%S')

    def iniciar_thread_background(self, intervalo: int = 60):
        def _loop():
            while True:
                try:
                    self.ciclo_de_estudo()
                except Exception as e:
                    log('[AutoCuriosidade] Erro: %s' % e)
                time.sleep(intervalo)
        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        log('[AutoCuriosidade] Thread ativa a cada %ds' % intervalo)
        return t

    def estatisticas(self) -> Dict:
        return {
            'ciclos_executados': self._ciclo_count,
            'licoes_aprendidas': self._licoes_aprendidas,
        }
