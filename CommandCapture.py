"""CommandCapture — captura stdout dos comandos como string estruturada.

Os 52 comandos do DevIA imprimem resultados via print().
O CommandCapture redireciona stdout durante a execução e captura o output.
Isso permite encadear comandos: output do cmd_A → input do cmd_B.
"""
import sys
import io
from typing import List, Dict, Optional


class CommandCapture:
    """Captura stdout durante execução de um comando.
    
    Uso:
        cap = CommandCapture()
        with cap.capturar():
            kernel.executar("grep", ["main", "src/"])
        output = cap.texto  # string do stdout capturado
        linhas = cap.linhas  # lista de linhas
    """
    
    def __init__(self):
        self.texto: str = ""
        self.linhas: List[str] = []
        self._capturando = False
        self._original_stdout = None
    
    def capturar(self):
        """Retorna gerenciador de contexto para capturar stdout."""
        self._original_stdout = sys.stdout
        self._buffer = io.StringIO()
        sys.stdout = self._buffer
        self._capturando = True
        return self
    
    def __enter__(self):
        self.capturar()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parar()
    
    def parar(self):
        """Para a captura e processa o resultado."""
        if self._capturando and self._original_stdout:
            sys.stdout = self._original_stdout
            self.texto = self._buffer.getvalue()
            self.linhas = [l for l in self.texto.split('\n') if l]
            self._capturando = False
    
    def resultado_json(self) -> dict:
        """Retorna resultado estruturado para ser passado ao próximo comando."""
        return {
            "stdout": self.texto,
            "linhas": self.linhas,
            "total_linhas": len(self.linhas),
            "primeira_linha": self.linhas[0] if self.linhas else "",
            "ultima_linha": self.linhas[-1] if self.linhas else "",
        }
    
    def extrair_caminhos(self) -> List[str]:
        """Extrai caminhos de arquivo das linhas de output do grep/read."""
        import re
        caminhos = []
        for linha in self.linhas:
            # Padrão: "  src/main.cpp:L42: conteudo" ou "  [Read] arquivo.cpp"
            m = re.search(r'([\w/\\-]+\.\w+)(?::L\d+)?', linha)
            if m:
                caminhos.append(m.group(1))
        return caminhos
    
    def extrair_valores(self, prefixo: str = "") -> Dict[str, str]:
        """Extrai pares chave=valor das linhas de output."""
        import re
        valores = {}
        for linha in self.linhas:
            if prefixo and not linha.startswith(prefixo):
                continue
            m = re.search(r'(\w[\w\s]*?)\s*[:=]\s*(.+?)$', linha)
            if m:
                chave = m.group(1).strip().lower().replace(' ', '_')
                valor = m.group(2).strip()
                valores[chave] = valor
        return valores
