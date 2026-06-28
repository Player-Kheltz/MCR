"""Modulo: KnowledgeGraph - Gerenciamento de conhecimento do MCR-DevIA.
Pode ser carregado pelo kernel ou importado diretamente."""
import os, json, re, hashlib

# Paths dinamicos
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
STOP_BUSCA = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'das', 'dos',
    'em', 'no', 'na', 'nos', 'nas', 'para', 'pra', 'por', 'com', 'sem', 'sob',
    'entre', 'como', 'que', 'qual', 'quais', 'quem', 'quando', 'onde', 'se',
    'ele', 'ela', 'eles', 'elas', 'voce', 'nos', 'meu', 'sua', 'seu', 'isso',
    'isto', 'aquele', 'essa', 'este', 'tem', 'ter', 'ser', 'estar', 'foi',
    'era', 'sao', 'sao', 'e', 'nao', 'mais', 'mas', 'muito', 'pouco', 'ja',
    'ainda', 'tambem', 'ate', 'apos', 'antes', 'depois', 'sempre', 'nunca',
    'aqui', 'ali', 'la', 'todo', 'tudo', 'todos', 'cada', 'algum', 'nenhum',
    'outro', 'mesmo', 'assim', 'bem', 'mal', 'sim', 'nao', 'talvez', 'entao',
    'apenas', 'so', 'quase', 'tipo', 'forma', 'maneira', 'exemplo', 'caso',
    'vez', 'coisa', 'gente', 'pessoa', 'dia', 'ano', 'mes', 'hora', 'minuto'}

def init_module(contexto):
    """Inicializa modulo KG e retorna instancia."""
    kg = KnowledgeGraph()
    contexto['kg'] = kg
    return 'kg', kg


class KnowledgeGraph:
    """Graph de conhecimento do MCR-DevIA. Persistente em knowledge.json."""
    
    def __init__(self):
        self.path = KG_PATH
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return self._licoes_iniciais()
    
    def _licoes_iniciais(self):
        return {
            "versoes": 1,
            "licoes": [
                {'id':'L001','erro':'LNK2001 __std_*','causa':'ABI mismatch','solucao':'Usar VS 2026','ctx':'compilar'},
                {'id':'L002','erro':'D9002 /std:c++latest','causa':'stdcpp23','solucao':'stdcpp20','ctx':'compilar'},
                {'id':'L003','erro':'string_view::contains','causa':'C++23','solucao':'find()!=npos','ctx':'compilar'},
            ],
            "index": {},
            "metricas": {"licoes": 3, "usos": 0, "geracoes": 0, "compilacoes": 0},
            "lessons": []
        }
    
    def salvar(self):
        self.data['versoes'] += 1
        self.data['metricas']['licoes'] = len(self.data['licoes'])
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def buscar(self, texto, max_r=5, incluir_inativos=False):
        palavras = set(re.findall(r'\w+', texto.lower())) - STOP_BUSCA
        scores = []
        for l in self.data['licoes']:
            if not incluir_inativos and l.get('inactive', False):
                continue
            alvo = l['erro'].lower() + ' ' + l.get('causa','').lower() + ' ' + l['solucao'].lower()
            score = 0
            for p in palavras:
                if len(p) < 3: continue
                if p in alvo:
                    if p in l['erro'].lower(): score += 5
                    elif p in l.get('ctx','').lower(): score += 4
                    elif p in l.get('causa','').lower(): score += 3
                    else: score += 2
            if score > 0: scores.append((score, l))
        scores.sort(key=lambda x: -x[0])
        return [s[1] for s in scores[:max_r]]
    
    def purgar(self, manter_ctxs=None):
        if manter_ctxs is None:
            manter_ctxs = set()
            for l in self.data['licoes']:
                ctx = l.get('ctx', '')
                if ctx and not l.get('inactive', False):
                    manter_ctxs.add(ctx)
            if not manter_ctxs:
                manter_ctxs = {'identidade'}
        count = 0
        for l in self.data['licoes']:
            lid = l.get('id', '')
            if lid.startswith('L') and len(lid) <= 5 and int(lid[1:]) <= 100:
                continue
            ctx = l.get('ctx', 'geral')
            if ctx in manter_ctxs:
                continue
            if ctx in ('weblearn', 'learning_scan', 'weblearn_permanente', 'pipeline_busca'):
                if not l.get('inactive', False):
                    l['inactive'] = True
                    count += 1
        self.salvar()
    
    def aprender(self, erro, causa, solucao, ctx='geral'):
        lid = f'L{len(self.data["licoes"])+1:04d}'
        self.data['licoes'].append({
            'id': lid, 'erro': erro[:80], 'causa': causa[:200],
            'solucao': solucao[:500], 'ctx': ctx, 'usos': 0
        })
        self.salvar()
    
    def gerar_licoes(self, dominio, quantidade=5):
        """Gera licoes para um dominio e salva no KG.
        Extraido do mcr_knowledge.py legacy.
        Retorna numero de licoes geradas."""
        try:
            from modulos.util import gerar as _gerar_k
        except:
            print(f'[KG] gerar_licoes: router nao disponivel')
            return 0
        
        temas = {
            'mcr': ['SPA', 'SHC', 'Dominios Elementais', 'Canary', 'OTClient',
                    'Eridanus', 'Sistema de Progressao', 'Habilidades Contextuais'],
            'codigo': ['monster', 'npc', 'item', 'spell', 'quest', 'creature',
                      'event', 'action', 'talkaction', 'movement'],
        }
        temas_dominio = temas.get(dominio, [dominio])
        
        contagem = 0
        import random
        random.shuffle(temas_dominio)
        
        for tema in temas_dominio[:quantidade]:
            prompt = (
                f"Crie uma licao sobre '{tema}' para o projeto MCR (Tibia/Canary).\n"
                f"Responda no formato:\n"
                f"PERGUNTA: (pergunta sobre o tema)\n"
                f"RESPOSTA: (explicacao em 2-3 frases)\n"
                f"CATEGORIA: {dominio}\n"
            )
            try:
                resp = _gerar_k(prompt, 0.3, "fast") or ""
                if resp and len(resp) > 50:
                    self.aprender(
                        erro=f"O que e {tema}?",
                        causa=f"Lesson gerada para dominio: {dominio}",
                        solucao=resp.strip()[:500],
                        ctx=f"licao_{dominio}"
                    )
                    contagem += 1
                    print(f'  [KG] Licao gerada: {tema}')
            except:
                pass
        
        return contagem
