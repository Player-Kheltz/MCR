"""conexao_bridge.py — adapta o KG do DevIA para o MCRConector do MCR.py v5.0.

Converte lessons do KnowledgeGraph em topicos + Markov chain
que o MCRConector pode consumir. Isso permite que o Emergir
descubra pontes entre topicos em 0ms (0 LLM) em vez de 25-40s."""
import os, sys, json, re, time

# MCR.py engine via caminho absoluto (evita conflito com modulos/MCR.py)
_mcr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MCR.py')
import importlib.util
_spec = importlib.util.spec_from_file_location("MCR_bridge", _mcr_path)
_mcr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mcr)
MCR = _mcr.MCR
MCRConector = _mcr.MCRConector


class CerebroKG:
    """Cerebro compativel com MCRConector, alimentado pelo KG do DevIA."""
    
    def __init__(self, kg=None):
        self.mk_palavra = MCR("palavras_kg")
        self.topicos = {}
        self._total_licoes = 0
        
        if kg:
            self._alimentar_do_kg(kg)
    
    def _alimentar_do_kg(self, kg):
        """Alimenta o MCR a partir de um KnowledgeGraph externo."""
        self.mk_palavra = MCR("palavras_kg")
        for lesson in getattr(kg, 'lessons', []) or []:
            if isinstance(lesson, dict):
                texto = lesson.get('erro', '') + ' ' + lesson.get('solucao', '')
                if len(texto) > 20:
                    self.mk_palavra.aprender(texto.split())
                    self._total_licoes += 1
    
    def alimentar_texto(self, ctx: str, texto: str):
        """Alimenta com texto arbitrario."""
        if not texto:
            return
        palavras = re.findall(r'\b[a-zA-Z0-9_]{3,}\b', texto.lower())
        if len(palavras) > 2:
            self.mk_palavra.aprender(palavras)
            topicos = re.findall(r'#(\w+)', texto)
            for t in topicos:
                self.topicos[t] = self.topicos.get(t, 0) + 1
    
    def descobrir_conexoes(self, top_k: int = 5) -> list:
        """Descobre pontes semanticas entre topicos via MCRConector."""
        topicos_lista = list(self.topicos.keys())
        if not topicos_lista or len(topicos_lista) < 2:
            return []
        
        conexao = MCRConector()
        resultados = []
        for i in range(len(topicos_lista)):
            for j in range(i+1, len(topicos_lista)):
                a, b = topicos_lista[i], topicos_lista[j]
                try:
                    score = conexao.conectar(a, b)
                    if score:
                        score_val = score if isinstance(score, (int, float)) else 0.5
                        resultados.append({
                            'topico_a': a, 'topico_b': b,
                            'ponte': 'conexao_semantica',
                            'score': score_val,
                        })
                except: pass
        
        resultados.sort(key=lambda x: -x.get('score', 0))
        return resultados[:top_k]
