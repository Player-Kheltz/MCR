"""Auto-Revisor: MCR-DevIA revisa a PROPRIA resposta pos-geracao.
Detecta alucinacoes (classes inventadas), nomes inconsistentes, e auto-corrige.

FLUXO:
1. Orquestrador gera resposta
2. AutoRevisor.revisar(resposta, contexto) 
3. Detecta alucinacoes comparando com classes REAIS do projeto
4. Se encontrar, registra no KG e RETORNA correcoes
5. Watchdog pode disparar AutoRevisor em arquivos do sandbox/
"""
import os, re, json, time

# Classes REAIS do projeto (conhecidas no codigo)
# MCR-DevIA pode aprender isso escaneando o projeto com grep
_CLASSES_REAIS = set()

def escanear_classes(diretorio_base=None):
    """Escaneia o projeto para encontrar classes REAIS definidas no codigo.
    Use: AutoRevisor.escanear_classes() para atualizar a lista."""
    global _CLASSES_REAIS
    
    if not diretorio_base:
        diretorio_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    classes = set()
    import subprocess
    
    try:
        # Usa grep para encontrar definicoes de classe em .py
        r = subprocess.run(
            ['grep', '-r', '-h', '-o', r'class \w+', '--include', '*.py',
             os.path.join(diretorio_base, 'scripts', 'mcr_devia')],
            capture_output=True, text=True, timeout=15
        )
        for linha in (r.stdout or '').split('\n'):
            if 'class ' in linha:
                classes.add(linha.replace('class ', '').strip())
        
        # Tambem busca no sandbox
        r2 = subprocess.run(
            ['grep', '-r', '-h', '-o', r'class \w+', '--include', '*.py',
             os.path.join(diretorio_base, 'sandbox')],
            capture_output=True, text=True, timeout=15
        )
        for linha in (r2.stdout or '').split('\n'):
            if 'class ' in linha:
                classes.add(linha.replace('class ', '').strip())
    except Exception:
        pass
    
    # Classes built-in comuns que sao validas
    classes_validas = {
        'ValueError', 'TypeError', 'KeyError', 'Exception', 'OSError',
        'IOError', 'RuntimeError', 'StopIteration', 'AttributeError',
        'ImportError', 'ModuleNotFoundError', 'FileNotFoundError',
        'PermissionError', 'TimeoutError', 'ConnectionError',
        'OrderedDict', 'defaultdict', 'deque', 'Counter',
        'ThreadPoolExecutor', 'ProcessPoolExecutor', 'Future',
        'asyncio', 'Path', 'PurePath', 'PathLike',
        'NamedTuple', 'dataclass', 'Enum', 'IntEnum',
        'Dict', 'List', 'Tuple', 'Set', 'FrozenSet',
        'Optional', 'Union', 'Any', 'Callable', 'Iterable',
        'Generator', 'Iterator', 'Awaitable', 'Coroutine',
        'HttpResponse', 'HttpRequest', 'JsonResponse',
    }
    classes.update(classes_validas)
    
    _CLASSES_REAIS = classes
    return classes


# Mapa de classes ESPECIFICAS por template/task
# Populated by escanear_classes() + lessons do KG
_CLASSES_POR_TEMPLATE = {
    "mega_teste": {"DataLake", "StreamSimulator", "ValidadorStream", "ErroStream"},
    "analisar_codigo": None,  # None = usa classes reais do projeto
}

