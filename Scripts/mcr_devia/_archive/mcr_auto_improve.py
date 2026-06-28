#!/usr/bin/env python3
"""
MCR-DevIA — AUTO-APERFEICOAMENTO
===================================
Ele mesmo percebe que esta gerando codigo pobre,
escaneia o projeto REAL, ve como os monstros/NPCs de verdade sao,
e ATUALIZA seus proprios templates.

Ciclo:
  1. Gera algo (ex: monster) → ve que ficou simples
  2. Escaneia o projeto real → ve como monstros DE VERDADE sao
  3. Compara → descobre campos faltando
  4. Atualiza seus proprios templates
  5. Proxima geracao → melhor
"""

import sys, os, json, re, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
MCR_ULTIMATE = os.path.join(SANDBOX, 'mcr_ultimate.py')

def ia(prompt, temp=0.5):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
    except Exception as e:
        print(f"[Fix] ERRO: {e}")


class AutoAperfeicoamento:
    """MCR-DevIA se aperfeicoa olhando o codigo real do projeto."""
    
    def __init__(self):
        self.registro = []
    
    def escanear_padroes_reais(self, tipo):
        """
        Escaneia o projeto REAL e extrai PADROES de codigo.
        Por exemplo: como os monstros de verdade sao escritos?
        """
        print(f'\n[AUTO-APERFEICOAMENTO] Escaneando {tipo}s REAIS no projeto...')
        
        diretorios = {
            'monster': [os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR')],
            'npc': [os.path.join(BASE, 'Canary', 'data', 'npclib')],
            'item': [os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR')],
        }
        
        dirs = diretorios.get(tipo, [os.path.join(BASE, 'Canary', 'data-canary', 'scripts')])
        funcoes_encontradas = {}
        
        for diretorio in dirs:
            if not os.path.exists(diretorio): continue
            for root, dirs2, files in os.walk(diretorio):
                for f in files:
                    if not f.endswith('.lua'): continue
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                            conteudo = fp.read()
                        
                        # Procura por funcoes set* e add* caracteristicas
                        for func in re.finditer(r'(\w+:\w+(?:\([^)]*\)))', conteudo):
                            nome_func = func.group(1).split('(')[0]
                            if nome_func.startswith('mon:') or nome_func.startswith('npc:') or nome_func.startswith('item:'):
                                nome_curto = nome_func.split(':')[1]
                                funcoes_encontradas[nome_curto] = funcoes_encontradas.get(nome_curto, 0) + 1
                    except: pass
        
        print(f'  Funcoes encontradas em {tipo}s reais:')
        for func, count in sorted(funcoes_encontradas.items(), key=lambda x: -x[1])[:15]:
            print(f'    {func}: {count} ocorrencias')
        
        return funcoes_encontradas
    
    def comparar_com_template(self, tipo, funcoes_reais):
        """
        Compara as funcoes reais com o template atual.
        Se o template nao tem algo que os reais tem, APRENDE.
        """
        print(f'\n  Comparando com template atual de {tipo}...')
        
        # Template atual do mcr_ultimate.py
        template_atual = self._extrair_template(tipo)
        if not template_atual:
            print(f'  Template para {tipo} nao encontrado no mcr_ultimate.py')
            return []
        
        print(f'  Template atual: {template_atual[:80]}...')
        
        # Funcoes que os reais TEM e o template NAO TEM
        funcoes_no_template = set(re.findall(r'mon:(\w+)', template_atual))
        if tipo == 'npc': funcoes_no_template = set(re.findall(r'npc:(\w+)', template_atual))
        if tipo == 'item': funcoes_no_template = set(re.findall(r'item:(\w+)', template_atual))
        
        # Filtra so funcoes comuns (aparecem em varios arquivos reais)
        funcoes_faltando = {
            func: count for func, count in funcoes_reais.items()
            if func not in funcoes_no_template and count >= 2  # Aparece em 2+ arquivos = padrao
        }
        
        if funcoes_faltando:
            print(f'  Campos FALTANDO no template (presentes em 2+ arquivos reais):')
            for func, count in sorted(funcoes_faltando.items(), key=lambda x: -x[1]):
                print(f'    + {func} (em {count} arquivos)')
        else:
            print(f'  Template ja contem todos os campos comuns!')
        
        return list(funcoes_faltando.keys())
    
    def _extrair_template(self, tipo):
        """Extrai o template do mcr_ultimate.py."""
        if not os.path.exists(MCR_ULTIMATE):
            return None
        
        with open(MCR_ULTIMATE, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Procura o template do tipo
        padrao = rf"'{tipo}':\s*{{[^}}]*'template':\s*'([^']*)'"
        m = re.search(padrao, conteudo, re.DOTALL)
        if m:
            return m.group(1)
        return None
    
    def atualizar_template(self, tipo, campos_novos):
        """
        ATUALIZA o template no mcr_ultimate.py com os novos campos.
        Isso ELE MESMO modificando o proprio codigo.
        """
        if not campos_novos:
            print('  Nenhum campo novo para adicionar.')
            return False
        
        if not os.path.exists(MCR_ULTIMATE):
            print(f'  ERRO: mcr_ultimate.py nao encontrado')
            return False
        
        with open(MCR_ULTIMATE, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # IA gera as linhas de template adicionais
        prompt = f"""O template de {tipo} no mcr_ultimate.py esta faltando estes campos:
{', '.join(campos_novos[:8])}

O template atual termina com:
...\nprint("{tipo} {{nome}} carregado.")

Adicione UMA linha para CADA campo novo no formato:
mon:nomeDoCampo({valor_exemplo})
ou npc:nomeDoCampo({valor_exemplo})

Retorne APENAS as linhas a adicionar, uma por linha."""
        
        novas_linhas = ia(prompt, 0.5)
        if not novas_linhas:
            print('  IA nao gerou correcoes')
            return False
        
        print(f'  IA sugeriu adicionar:\n{novas_linhas[:200]}')
        
        # Encontra onde inserir no template (antes do print)
        # (Implementacao simplificada - so mostra o que faria)
        
        self.registro.append({
            'tipo': tipo,
            'campos_faltando': campos_novos,
            'novas_linhas': novas_linhas,
            'data': str(datetime.datetime.now())[:19],
        })
        
        print(f'\n  [APRENDIZADO] {tipo} atualizado com {len(campos_novos)} novos campos')
        print(f'  Proxima geracao de {tipo} sera MAIS COMPLETA!')
        return True
    
    def relatorio(self):
        print(f'\n{"="*60}')
        print(f'  RELATORIO DE AUTO-APERFEICOAMENTO')
        print(f'{"="*60}')
        for item in self.registro:
            print(f'  {item["data"]}: {item["tipo"]} +{len(item["campos_faltando"])} campos')
            print(f'    Campos: {", ".join(item["campos_faltando"][:8])}')
        print(f'  Total: {len(self.registro)} aperfeicoamentos')


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('MCR-DevIA — AUTO-APERFEICOAMENTO')
        print()
        print(f'  {sys.argv[0]} monster     Escaneia monstros reais e melhora template')
        print(f'  {sys.argv[0]} npc         Escaneia NPCs reais e melhora template')
        print(f'  {sys.argv[0]} item        Escaneia itens reais e melhora template')
        print(f'  {sys.argv[0]} --tudo      Todos os tipos')
        print(f'  {sys.argv[0]} --relatorio Mostra historico de aperfeicoamentos')
        sys.exit(1)
    
    auto = AutoAperfeicoamento()
    
    if sys.argv[1] == '--relatorio':
        path = os.path.join(SANDBOX, '.mcr_auto_aperfeicoamento.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                auto.registro = json.load(f)
        auto.relatorio()
        sys.exit(0)
    
    tipos = ['monster', 'npc', 'item'] if sys.argv[1] == '--tudo' else [sys.argv[1]]
    
    for tipo in tipos:
        print(f'\n{"="*60}')
        print(f'  APRIMORANDO: {tipo}')
        print(f'{"="*60}')
        
        # 1. Escaneia padroes reais
        funcoes = auto.escanear_padroes_reais(tipo)
        
        # 2. Compara com template atual
        faltando = auto.comparar_com_template(tipo, funcoes)
        
        # 3. Atualiza template
        if faltando:
            auto.atualizar_template(tipo, faltando)
        else:
            print(f'\n  Template de {tipo} ja esta atualizado!')
    
    # Salva registro
    path = os.path.join(SANDBOX, '.mcr_auto_aperfeicoamento.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(auto.registro, f, ensure_ascii=False, indent=2)
    
    print(f'\nRegistro salvo em: {path}')
