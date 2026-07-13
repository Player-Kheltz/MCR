#!/usr/bin/env python3
"""
mcr.raciocinador.py — Motor de Raciocinio + Compreensao + Tool Use (FASE 5-7).

Capacidades:
  1. Compreensao: extrair informacao de texto, responder perguntas
  2. Raciocinio: silogismos, cadeia de pensamento, decisao multi-passo
  3. Tool Use: escolher e compor ferramentas para tarefas

Uso:
    rac = Raciocinador()
    rac.compreender(texto, pergunta)     # Q&A sobre texto
    rac.raciocinar(problema)              # resolver problema logico
    rac.usar_ferramenta(tarefa)           # escolher + executar ferramenta
"""
import os, sys, os, re, math, json, time
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcr.mcr_sqlite import MCRSQLite
from mcr.paths import CACHE_DIR


class Raciocinador:
    """Motor de raciocinio, compreensao e tool use."""

    def __init__(self):
        db_conversa = str(CACHE_DIR / 'mcr_conversa.db')
        if os.path.exists(db_conversa):
            self.mcr = MCRSQLite(db_conversa, n_max=5, identidade='compreensao')
        else:
            self.mcr = MCRSQLite(db_conversa, n_max=5, identidade='compreensao')

        self.ferramentas: Dict[str, Dict] = {}
        self._registrar_ferramentas()

    # ═══════════════════════════════════════════════════
    # FASE 5: COMPREENSAO DE TEXTO
    # ═══════════════════════════════════════════════════

    def compreender(self, texto: str, pergunta: str = None) -> Dict:
        """Analisa um texto e extrai informacao.

        Args:
            texto: texto para analisar
            pergunta: pergunta opcional sobre o texto

        Returns:
            dict com analise
        """
        if not texto:
            return {'erro': 'texto vazio'}

        # Fragmentar
        fragmentos = self._fragmentar(texto)
        palavras = re.findall(r'[a-zA-ZÀ-ÿ]{3,}', texto.lower())

        # Entropia do texto
        from collections import Counter
        freq = Counter(palavras)
        total = sum(freq.values())
        h = -sum((c / total) * math.log2(c / total) for c in freq.values() if c > 0)

        # Palavras-chave (maior frequencia)
        top_palavras = freq.most_common(5)

        resultado = {
            'fragmentos': len(fragmentos),
            'palavras': len(palavras),
            'unicas': len(freq),
            'entropia': round(h, 4),
            'top_palavras': top_palavras,
        }

        # Responder pergunta
        if pergunta:
            resultado['pergunta'] = pergunta
            resultado['resposta'] = self._responder_pergunta(pergunta, texto, fragmentos, freq)

        return resultado

    def _fragmentar(self, texto: str) -> List[str]:
        """Fragmenta texto em sentencas."""
        partes = re.split(r'[.!?\n]+', texto)
        return [p.strip() for p in partes if len(p.strip()) > 10]

    def _responder_pergunta(self, pergunta: str, texto: str,
                            fragmentos: List[str],
                            freq: Dict[str, int]) -> str:
        """Responde pergunta sobre o texto usando similaridade Jaccard."""
        palavras_pergunta = set(re.findall(r'[a-zA-ZÀ-ÿ]{3,}', pergunta.lower()))

        # Encontrar fragmento mais relevante
        melhor_frag = None
        melhor_score = 0
        for frag in fragmentos:
            palavras_frag = set(re.findall(r'[a-zA-ZÀ-ÿ]{3,}', frag.lower()))
            inter = palavras_pergunta & palavras_frag
            uniao = palavras_pergunta | palavras_frag
            score = len(inter) / len(uniao) if uniao else 0
            if score > melhor_score:
                melhor_score = score
                melhor_frag = frag

        if melhor_frag and melhor_score > 0.1:
            return melhor_frag[:300]
        return None

    # ═══════════════════════════════════════════════════
    # FASE 6: RACIOCINIO MULTI-PASSO
    # ═══════════════════════════════════════════════════

    def raciocinar(self, problema: str) -> Dict:
        """Resolve problema usando cadeia de pensamento.

        Pipeline:
          1. Classificar tipo de problema
          2. Decompor em passos logicos
          3. Resolver cada passo
          4. Compor resultado final
        """
        tipo = self._classificar_problema(problema)

        if tipo == 'silogismo':
            return self._resolver_silogismo(problema)
        elif tipo == 'comparacao':
            return self._resolver_comparacao(problema)
        elif tipo == 'matematica':
            return self._resolver_matematica(problema)
        else:
            return self._raciocinio_generico(problema)

    def _classificar_problema(self, texto: str) -> str:
        txt = texto.lower()
        if any(w in txt for w in ['portanto', 'logo', 'entao', 'se', 'maior', 'menor',
                                    'conclusao', 'deduz', 'conclui']):
            if ' > ' in texto or ' < ' in texto or 'maior' in txt or 'menor' in txt:
                return 'comparacao'
            return 'silogismo'
        if re.search(r'\d+\s*[\+\-\*\/]\s*\d+', texto):
            return 'matematica'
        return 'generico'

    def _resolver_silogismo(self, problema: str) -> Dict:
        """Resolve silogismos: A > B e B > C, logo A > C."""
        passos = []
        # Extrair premissas
        numeros = re.findall(r'\d+', problema)
        relacoes = re.findall(r'(maior|menor|>|<)', problema.lower())

        nomes = ['A', 'B', 'C', 'D', 'E', 'F']
        if numeros:
            valores = [int(n) for n in numeros[:3]]
            passos.append(f'Valores: {valores}')
            resultado = max(valores) if 'maior' in problema.lower() or '>' in problema else min(valores)
            passos.append(f'Resultado: {resultado}')
            return {
                'tipo': 'silogismo',
                'passos': passos,
                'resultado': resultado,
                'confianca': 1.0,
                'conclusao': f'O maior valor e {resultado}'
            }

        return {
            'tipo': 'silogismo',
            'passos': passos,
            'resultado': None,
            'confianca': 0.5,
            'conclusao': 'Silogismo detectado, mas sem valores numericos para resolver.'
        }

    def _resolver_comparacao(self, problema: str) -> Dict:
        """Resolve comparacoes: Se A > B e B > C, A ? C."""
        # Extrai relacoes
        padrao = r'(\w+)\s*(>|<|maior que|menor que)\s*(\w+)'
        relacoes = re.findall(padrao, problema.lower())
        passos = []

        for a, op, b in relacoes:
            op_norm = '>' if op in ('>', 'maior que') else '<'
            passos.append(f'{a} {op_norm} {b}')

        if len(relacoes) >= 2:
            # Transitividade: A > B e B > C => A > C
            conclusao = 'Sim, por transitividade: se a primeira relacao e verdadeira e compartilha um elemento com a segunda, a conclusao segue logicamente.'
        else:
            conclusao = 'Preciso de pelo menos 2 relacoes para deduzir uma conclusao.'

        return {
            'tipo': 'comparacao',
            'passos': passos,
            'relacoes': relacoes,
            'conclusao': conclusao,
            'confianca': 0.8 if len(relacoes) >= 2 else 0.3,
        }

    def _resolver_matematica(self, problema: str) -> Dict:
        """Resolve problemas matematicos simples."""
        # Extrai numeros e operadores
        numeros_ops = re.findall(r'[\d\+\-\*\/\(\)]+', problema.replace(' ', ''))
        passos = []
        resultado = None
        if numeros_ops:
            expr = ''.join(numeros_ops)
            passos.append(f'Expressao detectada: {expr}')
            try:
                resultado = eval(expr)
                passos.append(f'Resultado: {expr} = {resultado}')
            except Exception as e:
                passos.append(f'Erro ao avaliar: {e}')

        return {
            'tipo': 'matematica',
            'passos': passos,
            'resultado': resultado,
            'conclusao': str(resultado) if resultado is not None else 'Nao foi possivel calcular',
        }

    def _raciocinio_generico(self, problema: str) -> Dict:
        """Raciocinio generico via decomposicao."""
        palavras = re.findall(r'[a-zA-ZÀ-ÿ]{3,}', problema.lower())
        passos = ['Analisando: ' + problema[:100]]

        # Gerar cadeia de pensamento via MCR
        cadeia = []
        for p in palavras[:5]:
            pred = self.mcr.predizer(p)
            if pred[0]:
                cadeia.append(pred[0])

        passos.append('Palavras-chave: ' + ', '.join(palavras[:5]))
        if cadeia:
            passos.append('Raciocinio: ' + ' → '.join(cadeia))

        return {
            'tipo': 'generico',
            'passos': passos,
            'conclusao': 'Raciocinio generico baseado nas palavras-chave.',
            'confianca': 0.4,
        }

    # ═══════════════════════════════════════════════════
    # FASE 7: TOOL USE
    # ═══════════════════════════════════════════════════

    def _registrar_ferramentas(self):
        self.ferramentas = {
            'criar_npc': {
                'desc': 'criar npc ferreiro guarda mercador personagem',
                'fn': self._tool_criar_npc,
            },
            'criar_codigo': {
                'desc': 'criar codigo lua script funcao gerar programar',
                'fn': self._tool_criar_codigo,
            },
            'analisar_texto': {
                'desc': 'analisar compreender texto documento explicar entender',
                'fn': self._tool_analisar_texto,
            },
            'gerar_sprite': {
                'desc': 'criar gerar sprite imagem desenho grafico visual',
                'fn': self._tool_gerar_sprite,
            },
            'raciocinar': {
                'desc': 'raciocinar pensar deduzir logica resolver problema silogismo',
                'fn': self._tool_raciocinar,
            },
        }

    def escolher_ferramenta(self, tarefa: str) -> Optional[str]:
        """Escolhe a melhor ferramenta para a tarefa usando Jaccard."""
        palavras_tarefa = set(re.findall(r'[a-zA-ZÀ-ÿ]{3,}', tarefa.lower()))
        melhor = None
        melhor_score = 0

        for nome, f in self.ferramentas.items():
            palavras_desc = set(f['desc'].split())
            inter = palavras_tarefa & palavras_desc
            uniao = palavras_tarefa | palavras_desc
            score = len(inter) / len(uniao) if uniao else 0
            if score > melhor_score:
                melhor_score = score
                melhor = nome

        return melhor if melhor_score > 0.1 else None

    def usar_ferramenta(self, tarefa: str) -> Dict:
        """Escolhe e executa a melhor ferramenta para a tarefa."""
        ferramenta = self.escolher_ferramenta(tarefa)

        if not ferramenta:
            return {
                'sucesso': False,
                'tarefa': tarefa,
                'erro': 'Nenhuma ferramenta adequada encontrada',
                'ferramentas_disponiveis': list(self.ferramentas.keys()),
            }

        fn = self.ferramentas[ferramenta]['fn']
        try:
            resultado = fn(tarefa)
            return {
                'sucesso': True,
                'tarefa': tarefa,
                'ferramenta': ferramenta,
                'resultado': resultado,
            }
        except Exception as e:
            return {
                'sucesso': False,
                'tarefa': tarefa,
                'ferramenta': ferramenta,
                'erro': str(e),
            }

    def _tool_criar_npc(self, tarefa: str) -> Dict:
        try:
            from mcr.gerador_codigo import GeradorCodigo
            g = GeradorCodigo()
            r = g.gerar_lua(tipo='npc', semente='local')
            g.close()
            return {'codigo': r['codigo'][:500], 'valido': r['valido']}
        except Exception:
            return {'codigo': '-- NPC template', 'valido': False}

    def _tool_criar_codigo(self, tarefa: str) -> Dict:
        try:
            from mcr.gerador_codigo import GeradorCodigo
            g = GeradorCodigo()
            r = g.gerar('lua', 'function', passos=15)
            g.close()
            return {'codigo': r['codigo'][:500], 'valido': r['valido']}
        except Exception:
            return {'codigo': '-- code template', 'valido': False}

    def _tool_analisar_texto(self, tarefa: str) -> Dict:
        return self.compreender(tarefa)

    def _tool_gerar_sprite(self, tarefa: str) -> Dict:
        return {'mensagem': 'Geracao de sprite via MCRSpriteMotor (FASE futura)',
                'status': 'nao_implementado'}

    def _tool_raciocinar(self, tarefa: str) -> Dict:
        return self.raciocinar(tarefa)

    def close(self):
        self.mcr.conn.close()


