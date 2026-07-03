"""
    local_search.py — Busca local em arquivos do projeto MCR
    Uso: python local_search.py <pattern> [caminhos...]
    
    Exemplos:
      python local_search.py "HABILIDADES" --include *.lua
      python local_search.py "platinar" --path "E:\\Projeto MCR\\Canary"
      python local_search.py "learnHabilidade" --include *.{cpp,hpp}
    
    Retorna: caminho:linha: conteúdo
    Suporta regex, glob, exclusao de diretorios.
"""
import os, re, sys, fnmatch, argparse, json

def search_file(filepath, pattern, regex_obj):
    """Busca pattern em um arquivo, retorna lista de (linha, texto)"""
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f, 1):
                if regex_obj.search(line):
                    results.append((i, line.rstrip()))
    except Exception:
        pass  # ignora arquivos que nao da pra ler
    return results

def main():
    parser = argparse.ArgumentParser(description='Busca local em arquivos')
    parser.add_argument('pattern', help='Padrao regex para buscar')
    parser.add_argument('--path', default=os.environ.get('MCR_ROOT', r'E:\Projeto MCR'),
                        help='Diretorio raiz (padrao: MCR_ROOT ou E:\\Projeto MCR)')
    parser.add_argument('--include', default='*.lua',
                        help='Glob para incluir (ex: *.lua, *.{cpp,hpp})')
    parser.add_argument('--exclude-dirs', default='node_modules,.git,.learn_db',
                        help='Diretorios para excluir (separados por virgula)')
    parser.add_argument('--json', action='store_true',
                        help='Saida em JSON')
    parser.add_argument('--max-results', type=int, default=100,
                        help='Maximo de resultados (0 = ilimitado)')
    
    args = parser.parse_args()
    
    # Compila regex
    try:
        regex = re.compile(args.pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Erro na regex: {e}")
        sys.exit(1)
    
    exclude_dirs = set(d.strip() for d in args.exclude_dirs.split(','))
    include_patterns = args.include.split(',')
    
    all_results = {}
    total = 0
    
    # Suporta path de arquivo unico ou diretorio
    if os.path.isfile(args.path):
        # Path e um arquivo especifico
        filename = os.path.basename(args.path)
        dirpath = os.path.dirname(args.path)
        
        matched = False
        for pat in include_patterns:
            pat = pat.strip()
            if fnmatch.fnmatch(filename, pat):
                matched = True
                break
        if matched:
            relpath = os.path.basename(args.path)
            results = search_file(args.path, args.pattern, regex)
            if results:
                all_results[relpath] = results
                total += len(results)
    else:
        for root, dirs, files in os.walk(args.path):
            # Exclui diretorios
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for filename in files:
                # Verifica se o arquivo corresponde ao include
                matched = False
                for pat in include_patterns:
                    pat = pat.strip()
                    if fnmatch.fnmatch(filename, pat):
                        matched = True
                        break
                if not matched:
                    continue
                
                filepath = os.path.join(root, filename)
                relpath = os.path.relpath(filepath, args.path)
                
                results = search_file(filepath, args.pattern, regex)
                if results:
                    all_results[relpath] = results
                    total += len(results)
                
                if args.max_results > 0 and total >= args.max_results:
                    # Trunca para nao ficar enorme
                    pass
    
    if args.json:
        output = {}
        for relpath, lines in all_results.items():
            output[relpath] = [{"line": l, "text": t} for l, t in lines]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # Ordena por caminho
        for relpath in sorted(all_results.keys()):
            lines = all_results[relpath]
            print(f"\n{relpath}:")
            for line_num, text in lines:
                print(f"  {line_num}: {text[:200]}")
        
        print(f"\n--- {total} resultados em {len(all_results)} arquivos ---")

if __name__ == '__main__':
    main()
