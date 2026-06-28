"""Context Enricher Universal — Gera contexto NOVO para enriquecer respostas.
Em vez de apenas BUSCAR contexto (ContextCrew), o Enricher CRIA conteudo:
- Nomes proprios para lore (FAST + validacao)
- Dados tecnicos (grep + leitura de codigo)
- Curiosidades (weblearn + KG)
- Comparacoes estruturadas (FAST sobre dados do KG)

Integrado no pipeline: CR → ENRICHER → ORQUESTRADOR
"""
import os, sys, json, time, re, subprocess, hashlib

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

# Cache LRU: (hash da pergunta) -> (timestamp, conteudo)
_CACHE_ENRICHER = {}
_CACHE_TTL = 300  # 5 minutos
_CACHE_MAX = 32

# Palavras que indicam alucinacao (devem ser descartadas)
_ALUCINACOES = {'minecraft', 'docker', 'kubernetes', 'microserviço', 'single page application',
                'software as a service', 'wotc', 'wizards of the coast', 'd&d', 'aws', 'azure'}

def _fast(prompt, temp=0.2):
    """Chamada rapida ao modelo leve para classificacao."""
    try:
        from modulos.util import fast as _util_fast
        return _util_fast(prompt, temp, "fast") or ""
    except:
        return ""

def _gerar(prompt, temp=0.3, tarefa="leve"):
    """Chamada ao modelo para geracao de conteudo."""
    try:
        from modulos.util import gerar as _util_gerar
        return _util_gerar(prompt, temp, tarefa) or ""
    except:
        return ""

def _carregar_identidade():
    """Carrega MCR_IDENTITY para contexto tematico."""
    try:
        with open(os.path.join(BASE, 'docs', 'MCR_IDENTITY.md'), 'r', encoding='utf-8') as f:
            return f.read()[:800]
    except:
        return ""