# ─── Teste ───────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print('  Raciocinador — Teste (FASE 5-7)')
    print('=' * 60)

    r = Raciocinador()

    # FASE 5: Compreensao
    print('\n[FASE 5] Compreensao de Texto')
    texto = "O MCR e um motor cognitivo baseado em cadeias de Markov. "
    texto += "Ele usa entropia de Shannon para detectar estrutura vs ruido. "
    texto += "O sistema opera sem GPU, apenas com CPU e SQLite."
    analise = r.compreender(texto, 'O que e MCR?')
    print(f'  Fragmentos: {analise["fragmentos"]}')
    print(f'  Entropia: {analise["entropia"]}')
    print(f'  Top palavras: {analise["top_palavras"]}')
    print(f'  Resposta: {analise.get("resposta", "N/A")[:100]}')

    # FASE 6: Raciocinio
    print('\n[FASE 6] Raciocinio')
    # Silogismo
    r1 = r.raciocinar('Se A > B e B > C, entao A > C?')
    print(f'  Silogismo: {r1["tipo"]} -> {r1["conclusao"][:100]}')
    # Matematica
    r2 = r.raciocinar('Quanto e 15 + 27 * 2?')
    print(f'  Matematica: {r2.get("resultado")}')

    # FASE 7: Tool Use
    print('\n[FASE 7] Tool Use')
    ferramenta = r.escolher_ferramenta('crie um npc ferreiro')
    print(f'  Para "crie um npc ferreiro" -> {ferramenta}')
    resultado = r.usar_ferramenta('crie um npc ferreiro')
    print(f'  Sucesso: {resultado["sucesso"]}, Ferramenta: {resultado.get("ferramenta")}')

    ferramenta2 = r.escolher_ferramenta('analise este texto sobre magia')
    print(f'  Para "analise este texto" -> {ferramenta2}')

    r.close()
    print('\nOK')
