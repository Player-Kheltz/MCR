"""FewShotLearner — Aprendizado few-shot sem retreino.

LLMs aprendem do prompt ("exemplo1→A, exemplo2→B, novo→?").
MCR faz o mesmo EXTRAINDO exemplos do prompt e alimentando o coupling
em runtime. P(b|a) aprende em 1 exemplo — não precisa de backprop.

Pilar 1: cada exemplo vira P(output | input) no coupling.
Pilar 5: alimentar → predizer → aprender (loop fechado em runtime).
Pilar 7: exemplos compartilham padrões via NMI.

Uso:
    learner = FewShotLearner(coupling)
    learner.aprender_do_prompt("gato → animal\\ncarro → veiculo\\npeixe → ?")
    pred = learner.predizer("peixe")
"""
import re
from typing import Dict, List, Optional, Tuple


class FewShotLearner:

    def __init__(self, coupling):
        self._coupling = coupling
        self._exemplos: List[Tuple[str, str]] = []
        self._categorias: Dict[str, str] = {}

    def aprender_do_prompt(self, prompt: str) -> List[Tuple[str, str]]:
        """Extrai pares input→output do prompt e alimenta o coupling.

        Detecta padrões: "input → output", "input: output",
        "input = output", "input -> output".
        """
        padroes = [
            r'([a-zà-ÿ0-9\s]{2,30})\s*(?:→|->|=>|=|:)\s*([a-zà-ÿ0-9_]{2,30})',
        ]

        exemplos = []
        for padrao in padroes:
            matches = re.findall(padrao, prompt, re.IGNORECASE)
            for inp, out in matches:
                inp = inp.strip().lower()
                out = out.strip().lower()
                if not inp or not out or inp == out:
                    continue
                if len(inp) < 2 or len(out) < 2:
                    continue
                exemplos.append((inp, out))

        for inp, out in exemplos:
            self._coupling.alimentar(inp, out)
            self._exemplos.append((inp, out))
            self._categorias[inp] = out

        return exemplos

    def aprender_lote(self, exemplos: List[Tuple[str, str]]) -> None:
        """Alimenta múltiplos exemplos diretamente."""
        for inp, out in exemplos:
            self._coupling.alimentar(inp, out)
            self._exemplos.append((inp, out))
            self._categorias[inp] = out

    def predizer(self, input_text: str) -> Tuple[Optional[str], float]:
        """Prediz a categoria de um novo input após few-shot.

        Usa o coupling normalmente — os exemplos já foram alimentados.
        Se o input é idêntico a um exemplo, retorna direto.
        """
        input_lower = input_text.strip().lower()
        if input_lower in self._categorias:
            return self._categorias[input_lower], 1.0

        return self._coupling.decidir(input_text, (None, 0.0))

    def zerar(self) -> None:
        """Limpa exemplos aprendidos (não desalimenta o coupling)."""
        self._exemplos = []
        self._categorias = {}

    def n_exemplos(self) -> int:
        return len(self._exemplos)