class AutoRevisor:
    """Revisa respostas do MCR-DevIA procurando alucinacoes."""
    
    def __init__(self, kg=None):
        self.kg = kg
        if not _CLASSES_REAIS:
            escanear_classes()
    
    def _heuristico(self, classe, texto_completo):
        """Heuristica para detectar alucinacoes sem usar FAST.
        Universal: nao depende de listas fixas.
        
        Regras:
        1. Classe dentro de ```code``` = VALIDA (o modelo escreveu codigo, confia)
        2. Classe contextualizada no texto = VALIDA (aparece em 'A classe X faz...')
        3. Classe com 3+ maiusculas internas sem contexto = SUSPEITA
        4. Classe muito longa (10+ chars) com 4+ maiusculas = SUSPEITA
        """
        import re as _re
        
        # Regra 1: dentro de codigo = valido
        blocos = _re.findall(r'```(?:python)?\s*\n(.*?)```', texto_completo, _re.DOTALL)
        for bloco in blocos:
            if classe in bloco:
                return True
        
        # Regra 2: contextualizada no texto = valida
        contextos = [
            f"classe {classe}", f"Classe {classe}", f"A classe {classe}",
            f"'{classe}'", f'"{classe}"', f"`{classe}`",
            f"class {classe}", f"def {classe}",
        ]
        for ctx in contextos:
            if ctx in texto_completo:
                return True
        
        # Regra 3: nome composto suspeito (3+ maiusculas internas, 10+ chars)
        maiusculas = sum(1 for c in classe[1:] if c.isupper())
        if maiusculas >= 3 and len(classe) >= 10:
            return False  # Suspeito: ex: HyperNovaQuantumProcessor
        
        # Regra 4: 2+ maiusculas internas e nao e ingles conhecido
        if maiusculas >= 2 and len(classe) > 8:
            # Lista de palavras inglesas conhecidas que podem aparecer em CamelCase
            conhecidos = {'And', 'The', 'For', 'With', 'From', 'Into', 'Over', 'Under'}
            partes = _re.findall(r'[A-Z][a-z]*', classe)
            if not all(p in conhecidos for p in partes[1:]):
                return False  # Suspeito
        
        return True  # Aceita por duvida

    def revisar(self, texto_resposta, classes_permitidas=None, pergunta_original=""):
        """Revisa uma resposta. Retorna dict com alucinacoes encontradas.
        Usa heuristica universal (sem listas fixas, sem FAST).
        
        Args:
            texto_resposta: Texto da resposta gerada
            classes_permitidas: Ignorado (mantido para compatibilidade)
            pergunta_original: Pergunta original (para verificar generica)
        
        Returns:
            dict com {alucinacoes: [(classe, contexto)], total: N, sugestao: str, generica: bool}
        """
        if not texto_resposta:
            return {"alucinacoes": [], "total": 0, "sugestao": "", "generica": False}
        
        # So analisa TEXTO (fora de blocos ```code```)
        partes = re.split(r'```(?:python)?\s*\n.*?```', texto_resposta, flags=re.DOTALL)
        texto_limpo = ' '.join(partes)
        
        # Encontra possiveis nomes de classe no texto limpo
        candidatos = set(re.findall(r'\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b', texto_limpo))
        
        # Adiciona classes apos 'class ' ou 'def '
        candidatos.update(re.findall(r'(?:class|def)\s+([A-Z][a-zA-Z]+)', texto_resposta))
        
        # Filtra candidatos usando heuristica
        alucinacoes = []
        for c in sorted(candidatos):
            if not self._heuristico(c, texto_resposta):
                pos = texto_resposta.find(c)
                ctx = texto_resposta[max(0,pos-40):pos+len(c)+40].replace('\n', ' ')
                alucinacoes.append((c, ctx))
        
        sugestao = ""
        if alucinacoes:
            classes_str = ', '.join(a[0] for a in alucinacoes)
            sugestao = f"Classes suspeitas encontradas: {classes_str}. Verifique se existem no projeto."
        
        resultado = {
            "alucinacoes": alucinacoes,
            "total": len(alucinacoes),
            "sugestao": sugestao,
            "generica": False,
        }
        
        # ENRICHER CHECK: se resposta e muito curta e pergunta foi fornecida,
        # verifica se Enricher teria gerado conteudo util
        if pergunta_original and len(texto_resposta) < 500:
            try:
                from modulos.context_enricher import ContextEnricher
                enricher = ContextEnricher(kg=self.kg)
                enr = enricher.enriquecer(pergunta_original)
                if enr.get('valido') and enr.get('conteudo'):
                    resultado['generica'] = True
                    resultado['sugestao'] += ' | Resposta parece generica. Enricher poderia ter enriquecido.'
                    print(f'  [Auto-Revisor] Resposta GENERICA detectada (Enricher disponivel)')
            except Exception:
                pass
        
        # Registra no KG se tiver acesso
        if resultado["total"] > 0 and self.kg:
            try:
                self.kg.aprender(
                    f"auto_revisor: {alucinacoes[0][0]}",
                    f"alucinacao detectada",
                    f"classes={classes_str}, total={resultado['total']}",
                    "auto_revisor"
                )
            except Exception:
                pass
        
        # ===== PATTERN ENGINE CHECKS (eixo + entropia + n-grama) =====
        try:
            from modulos.pattern_engine import PatternEngine
            _pe = PatternEngine()
            _tokens = _pe.tokenizar(texto_resposta, 'texto')
            _padroes = _pe.extrair_padroes(_tokens)
            _eixo = _pe.eixo_nirvana_caos(_tokens)
            
            # Eixo check
            resultado['eixo'] = round(_eixo, 3)
            if _eixo < 0.4:
                resultado['sugestao'] += f' | Eixo baixo ({_eixo:.2f}) — resposta caotica'
                resultado['total'] += 1
                alucinacoes.append(('EIXO_CAOS', f'eixo={_eixo:.2f}'))
            
            # Entropia check
            _entropia = _padroes.get('entropia', 0.5)
            resultado['entropia'] = round(_entropia, 3)
            if _entropia > 0.8:
                resultado['sugestao'] += f' | Entropia alta ({_entropia:.2f}) — resposta aleatoria'
                resultado['total'] += 1
                alucinacoes.append(('ENTROPIA_ALTA', f'entropia={_entropia:.2f}'))
            
            # N-grama repeticao check
            _n_gramas = _padroes.get('n_gramas', {})
            _trigramas = list(_n_gramas.get(3, {}).keys()) if isinstance(_n_gramas, dict) else []
            if _trigramas and len(texto_resposta) > 200:
                # Conta repeticoes de trigramas
                from collections import Counter
                palavras = re.findall(r'\w+', texto_resposta.lower())
                trigramas = [' '.join(palavras[i:i+3]) for i in range(len(palavras)-2)]
                repeticoes = sum(1 for _, count in Counter(trigramas).items() if count > 2)
                if repeticoes > len(trigramas) * 0.1:  # mais de 10% de repeticoes
                    resultado['sugestao'] += f' | {repeticoes} trigramas repetidos — resposta em loop'
                    resultado['total'] += 1
                    alucinacoes.append(('LOOP_NGRAMA', f'{repeticoes} trigramas repetidos'))
        except Exception:
            pass
        
        return resultado
    
    def auto_corrigir(self, texto_resposta, classes_permitidas=None):
        """Auto-corrige alucinacoes: marca classes suspeitas APENAS no texto, nao em codigo."""
        resultado = self.revisar(texto_resposta, classes_permitidas)
        if resultado["total"] == 0:
            return texto_resposta, resultado
        
        # Divide em blocos de codigo e texto
        import re
        partes = re.split(r'(```(?:python)?\s*\n)', texto_resposta)
        dentro_codigo = False
        corrigido = []
        
        for parte in partes:
            if parte.startswith("```"):
                dentro_codigo = not dentro_codigo
                corrigido.append(parte)
                continue
            if dentro_codigo:
                corrigido.append(parte)  # Nao modifica dentro de codigo
            else:
                # So marca no texto
                for classe, _ in resultado["alucinacoes"]:
                    if classe in parte:
                        parte = parte.replace(classe, f"{classe}[?]")
                corrigido.append(parte)
        
        return ''.join(corrigido), resultado
    
    # ============================================================
    # VALIDADORES DE CODIGO (extraidos do crew_deepseek.py legacy)
    # ============================================================
    
    def validar_python(self, codigo):
        """Valida código Python com AST. Retorna (valido, erro)."""
        import ast
        try:
            ast.parse(codigo)
            return True, ""
        except SyntaxError as e:
            return False, f"SyntaxError: {e}"
    
    def validar_lua(self, codigo):
        """Valida código Lua com regras basicas (sem compilador nativo).
        Retorna (valido, explicacao)."""
        problemas = []
        if codigo.count("function") != codigo.count("end"):
            problemas.append("function/end mismatch")
        ends = codigo.count("end")
        functions = codigo.count("function")
        ifs = codigo.count("if")
        if ends < functions + ifs:
            problemas.append("if/function sem end")
        if codigo.count("(") != codigo.count(")"):
            problemas.append("parentheses mismatch")
        valido = len(problemas) == 0
        return valido, "; ".join(problemas) if problemas else ""
    
    def validar_termos_contra_kg(self, texto, kg=None):
        """Valida se termos compostos no texto existem no KG.
        Retorna (valido, suspeitos)."""
        if not kg:
            return True, []
        termos_compostos = set(re.findall(r"[A-Z][a-z]+\s+[A-Z][a-z]+", texto))
        suspeitos = []
        for termo in termos_compostos:
            tl = termo.lower().strip()
            existe = False
            try:
                results = kg.buscar(tl, max_r=3)
                for r in results:
                    texto_kg = (r.get('erro','') + ' ' + r.get('solucao','') + 
                               ' ' + r.get('causa','') + ' ' + r.get('ctx','')).lower()
                    if tl in texto_kg:
                        existe = True
                        break
            except Exception:
                pass
            if not existe:
                suspeitos.append(termo)
        if suspeitos:
            return False, suspeitos
        return True, []


# ============================================================
# INTEGRACAO COM O ORQUESTRADOR
# ============================================================
def init_module(contexto):
    """Inicializa o AutoRevisor como modulo do kernel."""
    kg = contexto.get('kg')
    ar = AutoRevisor(kg=kg)
    contexto['auto_revisor'] = ar
    return 'auto_revisor', ar


if __name__ == "__main__":
    # Teste
    escanear_classes()
    print(f"Classes reais encontradas: {len(_CLASSES_REAIS)}")
    print(f"Exemplos: {list(_CLASSES_REAIS)}")
    
    revisor = AutoRevisor()
    teste = "A classe DataLoader faz a carga e DataProcessor transforma. DataLake e StreamSimulator sao reais."
    res = revisor.revisar(teste, {"DataLake", "StreamSimulator"})
    print(f"\nAlucinacoes detectadas: {res['total']}")
    for c, ctx in res['alucinacoes']:
        print(f"  {c}: ...{ctx}...")
