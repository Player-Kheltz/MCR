"""Comando: conectar - Thinker de conexoes: busca conexoes entre dominios no KG."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "conectar",
        "desc": "Thinker de conexoes: busca conexoes entre dominios no KG.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Thinker de conexoes: busca conexoes entre dominios no KG."""
    print(f'[Conector] Buscando conexoes entre lessons...')
    import json, random
    kg_path = os.path.join(_SANDBOX, '.mcr_devia', 'knowledge.json')
    kg_dir = os.path.join(_SANDBOX, '.mcr_devia', 'kg')
    # Carrega lessons do multi-arquivo
    if os.path.exists(kg_dir):
        licoes = []
        for fname in sorted(os.listdir(kg_dir)):
            if not fname.endswith('.json') or fname == 'master.json': continue
            try:
                with open(os.path.join(kg_dir, fname), 'r', encoding='utf-8') as f:
                    licoes.extend(json.load(f).get('licoes', []))
            except: pass
        kg_data = {'licoes': licoes}
    elif os.path.exists(kg_path):
        with open(kg_path, encoding='utf-8') as f:
            kg_data = json.load(f)
    else:
        print('  KG nao encontrado')
        return
        lessons = kg.get('lessons', [])
        if len(lessons) >= 2:
            for _ in range(5):
                l1, l2 = random.sample(lessons, 2)
                ctx1 = l1.get('context', '?')
                ctx2 = l2.get('context', '?')
                # Conexao via palavras-chave
                palavras1 = set(str(l1).lower().split())
                palavras2 = set(str(l2).lower().split())
                comuns = palavras1 & palavras2
                if len(comuns) > 5:
                    print(f'  {ctx1} <-> {ctx2}: {len(comuns)} palavras em comum')
        else:
            print('[Conector] Menos de 2 lessons no KG')
    return True
