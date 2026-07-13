"""Comando: extract - Extrai partes de QUALQUER arquivo, modifica, reaplica (com seguranca)."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "extract",
        "desc": "Extrai partes de QUALQUER arquivo, modifica, reaplica (com seguranca).",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Extrai partes de QUALQUER arquivo, modifica, reaplica (com seguranca).
    Uso: python mcr_devia.py extract <arquivo> [descricao]
         python mcr_devia.py extract aplicar --force <arquivo>
         python mcr_devia.py extract revisar <arquivo>
    Fluxo: extrai -> revisar (MCR + Conselho) -> diff preview -> aplicar --force
    Seguranca: revisao ANTES de aplicar. So aplica com --force."""
    import xml.etree.ElementTree as ET_xt
    import csv as csv_xt, json as json_xt, shutil as sh_xt, re as re_xt
    
    # Se for comando 'revisar' (triagem -> MCR-DevIA + Conselho revisam)
    if args[0] == 'revisar' and len(args) >= 2:
        path_revisar = args[1]
        ext_dir = os.path.join(os.path.dirname(path_revisar), '_extract')
        if not os.path.exists(ext_dir):
            print(f'[Extract] Nada para revisar. Extraia os dados primeiro.')
            return
        
        for fname in sorted(os.listdir(ext_dir)):
            if not fname.endswith('.json') or fname == '_metadata.json':
                continue
            json_path = os.path.join(ext_dir, fname)
            with open(json_path, encoding='utf-8') as f:
                dados = json_xt.load(f)
            if not isinstance(dados, list):
                continue
            
            print(f'\n[Revisao] Revisao INDIVIDUAL em {fname} ({len(dados)} itens)...')
            print(f'  Analisando cada item com contexto completo...')
            
            import urllib.request as ur_xt
            suspeitos = []
            
            for i, item in enumerate(dados):
                if i >= 20:  # Limite de 20 por execucao para nao estourar tempo
                    break
                
                # Converte o item para JSON com contexto completo
                item_json = json_xt.dumps(item, ensure_ascii=False)
                
                # IA analisa item individualmente (usa router padronizado)
                from modulos.util import gerar as _gerar_xt
                prompt = f"Item de jogo (Tibia). Analise este item COMPLETO (todos os atributos). O nome, artigo e plural estao corretos em portugues? Responda APENAS: OK ou ERRO: descricao\n\n{item_json}"
                try:
                    resp = _gerar_xt(prompt, 0.1, "fast") or ""
                except Exception as e:
                    print(f"[Fix] ERRO: {e}")
                
                item_id = item.get("id") or item.get("_linha", i)
                nome = item.get("name", "?")
                
                if "ERRO" in resp:
                    suspeitos.append((item_id, nome, resp))
                    print(f'  [{len(suspeitos)}] ID {item_id}: {nome} -> ERRO')
                else:
                    print(f'  ID {item_id}: {nome} -> OK')
            
            print(f'\n  Revisados: {min(len(dados), 20)} itens')
            print(f'  Suspeitos: {len(suspeitos)} itens')
            for sid, snome, motivo in suspeitos:
                print(f'    ID {sid}: {snome} - {motivo}')
        
        print(f'\n[Revisao] Concluida. Para aplicar: extract aplicar --force {path_revisar}')
        return
    
    # Se for comando 'aplicar'
    if args[0] == 'aplicar' and len(args) >= 2:
        path_aplicar = args[1]
        ext_dir = os.path.join(os.path.dirname(path_aplicar), '_extract')
        if not os.path.exists(ext_dir):
            print(f'[Extract] Nada para aplicar. Diretorio _extract nao encontrado.')
            return
        
        # Gera DIFF preview antes de aplicar (seguranca)
        print(f'[Extract] Gerando diff preview...')
        ext = os.path.splitext(path_aplicar)[1].lower()
        diff_path = os.path.join(ext_dir, '_diff_preview.txt')
        with open(diff_path, 'w', encoding='utf-8') as df:
            df.write(f'Extract: {path_aplicar}\n\n')
        
        for fname in sorted(os.listdir(ext_dir)):
            if not fname.endswith('.json') or fname == '_metadata.json':
                continue
            json_path = os.path.join(ext_dir, fname)
            with open(json_path, encoding='utf-8') as f:
                dados = json_xt.load(f)
            with open(diff_path, 'a', encoding='utf-8') as df:
                df.write(f'--- {fname}\n')
                for reg in (dados if isinstance(dados, list) else [dados]):
                    for k, v in reg.items():
                        if not k.startswith('_') and k != 'id':
                            df.write(f'  {reg.get("id","?")}.{k}: {v}\n')
                df.write('\n')
        
        print(f'[Extract] Diff preview: {diff_path}')
        print(f'[Extract] Revise o preview. Para aplicar, execute novamente com --force.')
        print(f'[Extract] Para rejeitar: rm -rf {ext_dir}')
        return
    
    elif args[0] == 'aplicar' and '--force' in args:
        # So aplica com --force (confirmacao explicita)
        idx_force = args.index('--force')
        path_aplicar = args[1] if idx_force > 1 else args[idx_force + 1]
        ext_dir = os.path.join(os.path.dirname(path_aplicar), '_extract')
        if not os.path.exists(ext_dir):
            print(f'[Extract] Nada para aplicar.')
            return
        
        bak = path_aplicar + '.bak'
        sh_xt.copy2(path_aplicar, bak)
        print(f'[Extract] Backup: {bak}')
        
        for fname in sorted(os.listdir(ext_dir)):
            if not fname.endswith('.json') or fname == '_metadata.json':
                continue
            json_path = os.path.join(ext_dir, fname)
            with open(json_path, encoding='utf-8') as f:
                dados = json_xt.load(f)
            
            chave_id = dados.get('_chave_id', 'id')
            tipo = dados.get('_tipo', 'xml')
            registros = dados.get('_dados', [dados]) if isinstance(dados, dict) else dados
            if isinstance(registros, dict) and '_dados' not in dados:
                registros = [dados]
            
            contagem = 0
            if tipo == 'xml':
                tree = ET_xt.parse(path_aplicar)
                for reg in registros:
                    vid = reg.get(chave_id)
                    if not vid: continue
                    for elem in tree.findall(f'.//*[@{chave_id}="{vid}"]'):
                        for k, v in reg.items():
                            if k.startswith('_'): continue
                            if elem.get(k) != v:
                                elem.set(k, v)
                                contagem += 1
                tree.write(path_aplicar, encoding='utf-8', xml_declaration=True)
            elif tipo == 'json':
                with open(path_aplicar, encoding='utf-8') as f:
                    dados_orig = json_xt.load(f)
                for reg in registros:
                    for k, v in reg.items():
                        if k.startswith('_'): continue
                        if isinstance(dados_orig, dict) and k in dados_orig:
                            if dados_orig[k] != v:
                                dados_orig[k] = v
                                contagem += 1
                with open(path_aplicar, 'w', encoding='utf-8') as f:
                    json_xt.dump(dados_orig, f, indent=2, ensure_ascii=False)
            elif tipo == 'csv' or tipo == 'lua' or tipo == 'ini' or tipo == 'regex':
                with open(path_aplicar, encoding='utf-8') as f:
                    texto_orig = f.read()
                for reg in registros:
                    vid = reg.get(chave_id)
                    if not vid and 'nome' in reg:
                        vid = reg['nome']
                    if not vid: continue
                    for k, v in reg.items():
                        if k.startswith('_') or k == chave_id: continue
                        padrao = re_xt.compile(rf'({vid}\.{k}\s*=\s*["\']?)([^"\'\s]+)(["\']?)')
                        novo, n = padrao.subn(rf'\1{v}\3', texto_orig)
                        if n > 0:
                            texto_orig = novo
                            contagem += n
                with open(path_aplicar, 'w', encoding='utf-8') as f:
                    f.write(texto_orig)
            
            print(f'[Extract] {contagem} correcoes aplicadas de {fname}')
            
            # Registra no KG: MCR-DevIA aprende com cada extracao
            if contagem > 0 and 'kg' in dir():
                try:
                    kg.aprender(
                        f'extract: {os.path.basename(path_aplicar)} ({tipo})',
                        f'{contagem} correcoes em {len(registros)} registros',
                        f'extract aplicar {os.path.basename(path_aplicar)}',
                        'extract'
                    )
                except Exception:
                    pass
        return
    
    # --- EXTRACAO ---
    path = args[0]
    desc = " ".join(args[1:]) if len(args) > 1 else "extracao"
    formato = args[1] if len(args) > 2 and args[1] in ('xml','json','csv','lua','ini','regex') else None
    ext = os.path.splitext(path)[1].lower()
    
    if not formato:
        ext_code = {'.cpp','.c','.h','.hpp','.java','.py','.js','.ts','.go','.rs','.swift','.kt'}
        mapa = {'.xml':'xml','.json':'json','.csv':'csv','.lua':'lua','.ini':'ini','.cfg':'ini','.conf':'ini'}
        mapa.update({e:'code' for e in ext_code})
        formato = mapa.get(ext, 'regex')
    
    extract_dir = os.path.join(os.path.dirname(path), '_extract')
    os.makedirs(extract_dir, exist_ok=True)
    
    dados = []
    chave_id = 'id'
    
    if formato == 'xml':
        tree = ET_xt.parse(path)
        root = tree.getroot()
        tag_principal = root[0].tag if len(root) > 0 else 'item'
        for elem in root.findall(f'.//{tag_principal}'):
            item = dict(elem.attrib)
            item['_linha'] = elem.get('id', str(len(dados)+1))
            dados.append(item)
        print(f'[Extract] XML: {tag_principal}, {len(dados)} itens')
    
    elif formato == 'json':
        with open(path, encoding='utf-8') as f:
            data = json_xt.load(f)
        if isinstance(data, list):
            dados = data
        elif isinstance(data, dict):
            chave_ident = [k for k in data.keys() if k != '_metadata']
            if chave_ident:
                dados = [{chave_ident[0]: v} for v in data.values()]
            else:
                dados = [data]
        print(f'[Extract] JSON: {len(dados)} entradas')
    
    elif formato == 'csv':
        with open(path, encoding='utf-8', newline='') as f:
            reader = csv_xt.DictReader(f)
            for row in reader:
                dados.append(row)
        print(f'[Extract] CSV: {len(dados)} linhas')
    
    elif formato == 'lua':
        with open(path, encoding='utf-8') as f:
            texto = f.read()
        for m in re_xt.finditer(r'(\w+)\s*=\s*\{([^}]+)\}', texto):
            bloco = m.group(2)
            item = {'_nome': m.group(1)}
            for kv in re_xt.finditer(r'(\w+)\s*=\s*["\']?([^"\'}\s,]+)', bloco):
                item[kv.group(1)] = kv.group(2)
            dados.append(item)
        print(f'[Extract] Lua: {len(dados)} tabelas')
    
    elif formato == 'code':
        # Extrator universal de codigo (qualquer linguagem)
        with open(path, encoding='utf-8') as f:
            codigo = f.read()
        
        # Detecta linguagem pela extensao
        lang = ext.lstrip('.')
        
        # Extrai funcoes: padrao universal (nome(parametros) {
        for m in re_xt.finditer(r'(?:(?:\w+(?:\s+(?:\*|&)?)?\s+)?(\w+)\s*\([^)]*\))\s*(?:\{|:\s*\n)', codigo):
            nome = m.group(1)
            inicio = codigo[:m.start()].count('\n') + 1
            if nome and len(nome) > 1 and nome not in ('if','for','while','switch','catch','else'):
                item = {'_linha': inicio, 'nome': nome, 'tipo': 'funcao', 'linguagem': lang}
                # Extrai as primeiras 3 linhas do corpo
                corpo_linhas = codigo[m.end():].split('\n')
                item['corpo'] = ' '.join(l.strip() for l in corpo_linhas if l.strip())
                dados.append(item)
        
        # Extrai classes
        for m in re_xt.finditer(r'(?:class|struct)\s+(\w+)(?:\s*:\s*public\s+(\w+))?', codigo):
            nome = m.group(1)
            inicio = codigo[:m.start()].count('\n') + 1
            if nome and len(nome) > 1:
                item = {'_linha': inicio, 'nome': nome, 'tipo': 'classe', 'linguagem': lang}
                if m.group(2):
                    item['herda'] = m.group(2)
                dados.append(item)
        
        print(f'[Extract] Code ({lang}): {len(dados)} funcoes/classes')
    
    elif formato in ('ini', 'regex'):
        with open(path, encoding='utf-8') as f:
            texto = f.read()
        secoes = re_xt.findall(r'\[(\w+)\](.+?)(?=\[|\Z)', texto, re_xt.DOTALL)
        for sec, conteudo in secoes:
            item = {'_sec': sec}
            for kv in re_xt.finditer(r'(\w+)\s*=\s*(.+)', conteudo):
                item[kv.group(1)] = kv.group(2).strip()
            dados.append(item)
        print(f'[Extract] INI/Regex: {len(dados)} secoes')
    
    if not dados:
        print('[Extract] Nenhum dado extraido.')
        return
    
    # Salva dados extraidos
    nome_base = desc.replace(' ','_')
    ext_path = os.path.join(extract_dir, f'{nome_base}.json')
    with open(os.path.join(extract_dir, '_metadata.json'), 'w', encoding='utf-8') as f:
        json_xt.dump({'_tipo': formato, '_chave_id': chave_id, '_arquivo': path}, f)
    with open(ext_path, 'w', encoding='utf-8') as f:
        json_xt.dump(dados, f, indent=2, ensure_ascii=False)
    
    print(f'[Extract] Dados salvos em {ext_path}')
    print(f'[Extract] Para modificar: edite o JSON, depois execute:')
    print(f'  python mcr_devia.py extract aplicar {path}')
    print(f'[Extract] Para MCR-DevIA corrigir: python mcr_devia.py perguntar "... instrucao ..."')
    return True
