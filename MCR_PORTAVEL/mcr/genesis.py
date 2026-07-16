"""genesis.py — Auto-expansão MCR.

Princípio MCR:
  MCR descobre seus próprios níveis. Quando encontra novos padrões
  em diretórios de dados, gera automaticamente seeds e ferramentas.

Uso:
  genesis = MCRGenesis()
  genesis.expandir(mcr_instance, novo_diretorio)
  → descobre domínio, gera seeds, registra no coupling
"""
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional
import re


class MCRGenesis:
    """Auto-expansão: descobre novos domínios e gera ferramentas."""

    def __init__(self):
        self._descobertos: List[Dict] = []

    def expandir(self, mcr, diretorio: str) -> Optional[Dict]:
        """Explora diretório, descobre padrões, gera seeds.

        Args:
            mcr: instância MCR ativa
            diretorio: caminho do novo diretório de dados
        Returns:
            {'dominio': nome, 'arquivos': N, 'seeds': K} ou None
        """
        path = Path(diretorio)
        if not path.exists() or not path.is_dir():
            return None

        arquivos = [f for f in path.iterdir() if f.is_file()]
        if len(arquivos) < 5:
            return None

        nome_dominio = path.name
        seeds_gerados = 0

        # Extrai tokens dos nomes de arquivo
        tokens_freq = Counter()
        for f in arquivos[:30]:
            tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', f.stem.lower())
            for t in tokens:
                tokens_freq[t] += 1

        # Encontra a tool mais similar a este domínio
        wrappers = getattr(mcr, '_wrappers', {})
        tool_match = None
        dom_tokens = set(nome_dominio.replace('_', ' ').split())
        for tool_name in wrappers:
            tool_tokens = set(tool_name.replace('_lua', '').replace('_', ' ').split())
            if dom_tokens & tool_tokens or nome_dominio in tool_name:
                tool_match = tool_name.replace('_lua', '')
                break

        if not tool_match:
            # Domínio novo — usa o nome do diretório como tool
            tool_match = nome_dominio.replace('_', ' ')

        # Gera seeds dos arquivos
        seeds = []
        for f in arquivos[:15]:
            tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', f.stem.lower())
            if len(tokens) >= 2:
                frase = ' '.join(tokens[:4])
                estado = mcr._fingerprint_chave(frase)
                mcr.mk.aprender(estado, tool_match)
                mcr._coupling.alimentar(frase, tool_match)
                seeds.append(frase)
                seeds_gerados += 1

        resultado = {
            'dominio': nome_dominio,
            'arquivos': len(arquivos),
            'seeds': seeds_gerados,
            'tool': tool_match,
            'tokens': len(tokens_freq),
        }
        self._descobertos.append(resultado)
        return resultado

    def estatisticas(self) -> Dict:
        """Resumo de expansões realizadas."""
        return {
            'descobertos': len(self._descobertos),
            'dominios': [d['dominio'] for d in self._descobertos],
            'total_seeds': sum(d['seeds'] for d in self._descobertos),
        }
