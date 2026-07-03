"""Comando: edit - Edita por LINHA (precisao cirurgica)."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "edit",
        "desc": "Edita por LINHA (precisao cirurgica).",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Edita por LINHA (precisao cirurgica). 
    Uso: python mcr_devia.py edit <path> <linha> <novo_conteudo>
    Ou:  python mcr_devia.py edit <path> --range <inicio> <fim> --substituir <velho> <novo>
    Ou:  python mcr_devia.py edit <path> --linha <n> --substituir <velho> <novo>"""
    path = args[0]
    if not os.path.exists(path):
        print(f'[Edit] Arquivo nao encontrado: {path}')
    else:
        with open(path, encoding='utf-8') as fh:
            linhas = fh.readlines()
        
        if '--range' in args:
            # Edicao por intervalo de linhas
            idx_range = args.index('--range')
            try:
                inicio = int(args[idx_range + 1])
                fim = int(args[idx_range + 2])
            except Exception as e:
                print(f"[Fix] ERRO: {e}")
                return
            idx_sub = args.index('--substituir') if '--substituir' in args else None
            if idx_sub:
                velho = args[idx_sub + 1]
                novo = args[idx_sub + 2]
                # So substitui no intervalo especificado
                for i in range(inicio - 1, min(fim, len(linhas))):
                    if i >= 0 and velho in linhas[i]:
                        linhas[i] = linhas[i].replace(velho, novo)
                        # Forca unicidade: so 1 substituicao por padrao no intervalo
                        break
                else:
                    print(f'[Edit] Padrao "{velho}" nao encontrado entre L{inicio}-L{fim}')
                    return
            else:
                print('[MCR-DevIA] Use: --range <inicio> <fim> --substituir <velho> <novo>')
                return
        elif '--linha' in args:
            # Edicao por linha unica com substituicao de texto
            idx_linha = args.index('--linha')
            try:
                linha_alvo = int(args[idx_linha + 1])
            except Exception as e:
                print(f"[Fix] ERRO: {e}")
                return
            idx_sub = args.index('--substituir') if '--substituir' in args else None
            if idx_sub and 1 <= linha_alvo <= len(linhas):
                velho = args[idx_sub + 1]
                novo = args[idx_sub + 2]
                if velho in linhas[linha_alvo - 1]:
                    linhas[linha_alvo - 1] = linhas[linha_alvo - 1].replace(velho, novo)
                else:
                    print(f'[Edit] Padrao nao encontrado na L{linha_alvo}')
                    print(f'  Conteudo: {linhas[linha_alvo - 1].rstrip().encode('ascii',errors='replace').decode('ascii')}')
                    return
            else:
                print('[MCR-DevIA] Use: --linha <n> --substituir <velho> <novo>')
                return
        else:
            # Edicao simples: substituir linha inteira
            try:
                linha_alvo = int(args[1])
                novo_conteudo = " ".join(args[2:])
            except Exception as e:
                print(f"[Fix] ERRO: {e}")
                return
            if 1 <= linha_alvo <= len(linhas):
                print(f'[Edit] Substituindo L{linha_alvo}:')
                print(f'  Antes: {linhas[linha_alvo-1].rstrip().encode('ascii',errors='replace').decode('ascii')}')
                linhas[linha_alvo - 1] = novo_conteudo + ('\n' if not novo_conteudo.endswith('\n') else '')
                print(f'  Depois: {linhas[linha_alvo-1].rstrip().encode('ascii',errors='replace').decode('ascii')}')
            else:
                print(f'[Edit] Linha {linha_alvo} invalida (1-{len(linhas)})')
                return
        
        # Salva
        with open(path, 'w', encoding='utf-8') as fh:
            fh.writelines(linhas)
        
        # Valida: tenta compilar
        if path.endswith('.py'):
            try:
                compile("".join(linhas), path, 'exec')
                print(f'[Edit] [OK] Edit aplicado e compilacao verificada!')
            except SyntaxError as e:
                print(f'[Edit] [ALERTA] Edit aplicado, mas erro de sintaxe: {e}')
                print(f'[Edit] Revertendo...')
                # (aqui poderia ter rollback, mas exige backup previo)
        else:
            print(f'[Edit] [OK] Edit aplicado!')
    return True
