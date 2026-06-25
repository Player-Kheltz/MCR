"""Reinforce Portuguese in prompt and add better fallback"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the gerar_nomes method and replace its content
old_start = "    def gerar_nomes(self, cfg, quantidade):"
old_end = "        return []"

# Find the exact boundaries
idx_start = c.find(old_start)
idx_func_end = c.find('\n    def executar(self', idx_start)
if idx_func_end == -1:
    idx_func_end = c.find('\n    def validar_nome', idx_start)

old_func_body = c[idx_start:idx_func_end]

new_func = '''    def gerar_nomes(self, cfg, quantidade):
        """Gera nomes com detector de ingles e fallback tematico."""
        fp_ctx = self.fp.get_contexto()
        pool = ', '.join(cfg.get('pool_tematico', []))
        proib = ', '.join(cfg.get('palavras_proibidas', []))
        
        prompt_base = (
            f"Crie {quantidade*2} nomes em PORTUGUES para {cfg['nome']}.\\n"
            f"Contexto: {cfg['descricao']}\\n"
            f"Palavras disponiveis: {pool}\\n"
            f"PROIBIDO: {proib}\\n"
            f"IMPORTANTE: Nomes DEVEM ser em PORTUGUES BRASILEIRO.\\n"
            f"EXEMPLO BOM: 'Soco Certeiro', 'Esquiva Felina', 'Gancho Poderoso'\\n"
            f"EXEMPLO RUIM: 'Iron Fist', 'Raging Tiger', 'Thunder Punch' (INGLES!)\\n"
            f"{fp_ctx}\\n"
            f"\\nResponda JSON: [{{\\"nome\\":\\"...\\"}},...]"
        )
        
        for t in range(5):
            if t > 0:
                # Reforca a cada tentativa
                prompt = prompt_base + f"\\n\\nTentativa {t+1}: VOCE DEVE gerar em PORTUGUES BRASILEIRO. Rejeitamos nomes em ingles."
            else:
                prompt = prompt_base
            
            r = self.ia.gerar(prompt, 0.9)
            dados = self.ia.extrair_json(r) if r else None
            if isinstance(dados, list): 
                # Filtra ingles aqui mesmo
                pt_words = ['de', 'da', 'do', 'das', 'dos', 'com', 'sem', 'para', 'em', 'no', 'na', 'um', 'uma']
                en_suffixes = ['ing', 'er', 'ly', 'ed', 'tion', 'ment']
                en_words = ['the', 'and', 'of', 'raging', 'iron', 'thunder', 'mighty', 'blazing', 'cruel', 'fist', 'blade', 'strike', 'master', 'slash', 'king', 'queen', 'lord', 'knight', 'bear', 'sonic', 'titanic']
                
                filtered = []
                for item in dados:
                    nome = item.get('nome', '') if isinstance(item, dict) else ''
                    if not nome: continue
                    n = nome.lower()
                    palavras = n.split()
                    is_english = False
                    for p in palavras:
                        if p in en_words: is_english = True; break
                        for suf in en_suffixes:
                            if p.endswith(suf) and len(p) > 4: is_english = True; break
                        if is_english: break
                    if not is_english:
                        filtered.append(item)
                
                if filtered:
                    print(f'    (filtrados {len(dados) - len(filtered)} nomes em ingles)')
                    return filtered
                else:
                    prompt = prompt_base + f"\\n\\nTODOS os nomes estavam em ingles. Use palavras do pool: {pool}"
            elif isinstance(dados, dict):
                for v in dados.values():
                    if isinstance(v, list): 
                        filtered = [x for x in v if isinstance(x, dict) and x.get('nome')]
                        if filtered: return filtered
        
        # Fallback: gera nomes do pool
        print(f'    (usando fallback do pool tematico)')
        pool_list = cfg.get('pool_tematico', ['Golpe', 'Ataque'])
        result = []
        prefixos = ['Soco', 'Chute', 'Golpe', 'Esquiva', 'Combo']
        for i in range(quantidade * 2):
            p = prefixos[i % len(prefixos)]
            s = random.choice(pool_list)
            nome = f'{p} {s.title()}'
            if nome not in [x.get('nome','') for x in result]:
                result.append({'nome': nome})
        return result'''

c = c.replace(old_func_body, new_func)

with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'mcr_crew.py', 'exec')
    print('OK! Generator rewritten with English filter + fallback')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
    lines = c.split('\n')
    if e.lineno:
        for i in range(max(0,e.lineno-3), min(len(lines),e.lineno+2)):
            print(f'  {i+1}: {lines[i][:100]}')
