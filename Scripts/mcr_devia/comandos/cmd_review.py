"""Comando: review - Revisa dados extraidos usando Orquestrador Universal."""
import os, sys, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, _get_modelo, BASE as _BASE, SANDBOX as _SANDBOX, OLLAMA_URL as _OLLAMA_URL

def register():
    return {
        "name": "review",
        "desc": "Revisa dados extraidos usando Orquestrador Universal (prompt sob demanda)",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Revisa dados extraidos com Orquestrador Universal.
    Uso: python mcr_devia.py review <arquivo> [limite]
    Fluxo: extract -> review -> extract aplicar --force
    """
    path_review = args[0]
    limite = int(args[1]) if len(args) > 1 else 20
    ext_dir = os.path.join(os.path.dirname(path_review), '_extract') if os.path.isdir(os.path.dirname(path_review)) else None
    
    if not ext_dir or not os.path.exists(ext_dir):
        print(f'[Review] Nenhum dado extraido encontrado. Execute extract primeiro.')
        return True
    
    import urllib.request as ur_rv
    import json as json_rv
    
    for fname in sorted(os.listdir(ext_dir)):
        if not fname.endswith('.json') or fname == '_metadata.json':
            continue
        json_path = os.path.join(ext_dir, fname)
        with open(json_path, encoding='utf-8') as f:
            dados = json_rv.load(f)
        if not isinstance(dados, list):
            continue
        
        print(f'\n[Review] Revisando {fname} ({len(dados)} registros, limite {limite})...')
        suspeitos = []
        
        # Self few-shot (igual ao original)
        exemplos_few_shot = ""
        if len(dados) >= 3:
            saudavel = json_rv.dumps(dados[0], ensure_ascii=False)
            erros_gerados = []
            funcoes_erro = (
                lambda d: {**d, "artigo": "erro_artigo"} if "artigo" in d else d,
                lambda d: {**d, "plural": d.get("name", d.get("nome", "?")) + "_erro"} if "plural" in d else d,
            )
            for i in range(min(10, len(dados))):
                try:
                    item_err = funcoes_erro[i % 2](dict(dados[i]))
                    if item_err != dados[i]:
                        erros_gerados.append(json_rv.dumps(item_err, ensure_ascii=False))
                except:
                    pass
            if erros_gerados:
                exemplos_few_shot = f"Exemplo CORRETO:\n{saudavel}\n\n"
                for e in erros_gerados[:3]:
                    exemplos_few_shot += f"Exemplo ERRO:\n{e}\n\n"
        
        # Usar Orquestrador para gerar o prompt de review
        from modulos.orquestrador import Orquestrador
        orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx_crew)
        
        itens_lote = dados[:limite]
        lote_json = '\n'.join(
            f"ITEM {i+1}: {json_rv.dumps(item, ensure_ascii=False)}"
            for i, item in enumerate(itens_lote)
        )
        
        params = {
            "arquivo": fname,
            "total_registros": len(dados),
            "limite": limite,
            "few_shot": exemplos_few_shot[:1000],
            "itens": lote_json[:3000],
        }
        
        resultado = orq.executar("review", params, consulta=f"review {fname}", temp=0.1)
        
        if not resultado["sucesso"]:
            print(f'  [Review] Falhou: {resultado.get("erro", "desconhecido")}')
            continue
        
        resp = resultado["resposta"]
        
        # Parse resposta (igual ao original)
        for i, item in enumerate(itens_lote):
            item_id = item.get("id") or item.get("_linha", i)
            nome = item.get("name", item.get("nome", "?"))
            padrao_item = re.search(rf'ITEM\s*{i+1}\s*:\s*(.*)', resp, re.IGNORECASE)
            status_item = padrao_item.group(1) if padrao_item else ""
            if "ERRO" in status_item.upper():
                suspeitos.append((item_id, nome, status_item[:80]))
                print(f'  [{len(suspeitos)}] ID {item_id}: {nome} -> ERRO')
            else:
                print(f'  ID {item_id}: {nome} -> OK')
        
        print(f'  [Review] {len(suspeitos)} suspeitos em {fname}')
    
    print(f'\n[Review] Concluido. Total de suspeitos: {sum(1 for _ in open(json_path) for _ in []) if False else "(ver acima)"}')
    if suspeitos:
        print(f'[Review] Para corrigir: edite o JSON em {ext_dir} e execute:')
        print(f'  python mcr_devia.py extract aplicar --force {path_review}')
    return True
