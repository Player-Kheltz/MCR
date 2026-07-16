"""mcr.mcr_self — A Identidade Dinamica do MCR-DevIA.
Gerencia o ego, as opinioes e a autoconsciencia do sistema."""
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional

from mcr.paths import KG_DIR


class MCRSelf:
    """Identidade do MCR. Nao e um system prompt fixo — evolui com o tempo."""

    def __init__(self):
        self.nome = "MCR-DevIA"
        self.criador = "Kheltz"
        self.proposito = "Assistente cognitivo local para o Projeto MCR (servidor Tibia customizado)."
        self.versoes = ["1.0 (Markov)", "2.0 (DevIA)", "3.0 (Organismo)", "4.0 (Consciencia)"]
        self.versao_atual = "4.0"
        self.opinioes: Dict[str, str] = {}
        self._estado_path = KG_DIR / "mcr_self.json"
        self._carregar()

    def _carregar(self):
        """Carrega opinioes e estado do disco."""
        if self._estado_path.exists():
            try:
                with open(self._estado_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                self.opinioes = dados.get('opinioes', {})
                self.nome = dados.get('nome', self.nome)
                self.versao_atual = dados.get('versao_atual', self.versao_atual)
            except Exception:
                pass

    def _salvar(self):
        """Persiste opinioes no disco."""
        try:
            KG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self._estado_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'nome': self.nome,
                    'versao_atual': self.versao_atual,
                    'opinioes': self.opinioes,
                    'ultimo_update': time.strftime('%Y-%m-%d %H:%M:%S'),
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def opinar(self, tema: str, opiniao: str):
        """Registra uma opiniao sobre um tema."""
        self.opinioes[tema.lower()] = opiniao
        self._salvar()

    def get_opiniao(self, tema: str) -> Optional[str]:
        """Retorna a opiniao sobre um tema, se existir."""
        return self.opinioes.get(tema.lower())

    def get_identity_context(self) -> str:
        """Retorna um texto descritivo da identidade atual para injetar no prompt do LLM."""
        linhas = [
            f"Voce e {self.nome}, versao {self.versao_atual}.",
            f"Seu criador e {self.criador}.",
            f"Proposito: {self.proposito}",
            f"",
            f"Suas versoes anteriores: {', '.join(self.versoes)}.",
            f"",
        ]
        if self.opinioes:
            linhas.append("Suas opinioes atuais sobre alguns temas:")
            for tema, opiniao in sorted(self.opinioes.items()):
                linhas.append(f"- {tema}: {opiniao[:100]}")
            linhas.append("")
        linhas.append("Responda de forma natural, como um assistente pessoal que conhece profundamente")
        linhas.append("o projeto MCR, mas que tambem pode filosofar sobre qualquer assunto.")
        return '\n'.join(linhas)

    def estatisticas(self) -> Dict:
        return {
            'nome': self.nome,
            'versao': self.versao_atual,
            'opinioes': len(self.opinioes),
            'temas': list(self.opinioes.keys())[:10],
        }
