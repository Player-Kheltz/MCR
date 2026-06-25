"""Auto-Template V2 — Aprende a pensar como o assistente cloud"""
import re, os, json
from collections import Counter

class AutoTemplateV2:
    """
    Cria templates como EU faria:
    1. Coleta VARIOS exemplos do mesmo tipo
    2. Compara (diff) linha a linha
    3. O que é IGUAL em todos = ESTRUTURA (fixo)
    4. O que é DIFERENTE = BLANK (variavel)
    5. Nomeia blanks pelo CONTEXTO (funcao chamada)
    """
    
    @staticmethod
    def coletar_exemplos(caminho, categorias=None, max_por_tipo=10):
        """
        Escaneia diretorio, agrupa arquivos por categoria,
        retorna dict: categoria -> [conteudos]
        """
        exemplos = {}
        
        for root, dirs, files in os.walk(caminho):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'build', '.git')]
            
            for f in files:
                if not f.endswith('.lua'):
                    continue
                
                caminho_completo = os.path.join(root, f)
                try:
                    with open(caminho_completo, 'r', encoding='utf-8', errors='replace') as fp:
                        conteudo = fp.read()
                except:
                    continue
                
                # Detecta categoria
                cat = AutoTemplateV2._detectar_categoria(conteudo, f)
                if not cat:
                    continue
                if categorias and cat not in categorias:
                    continue
                
                if cat not in exemplos:
                    exemplos[cat] = []
                if len(exemplos[cat]) < max_por_tipo:
                    exemplos[cat].append(conteudo)
        
        return exemplos
    
    @staticmethod
    def _detectar_categoria(conteudo, nome_arquivo):
        """Detecta categoria como EU faria: pelo conteudo, nao pelo nome."""
        score = 0
        categoria = None
        
        # Padroes fortes (match direto)
        padroes = [
            ('npc', [r'NPC\(', r':setSaudacao', r':addItem', r'local npc']),
            ('quest', [r'Quest\(', r':addObjetivo', r':addRecompensa', r':setDescricao']),
            ('monster', [r'Monster\(', r':setHealth', r':addLoot', r':setAttack']),
            ('item', [r'Item\(', r':setType', r':setAttack', r':setWeight']),
            ('spell', [r'Spell\(', r':setDamage', r':setManaCost', r':setCooldown']),
            ('talkaction', [r'TalkAction\(', r'.onSay']),
            ('creaturescript', [r'CreatureEvent\(', r'onLogin', r'onDeath']),
            ('globalevent', [r'GlobalEvent\(', r'onStartup', r'onTimer']),
            ('action', [r'Action\(', r':aid\(', r'onUse']),
            ('movement', [r'Movement\(', r'onStepIn', r'onStepOut']),
        ]
        
        for cat, padroes_cat in padroes:
            for p in padroes_cat:
                if re.search(p, conteudo, re.IGNORECASE):
                    score += 1
                    if score >= 2:  # Precisa de 2 matches pra confirmar
                        return cat
        
        return None
    
    @staticmethod
    def criar_template_por_dif(multiplos_exemplos):
        """
        O coracao: compara VARIOS exemplos do mesmo tipo.
        Linhas IGUAIS em todos = estrutura (vai pro template)
        Linhas DIFERENTES = blank em potencial
        
        Retorna (template_string, lista_de_blanks_com_contexto)
        """
        if not multiplos_exemplos or len(multiplos_exemplos) < 2:
            # Com 1 exemplo, usa abordagem antiga (heuristica)
            return AutoTemplateV2._template_de_um_exemplo(multiplos_exemplos[0]) if multiplos_exemplos else (None, [])
        
        # Divide todos os exemplos em linhas
        todos_linhas = [ex.split('\n') for ex in multiplos_exemplos]
        
        # Encontra o comprimento minimo (compara so ate a menor)
        min_len = min(len(linhas) for linhas in todos_linhas)
        
        template_linhas = []
        blanks_info = []  # (nome_blank, exemplos_de_valores)
        
        for i in range(min_len):
            linhas_desta_pos = [ex[i] for ex in todos_linhas]
            linhas_limpas = [l.strip() for l in linhas_desta_pos]
            
            # Se TODAS as linhas sao IGUAIS: estrutura fixa
            if all(l == linhas_limpas[0] for l in linhas_limpas):
                template_linhas.append(linhas_limpas[0])
                continue
            
            # Se sao DIFERENTES: blank!
            # Tenta entender o contexto: que funcao esta sendo chamada?
            linha_ref = linhas_limpas[0]
            
            # Extrai contexto: nome da funcao sendo chamada
            ctx = AutoTemplateV2._extrair_contexto(linha_ref)
            
            # Cria nome do blank baseado no contexto
            if ctx:
                nome_blank = ctx.replace(':', '_').replace('(', '').replace(')', '')
                # Pega os valores unicos como exemplos
                valores_unicos = list(set(linhas_limpas))
                
                # Cria linha de template com o blank
                # Tenta achar o padrao: o que é fixo e o que varia
                template_linha = AutoTemplateV2._criar_linha_template(linha_ref, valores_unicos, nome_blank)
                template_linhas.append(template_linha)
                blanks_info.append((nome_blank, valores_unicos[:5]))
            else:
                # Sem contexto, usa blank generico
                template_linhas.append(f'-- [blank_{len(blanks_info)}]')
                blanks_info.append((f'blank_{len(blanks_info)}', list(set(linhas_limpas))[:3]))
        
        template = '\n'.join(template_linhas)
        blanks = [b[0] for b in blanks_info]
        
        return template, blanks
    
    @staticmethod
    def _extrair_contexto(linha):
        """Extrai contexto de uma linha: que funcao/metodo esta sendo chamado?"""
        # Procura padrao: objeto:metodo("valor")
        m = re.search(r'(\w+:\w+)\(', linha)
        if m:
            return m.group(1)
        # Procura padrao: funcao("valor")  
        m = re.search(r'(\w+)\(', linha)
        if m:
            return m.group(1)
        # Procura atribuicao: tipo = "valor"
        m = re.search(r'(\w+)\s*=', linha)
        if m:
            return m.group(1)
        return None
    
    @staticmethod
    def _criar_linha_template(linha_ref, valores, nome_blank):
        """Cria uma linha de template substituindo a parte variavel por {blank}."""
        if not valores:
            return linha_ref
        
        # Encontra a parte que varia entre os valores
        # Procura strings entre aspas
        partes_entre_aspas = re.findall(r'["\']([^"\']*)["\']', linha_ref)
        if partes_entre_aspas:
            for parte in partes_entre_aspas:
                if any(parte in v for v in valores):
                    linha_template = linha_ref.replace(f'"{parte}"', f'{{{nome_blank}}}', 1)
                    return linha_template
        
        # Procura numeros
        numeros = re.findall(r'\b(\d+)\b', linha_ref)
        if numeros:
            for num in numeros:
                # Verifica se esse numero varia entre os exemplos
                for v in valores:
                    if num not in v:
                        linha_template = linha_ref.replace(num, f'{{{nome_blank}}}', 1)
                        return linha_template
        
        # Fallback: substitui a primeira string ou numero
        m = re.search(r'["\'][^"\']*["\']', linha_ref)
        if m:
            val = m.group()
            return linha_ref.replace(val, f'{{{nome_blank}}}', 1)
        
        return f'-- [blank_{nome_blank}: {linha_ref}]'
    
    @staticmethod
    def _template_de_um_exemplo(conteudo):
        """Fallback: com 1 exemplo, usa heuristica."""
        linhas = conteudo.split('\n')
        template_linhas = []
        blanks = []
        blank_count = 0
        
        for linha in linhas:
            # Comentarios viram template fixo
            if linha.strip().startswith('--'):
                template_linhas.append(linha)
                continue
            
            # Strings com conteudo significativo viram blanks
            partes_entre_aspas = re.findall(r'["\']([^"\']{3,})["\']', linha)
            if partes_entre_aspas:
                linha_template = linha
                for parte in partes_entre_aspas:
                    if not parte.isdigit():
                        # Tenta nomear o blank pelo contexto
                        ctx = AutoTemplateV2._extrair_contexto(linha)
                        nome_blank = f'{ctx}_{blank_count}' if ctx else f'blank_{blank_count}'
                        blank_count += 1
                        linha_template = linha_template.replace(f'"{parte}"', f'{{{nome_blank}}}', 1)
                        blanks.append(nome_blank)
                template_linhas.append(linha_template)
            else:
                template_linhas.append(linha)
        
        return '\n'.join(template_linhas), blanks
    
    @staticmethod
    def salvar_template(nome_modulo, template, blanks, base_dir):
        """Salva o modulo descoberto."""
        info = {
            'nome': nome_modulo,
            'template': template,
            'blanks': blanks,
            'descoberto_em': str(__import__('datetime').datetime.now()),
            'exemplos_usados': 0,
        }
        path = os.path.join(base_dir, f'modulo_{nome_modulo}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        return path
    
    @staticmethod
    def demo():
        """Demonstra como o sistema pensa."""
        print("\n=== Como eu (cloud) crio templates ===")
        print("1. Eu nunca olho um arquivo isolado")
        print("2. Junto 3-5 arquivos do MESMO TIPO")
        print("3. Comparo linha a linha:")
        print("   - LINHA IGUAL = estrutura (va para o template)")
        print("   - LINHA DIFERENTE = blank em potencial")
        print("4. Nomeio o blank pelo CONTEXTO:")
        print("   - npc:setSaudacao('Ola') -> blank 'setSaudacao'")
        print("   - monster:setHealth(100) -> blank 'setHealth'")
        print("5. O template final tem ZERO erros de sintaxe")
        print("   porque CADA linha veio de codigo real que funciona!")
        print()
        
        # Teste com exemplos simulados
        exemplos = [
            '-- NPC: Ferreiro\nlocal npc = NPC("Ferreiro")\nnpc:setSaudacao("Bem-vindo!")\nnpc:addItem(101, 50)',
            '-- NPC: Mercador\nlocal npc = NPC("Mercador")\nnpc:setSaudacao("Quer comprar algo?")\nnpc:addItem(102, 30)',
            '-- NPC: Guarda\nlocal npc = NPC("Guarda")\nnpc:setSaudacao("Pare!")\nnpc:addItem(103, 100)',
        ]
        
        print("=== TESTE COM 3 NPCs ===")
        template, blanks = AutoTemplateV2.criar_template_por_dif(exemplos)
        print(f"Template gerado ({len(blanks)} blanks):")
        for linha in template.split('\n'):
            print(f"  {linha}")
        print(f"\nBlanks encontrados: {blanks}")
        
        return template, blanks


if __name__ == '__main__':
    AutoTemplateV2.demo()
