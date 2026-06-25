"""Add Portuguese/English detector + fix anglicisms"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add Portuguese detector to validar_nome method
old_func = """    def validar_nome(self, nome, cfg):
        n = nome.lower().strip()
        if len(n) < 3: return False, "Muito curto"
        if len(n.split()) < 2: return False, "Precisa de 2+ palavras"
        for p in cfg.get('palavras_proibidas', []):
            if p in n: return False, f"Proibida: '{p}'"
        # Fingerprint check
        for ex in self.fp.data.get('exemplos_ruins', []):
            ex_palavras = set(ex.lower().split())
            nome_palavras = set(n.split())
            if len(ex_palavras & nome_palavras) >= 2:
                return False, f"Similar ao exemplo ruim '{ex}'"
        return True, "OK\""""

new_func = """    def validar_nome(self, nome, cfg):
        n = nome.lower().strip()
        if len(n) < 3: return False, "Muito curto"
        if len(n.split()) < 2: return False, "Precisa de 2+ palavras"
        # Verifica se tem palavras em portugues de verdade
        palavras_pt = ['de', 'da', 'do', 'das', 'dos', 'com', 'sem', 'para', 'por', 'em', 'no', 'na', 'um', 'uma', 'o', 'a', 'os', 'as']
        palavras_nome = n.split()
        # Se TODAS as palavras sao ingles (terminam em ing, er, ou sao ingles conhecidas)
        sufixos_ingles = ['ing', 'er', 'ly', 'ed', 'tion', 'sion', 'ment', 'ness']
        palavras_ingles_conhecidas = ['the', 'and', 'of', 'to', 'in', 'is', 'it', 'you', 'that', 'was',
                                      'for', 'are', 'with', 'his', 'they', 'this', 'has', 'but', 'not',
                                      'raging', 'iron', 'thunder', 'bear', 'sonic', 'mighty', 'blazing',
                                      'unyielding', 'titanic', 'cruel', 'fist', 'blade', 'saber', 'strike',
                                      'slash', 'master', 'hunter', 'knight', 'lord', 'king', 'queen']
        
        # Se alguma palavra for ingles conhecida ou tiver sufixo ingles, rejeita
        for p in palavras_nome:
            if p in palavras_ingles_conhecidas:
                return False, f"'{p}' parece ingles, use portugues"
            for suf in sufixos_ingles:
                if p.endswith(suf) and len(p) > 4:
                    return False, f"'{p}' termina em '{suf}' (parece ingles)"
        
        # Bonus: pelo menos uma palavra deve ser portuguesa
        for p in palavras_nome:
            if p in palavras_pt:
                break
        else:
            # Verifica se alguma palavra parece portuguesa (termina em vogal + 'o', 'a', 'e')
            pass  # Muito generico, pode dar falso positivo
        
        for p in cfg.get('palavras_proibidas', []):
            if p in n: return False, f"Proibida: '{p}'"
        # Fingerprint check
        for ex in self.fp.data.get('exemplos_ruins', []):
            ex_palavras = set(ex.lower().split())
            nome_palavras = set(n.split())
            if len(ex_palavras & nome_palavras) >= 2:
                return False, f"Similar ao exemplo ruim '{ex}'"
        return True, "OK\""""

c = c.replace(old_func, new_func)

with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'mcr_crew.py', 'exec')
    print('OK! Portuguese detector added')
except SyntaxError as e:
    print(f'Error: {e}')