class ContextEnricher:
    """Gera contexto NOVO para enriquecer respostas."""
    
    def __init__(self, ctx_crew=None, kg=None):
        self.ctx_crew = ctx_crew
        self.kg = kg
    
    def enriquecer(self, pergunta: str, termos: list = None) -> dict:
        """Ciclo completo: classifica, gera, valida, cacheia.
        
        Args:
            pergunta: Texto original da pergunta
            termos: Termos extraidos (opcional, do CR). Se None, extrai da pergunta.
        
        Returns:
            dict: {tipo, conteudo, valido}
        """
        # Se nao tem termos, extrai palavras-chave da pergunta
        if not termos:
            import re
            termos = re.findall(r'[a-zA-Z.]{2,}', pergunta)
            stop = {'de','para','que','com','uma','era','mais','como','por','seu','sua',
                    'tem','ela','ele','voce','me','te','se','nos','lhe','das','dos',
                    'nas','nem','mas','sobre','isto','isso','aquele','este','essa'}
            termos = [t for t in termos if t.lower() not in stop][:8]
        
        h = hashlib.md5(pergunta.lower().encode()).hexdigest()[:12]
        if h in _CACHE_ENRICHER:
            ts, cached = _CACHE_ENRICHER[h]
            if time.time() - ts < _CACHE_TTL:
                return cached
        
        t0 = time.time()
        
        # 1. Classifica carencia
        tipo = self._classificar_carencia(pergunta)
        
        # 2. Gera conteudo
        conteudo = ""
        if tipo == 'lore_nomes':
            conteudo = self._gerar_lore(pergunta)
        elif tipo == 'lore_eventos':
            conteudo = self._gerar_lore_eventos(pergunta)
        elif tipo == 'tecnico_detalhes':
            conteudo = self._gerar_tecnico(termos)
        elif tipo == 'tecnico_dados':
            conteudo = self._gerar_dados(pergunta, termos)
        elif tipo == 'factual_curiosidade':
            conteudo = self._gerar_curiosidades(pergunta)
        elif tipo == 'comparacao':
            conteudo = self._gerar_comparacao(pergunta)
        elif tipo == 'generico_reforco':
            conteudo = self._gerar_reforco_generico(pergunta)
        
        # 3. Valida
        valido = self._validar(conteudo, tipo)
        
        resultado = {
            'tipo': tipo,
            'conteudo': conteudo,
            'valido': valido,
            'tempo': round(time.time() - t0, 1),
        }
        
        # Cache
        _CACHE_ENRICHER[h] = (time.time(), resultado)
        if len(_CACHE_ENRICHER) > _CACHE_MAX:
            mais_antiga = min(_CACHE_ENRICHER.keys(), key=lambda k: _CACHE_ENRICHER[k][0])
            del _CACHE_ENRICHER[mais_antiga]
        
        return resultado
    
    def _classificar_carencia(self, pergunta: str) -> str:
        """FAST classifica o que esta faltando na resposta."""
        p = pergunta.lower()
        
        # Heuristica rapida (0 IA) para casos obvios
        palavras_lore = ['crie uma lore', 'crie uma historia', 'conte uma historia',
                        'descreva', 'lore para', 'historia de', 'npc', 'personagem',
                        'cidade', 'reino', 'artefato', 'item magico']
        palavras_tecnico = ['codigo', 'arquivo', 'funcao', 'classe', 'metodo',
                           'implemente', 'crie um', 'gere', 'como funciona',
                           'o que e .lua', 'o que e .py']
        palavras_comparacao = ['diferenca', 'vs', 'versus', 'comparacao',
                              'qual a diferenca', 'compare']
        palavras_dados = ['quantos', 'quanto', 'qual o numero', 'versoes',
                         'dominios', 'niveis', 'atributos']
        
        if any(p in palavras_lore for p in p.split()):
            return 'lore_nomes'
        if any(kw in p for kw in palavras_comparacao):
            return 'comparacao'
        if any(kw in p for kw in palavras_tecnico):
            return 'tecnico_detalhes'
        if any(kw in p for kw in palavras_dados):
            return 'tecnico_dados'
        
        # Fallback: FAST decide
        prompt = (
            f"{_carregar_identidade()[:400]}\n\n"
            f"Pergunta: {pergunta[:300]}\n\n"
            "Classifique em UMA palavra o que esta FALTANDO para responder "
            "esta pergunta de forma NAO GENERICA:\n"
            "- lore_nomes: precisa de nomes proprios, personagens, lugares\n"
            "- lore_eventos: precisa de historia, fundacao, eras\n"
            "- tecnico_detalhes: precisa de codigo, arquivos, APIs\n"
            "- tecnico_dados: precisa de numeros, versoes, metricas\n"
            "- factual_curiosidade: precisa de fatos interessantes\n"
            "- comparacao: precisa de comparacao estruturada\n"
            "- generico_reforco: precisa de qualquer enriquecimento\n\n"
            "Resposta (apenas uma palavra):"
        )
        resp = _fast(prompt, 0.15)
        tipos_validos = ['lore_nomes', 'lore_eventos', 'tecnico_detalhes',
                        'tecnico_dados', 'factual_curiosidade', 'comparacao',
                        'generico_reforco']
        for t in tipos_validos:
            if t in resp.lower():
                return t
        return 'generico_reforco'
    
    def _gerar_lore(self, pergunta: str) -> str:
        """Gera nomes proprios para enriquecer lore."""
        identidade = _carregar_identidade()[:400]
        prompt = (
            f"{identidade}\n\n"
            f"Tema: {pergunta[:300]}\n\n"
            "Gene 5-8 NOMES PROPRIOS CRIATIVOS em portugues para este tema.\n"
            "Separe cada nome com virgula. NAO use colchetes ou marcadores.\n\n"
            "Exemplo:\n"
            "Mestra Aurora, Guardiao Pyralis, Lago das Chamas Eternas, Cristal de Fogo Submerso, Floresta dos Ventos, Templo do Equilibrio\n\n"
            "Apenas os nomes, sem introducao ou explicacao:"
        )
        resp = _gerar(prompt, 0.4, "texto")
        
        # Extrai nomes (qualquer coisa com letra maiuscula seguida de minusculas, com 3+ chars)
        nomes = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+(?:de|da|do|das|dos|e|[A-Z][a-z]{2,})){0,4}', resp)
        nomes = [n.strip() for n in nomes if len(n.strip()) > 4]
        
        # Se poucos nomes, tenta de novo com prompt mais direto
        if len(nomes) < 4:
            prompt2 = (
                f"{identidade}\n\n"
                f"Tema: {pergunta[:200]}\n\n"
                "Liste 6 nomes proprios em portugues para este tema.\n"
                "FORMATO: nome1, nome2, nome3, nome4, nome5, nome6\n"
                "EXEMPLO: Lady Elara, Templo Solar, Espada da Aurora, Vale dos Ventos\n\n"
                "Nomes:"
            )
            resp2 = _gerar(prompt2, 0.5, "texto")
            nomes2 = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+(?:de|da|do|das|dos|e|[A-Z][a-z]{2,})){0,4}', resp2)
            nomes2 = [n.strip() for n in nomes2 if len(n.strip()) > 4]
            if len(nomes2) > len(nomes):
                nomes = nomes2
                resp = resp2
        
        if nomes and len(nomes) >= 3:
            bloco = "[CONTEXTO ENRIQUECIDO - Nomes e Lugares]\n"
            bloco += 'Use estes nomes na resposta: ' + ', '.join(nomes[:10])
            bloco += "\n[/CONTEXTO]\n"
            return bloco
        return ""
    
    def _gerar_lore_eventos(self, pergunta: str) -> str:
        """Gera eventos historicos para enriquecer lore."""
        prompt = (
            f"{_carregar_identidade()[:400]}\n\n"
            f"Tema: {pergunta[:300]}\n\n"
            "Gere 3 eventos historicos ficticios para enriquecer este tema.\n"
            "Cada evento: nome, ano/era, descricao curta, consequencia.\n"
            "Use nomes proprios em portugues.\n"
            "FORMATO:\n"
            "EVENTO 1: [nome] - [descricao] - [consequencia]\n"
            "EVENTO 2: [nome] - [descricao] - [consequencia]\n"
            "EVENTO 3: [nome] - [descricao] - [consequencia]"
        )
        resp = _gerar(prompt, 0.4, "texto")
        if resp and len(resp) > 100:
            return f"\n[CONTEXTO ENRIQUECIDO - Eventos]\n{resp[:2000]}\n[/CONTEXTO]\n"
        return ""
    
    def _gerar_tecnico(self, termos: list) -> str:
        """Busca dados TECNICOS REAIS usando ferramentas (grep em Python puro)."""
        partes = []
        
        # Diretorios para buscar
        dirs_busca = [
            os.path.join(BASE, 'scripts', 'mcr_devia'),
            os.path.join(BASE, 'Canary', 'src'),
            os.path.join(BASE, 'OTClient', 'src'),
            os.path.join(BASE, 'Canary', 'data-canary', 'scripts'),
        ]
        
        # 1. Busca por termo nos arquivos (sem grep, em Python puro)
        for termo in termos[:5]:
            if len(termo) < 2:
                continue
            termo_lower = termo.lower()
            for start_dir in dirs_busca:
                if not os.path.exists(start_dir):
                    continue
                try:
                    for root, dirs, files in os.walk(start_dir):
                        # Limita profundidade (10 niveis max)
                        if root.count(os.sep) > start_dir.count(os.sep) + 10:
                            continue
                        for f in files:
                            ext = os.path.splitext(f)[1].lower()
                            if ext not in ('.py', '.cpp', '.h', '.hpp', '.lua', '.txt', '.md'):
                                continue
                            fpath = os.path.join(root, f)
                            try:
                                if os.path.getsize(fpath) > 50000:  # Max 50KB
                                    continue
                                with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                                    lines = fh.readlines()
                                for i, line in enumerate(lines):
                                    if termo_lower in line.lower():
                                        rel = os.path.relpath(fpath, BASE)
                                        partes.append(f"  {rel}:L{i+1}: {line.strip()[:150]}")
                                        break  # 1 linha por arquivo
                            except:
                                pass
                except:
                    pass
        
        # 2. Usa import glob para achar arquivos com a extensao do termo
        # Ex: se termo = ".lua", busca arquivos *.lua
        for termo in termos[:3]:
            t = termo.strip().lower()
            if t.startswith('.'):
                ext = t
                for start_dir in dirs_busca:
                    if not os.path.exists(start_dir):
                        continue
                    count = 0
                    for root, dirs, files in os.walk(start_dir):
                        for f in files:
                            if f.endswith(ext):
                                rel = os.path.relpath(os.path.join(root, f), BASE)
                                if count < 5:
                                    partes.append(f"  {rel}")
                                    count += 1
                                else:
                                    break
                        if count >= 5:
                            break
        
        # 3. Busca no KG se disponivel
        if self.kg:
            try:
                lessons = self.kg.buscar(' '.join(termos[:5]), max_r=5)
                for l in lessons:
                    sol = l.get('solucao', '').strip()
                    ctx_tag = l.get('ctx', '')
                    if sol and len(sol) > 50:
                        partes.append(f"  [KG:{ctx_tag}] {sol[:300]}")
            except:
                pass
        
        if partes:
            bloco = "[CONTEXTO ENRIQUECIDO - Dados Tecnicos]\n"
            bloco += '\n'.join(partes[:12])
            bloco += "\n[/CONTEXTO]\n"
            return bloco
        return ""
    
    def _gerar_dados(self, pergunta: str, termos: list) -> str:
        """Busca dados numericos e especificos."""
        # Tenta KG primeiro
        partes = []
        consulta = ' '.join(termos[:5]) if termos else pergunta[:100]
        if self.kg:
            try:
                lessons = self.kg.buscar(consulta, max_r=8)
                for l in lessons:
                    sol = l.get('solucao', '').strip()
                    ctx_tag = l.get('ctx', '')
                    if sol and len(sol) > 40:
                        # Prioriza lessons com dados numericos
                        if any(c.isdigit() for c in sol):
                            partes.insert(0, f"[KG:{ctx_tag}] {sol[:400]}")
                        else:
                            partes.append(f"[KG:{ctx_tag}] {sol[:400]}")
            except:
                pass
        
        if partes:
            bloco = "[CONTEXTO ENRIQUECIDO - Dados Especificos]\n"
            bloco += '\n'.join(partes[:8])
            bloco += "\n[/CONTEXTO]\n"
            return bloco
        return ""
    
    def _gerar_curiosidades(self, pergunta: str) -> str:
        """Busca curiosidades via WebLearn + KG."""
        partes = []
        
        # WebLearn
        if self.ctx_crew:
            try:
                ctx = self.ctx_crew.executar(pergunta)
                if ctx and len(ctx) > 50:
                    # Extrai partes interessantes (nao genericas)
                    for line in ctx.split('\n'):
                        if len(line) > 60 and not any(g in line.lower()
                            for g in ['generico', 'exemplo', 'informacao']):
                            partes.append(f"[WebLearn] {line[:300]}")
            except:
                pass
        
        if not partes and self.kg:
            try:
                lessons = self.kg.buscar(pergunta[:100], max_r=5)
                for l in lessons:
                    sol = l.get('solucao', '').strip()
                    if sol and len(sol) > 80:
                        partes.append(f"[KG] {sol[:400]}")
            except:
                pass
        
        if partes:
            bloco = "[CONTEXTO ENRIQUECIDO - Curiosidades]\n"
            bloco += '\n'.join(partes[:5])
            bloco += "\n[/CONTEXTO]\n"
            return bloco
        return ""
    
    def _gerar_comparacao(self, pergunta: str) -> str:
        """Gera estrutura de comparacao."""
        prompt = (
            f"{_carregar_identidade()[:400]}\n\n"
            f"Pergunta: {pergunta[:300]}\n\n"
            "Crie UMA TABELA de comparacao em formato texto:\n"
            "| Item | Caracteristica 1 | Caracteristica 2 | ... |\n"
            "|------|-----------------|-----------------|-----|\n"
            "Use dados do contexto do projeto MCR.\n"
            "Responda em PT-BR."
        )
        resp = _gerar(prompt, 0.3, "texto")
        if resp and '|' in resp and len(resp) > 100:
            return f"\n[CONTEXTO ENRIQUECIDO - Comparacao]\n{resp[:1500]}\n[/CONTEXTO]\n"
        return ""
    
    def _gerar_reforco_generico(self, pergunta: str) -> str:
        """Tenta qualquer enriquecimento disponivel."""
        # Tenta tudo e pega o que funcionar
        resultados = []
        
        lore = self._gerar_lore(pergunta)
        if lore:
            resultados.append(lore)
        
        tec = self._gerar_tecnico([pergunta])
        if tec:
            resultados.append(tec)
        
        if resultados:
            return '\n'.join(resultados[:3])
        return ""
    
    def _validar(self, conteudo: str, tipo: str) -> bool:
        """Valida se o enriquecimento e util."""
        if not conteudo or len(conteudo) < 40:
            return False
        
        conteudo_lower = conteudo.lower()
        
        # Verifica alucinacoes (mas ignora se for negacao)
        for aluc in _ALUCINACOES:
            if aluc in conteudo_lower:
                # Verifica se e negacao (busca contexto ao redor)
                idx = conteudo_lower.find(aluc)
                ctx_antes = conteudo_lower[max(0, idx-50):idx]
                negacoes = ['nao e ', 'nao sendo ', 'nao se trata de ',
                           'diferente de ', 'ao contrario de ', 'em vez de ',
                           'nao confundir', 'nao se refere a', 'nao significa',
                           'não é ', 'não sendo ', 'não se trata de ',
                           'não confundir', 'não se refere a', 'não significa']
                if any(neg in ctx_antes for neg in negacoes):
                    continue  # Negacao, nao e alucinacao
                print(f'  [Enricher] Conteudo rejeitado: contem "{aluc}"')
                return False
        
        # Validacao por tipo
        if tipo == 'lore_nomes':
            nomes = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+(?:de|da|do|das|dos|e|[A-Z][a-z]{2,})){0,4}', conteudo)
            nomes_validos = [n for n in nomes if len(n.strip()) > 4]
            if len(nomes_validos) < 3:
                print(f'  [Enricher] Lore rejeitada: apenas {len(nomes_validos)} nomes proprios')
                return False
        
        if tipo == 'tecnico_detalhes':
            # Precisa ter caminhos de arquivo, codigo ou termos tecnicos
            tech_indicators = ['.py', '.cpp', '.lua', '.h', 'scripts/', 'Canary/',
                              'OTClient/', 'funcao', 'classe', 'metodo', 'arquivo']
            if not any(m in conteudo for m in tech_indicators):
                print(f'  [Enricher] Tecnico rejeitado: sem referencias a codigo')
                return False
        
        return True
