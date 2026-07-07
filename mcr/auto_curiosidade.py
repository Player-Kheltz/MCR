"""mcr.auto_curiosidade — A Mente Inquieta.
Orquestra o estudo autonomo em background: detecta lacunas -> estuda -> aprende."""
import json
import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional

from mcr.meta_gap import MetaGap
from mcr.paths import KG_DIR
from mcr.encoding import read_file, write_file
from mcr.pattern_miner import miner_arquivo_lua, miner_arquivo_cpp


class AutoCuriosidade:
    """Mente Inquieta: estuda, aprende e alimenta o KG autonomamente."""

    def __init__(self, llm_func=None):
        self.llm_func = llm_func
        self.meta_gap = MetaGap()
        self._ciclo_count = 0
        self._licoes_aprendidas = 0
        KG_DIR.mkdir(parents=True, exist_ok=True)

    # ─── Estagio 1: Estudar Arquivo ────────────────────────────

    def estudar_arquivo(self, caminho: Path) -> Optional[Dict]:
        """Estuda um arquivo: extrai AST + gere resumo.
        
        Returns:
            dict com licao estruturada, ou None se falhar.
        """
        if not caminho.exists():
            return None

        ext = caminho.suffix.lower()
        print(f'[AutoCuriosidade] Estudando: {caminho.name}')

        t0 = time.time()
        padrao = None

        if ext == '.lua':
            padrao = miner_arquivo_lua(caminho)
        elif ext in ('.cpp', '.h', '.hpp'):
            padrao = miner_arquivo_cpp(caminho)

        if not padrao:
            print(f'[AutoCuriosidade] Nao foi possivel extrair AST de {caminho.name}')
            return None

        t1 = time.time()

        # Gera licao estruturada
        licao = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'arquivo': str(caminho),
            'linguagem': padrao.get('linguagem', 'unknown'),
            'tipo': padrao.get('tipo', 'generic'),
            'api_calls': padrao.get('api_calls', [])[:20],
            'variaveis': padrao.get('variaveis', [])[:10],
            'tamanho_linhas': padrao.get('tamanho_linhas', 0),
            'tempo_extracao': round(t1 - t0, 2),
            'estudado_por': 'auto_curiosidade',
        }

        # Se LLM disponivel, tenta resumo
        if self.llm_func:
            try:
                resumo = self._gerar_resumo_via_llm(padrao, caminho.name)
                if resumo:
                    licao['resumo_llm'] = resumo
            except Exception:
                pass

        print(f'[AutoCuriosidade] Licao extraida: {licao["linguagem"]}, '
              f'{len(licao["api_calls"])} APIs, {licao["tamanho_linhas"]} linhas')
        return licao

    def _gerar_resumo_via_llm(self, padrao: Dict, nome_arquivo: str) -> Optional[str]:
        """Usa o LLM para gerar um resumo do que o arquivo faz."""
        if not self.llm_func:
            return None

        prompt = (
            f"Analise este codigo-fonte do Canary (servidor Tibia).\n"
            f"Arquivo: {nome_arquivo}\n"
            f"Linguagem: {padrao.get('linguagem', '?')}\n"
            f"Tipo detectado: {padrao.get('tipo', 'generic')}\n"
            f"APIs chamadas: {', '.join(padrao.get('api_calls', [])[:10])}\n"
            f"Variaveis declaradas: {', '.join(padrao.get('variaveis', [])[:8])}\n"
            f"Tamanho: {padrao.get('tamanho_linhas', 0)} linhas\n\n"
            f"Resuma em 2-3 frases: O que este arquivo faz? "
            f"Qual conceito do jogo ele implementa? "
            f"O que um gerador de codigo precisa saber sobre ele?"
        )
        try:
            resp = self.llm_func(prompt, modelo='qwen2.5-coder:7b')
            if resp and len(resp) > 20:
                return resp.strip()[:500]
        except Exception:
            pass
        return None

    # ─── Estagio 2: Aprender Licao ─────────────────────────────

    def aprender_licao(self, licao: Dict) -> bool:
        """Injeta uma licao no Knowledge Graph (arquivo JSON).
        
        Returns:
            True se o KG foi atualizado.
        """
        if not licao:
            return False

        # Carrega KG atual
        padroes = []
        kg_path = self._get_kg_path()

        if kg_path.exists():
            try:
                with open(kg_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                padroes = dados.get('padroes', dados if isinstance(dados, list) else [])
            except Exception:
                padroes = []

        # Verifica se ja existe licao para este arquivo
        arquivo = licao.get('arquivo', '')
        for p in padroes:
            if p.get('arquivo') == arquivo:
                # Ja estudado — atualiza
                p.update(licao)
                break
        else:
            padroes.append(licao)

        # Salva
        with open(kg_path, 'w', encoding='utf-8') as f:
            json.dump({'metadata': {'total': len(padroes), 'atualizado': time.strftime('%Y-%m-%d %H:%M:%S')},
                       'padroes': padroes}, f, ensure_ascii=False, indent=2)

        self._licoes_aprendidas += 1
        print(f'[AutoCuriosidade] KG atualizado: {len(padroes)} padroes (+1 licao)')
        return True

    def _get_kg_path(self) -> Path:
        """Retorna o caminho do KG atual (ultimo patterns_*.json ou cria novo)."""
        arquivos = sorted(KG_DIR.glob('patterns_*.json'))
        if arquivos:
            return arquivos[-1]
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        return KG_DIR / f'patterns_{timestamp}.json'

    # ─── Ciclo Completo ────────────────────────────────────────

    def ciclo_de_estudo(self) -> int:
        """Executa um ciclo completo: detectar lacunas -> estudar -> aprender.
        
        Returns:
            numero de lacunas estudadas neste ciclo.
        """
        self._ciclo_count += 1
        print(f'\n[AutoCuriosidade] Ciclo #{self._ciclo_count}')

        lacunas = self.meta_gap.detectar_lacunas()
        if not lacunas:
            print('[AutoCuriosidade] Nenhuma lacuna detectada. KG completo para esta varredura.')
            return 0

        estudadas = 0
        for lacuna in lacunas[:3]:  # Estuda no max 3 por ciclo
            print(f'\n[AutoCuriosidade] Processando lacuna: {lacuna["tema"]}')

            # Estuda o primeiro arquivo da lacuna
            if not lacuna['arquivos']:
                continue

            caminho = Path(lacuna['arquivos'][0])
            licao = self.estudar_arquivo(caminho)

            if licao:
                # Adiciona metadados da lacuna
                licao['tema'] = lacuna['tema']
                licao['descoberto_por'] = 'meta_gap'
                licao['lacuna_motivo'] = lacuna['motivo']

                if self.aprender_licao(licao):
                    estudadas += 1

        print(f'[AutoCuriosidade] Ciclo #{self._ciclo_count} concluido: {estudadas} lacunas estudadas')
        return estudadas

    # ─── Thread Background ─────────────────────────────────────

    def iniciar_thread_background(self, intervalo: int = 60):
        """Inicia thread daemon que executa ciclo_de_estudo continuamente."""
        def _loop():
            while True:
                try:
                    self.ciclo_de_estudo()
                except Exception as e:
                    print(f'[AutoCuriosidade] Erro no ciclo: {e}')
                time.sleep(intervalo)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        print(f'[AutoCuriosidade] Thread background ativa a cada {intervalo}s')
        return t

    # ─── Utilitarios ───────────────────────────────────────────

    def estatisticas(self) -> Dict:
        return {
            'ciclos_executados': self._ciclo_count,
            'licoes_aprendidas': self._licoes_aprendidas,
            'lacunas_conhecidas': len(self.meta_gap.conhecidos),
        }
