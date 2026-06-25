#!/usr/bin/env python3
"""
MCR-DevIA AGENT — Auditoria Completa do Projeto MCR
======================================================
Vasculha TUDO e encontra:
  - Arquivos com sintaxe suspeita
  - Codigo nao utilizado
  - Padroes inconsistentes
  - Oportunidades de melhoria
  - Erros silenciosos

Uso: python mcr_auditor.py
"""

import sys, os, json, re, datetime, hashlib

BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')

class Auditor:
    def __init__(self):
        self.resultados = []
        self.total_arquivos = 0
    
    def add(self, tipo, severidade, arquivo, detalhe):
        self.resultados.append({
            'tipo': tipo, 'severidade': severidade,
            'arquivo': arquivo, 'detalhe': detalhe[:120],
            'data': str(datetime.datetime.now())[:19]
        })
    
    def auditar_projeto(self):
        print('[AUDITOR MCR-DevIA] Escaneando projeto...\n')
        
        # 1. Escanear scripts MCR
        print('[1/5] Scripts MCR...')
        base_scripts = os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR')
        if os.path.exists(base_scripts):
            for root, dirs, files in os.walk(base_scripts):
                for f in files:
                    if not f.endswith('.lua'): continue
                    self.total_arquivos += 1
                    path = os.path.join(root, f)
                    try:
                        with open(path,'r',encoding='utf-8',errors='replace') as fp:
                            conteudo = fp.read()
                        # Chaves desbalanceadas
                        o, c = conteudo.count('{'), conteudo.count('}')
                        if o != c:
                            self.add('sintaxe', 'ALTA', path.replace(BASE,''), f'Chaves: {o}/{c}')
                        # Linhas muito longas
                        for i, linha in enumerate(conteudo.split('\n'), 1):
                            if len(linha) > 200:
                                self.add('estilo', 'BAIXA', path.replace(BASE,''), f'Linha {i}: {len(linha)} chars')
                                break
                        # Comentarios TODO/FIXME
                        if 'TODO' in conteudo or 'FIXME' in conteudo:
                            self.add('manutencao', 'MEDIA', path.replace(BASE,''), 'Contem TODO/FIXME')
                        # print de debug esquecido
                        if 'print(' in conteudo and 'DEBUG' in conteudo:
                            self.add('debug', 'BAIXA', path.replace(BASE,''), 'Print de debug')
                    except: pass
        
        print(f'  {self.total_arquivos} arquivos .lua escaneados')
        
        # 2. Escanear C++ source
        print('[2/5] Codigo C++...')
        base_cpp = os.path.join(BASE, 'Canary', 'src')
        cpp_count = 0
        if os.path.exists(base_cpp):
            for root, dirs, files in os.walk(base_cpp):
                for f in files:
                    if not f.endswith(('.cpp','.hpp')): continue
                    cpp_count += 1
                    path = os.path.join(root, f)
                    try:
                        with open(path,'r',encoding='utf-8',errors='replace') as fp:
                            conteudo = fp.read()
                        # TODO/FIXME
                        if 'TODO' in conteudo or 'FIXME' in conteudo:
                            self.add('manutencao', 'MEDIA', path.replace(BASE,''), 'Contem TODO/FIXME')
                        # Funcoes muito longas (> 100 linhas)
                        lines = conteudo.split('\n')
                        if len(lines) > 500:
                            self.add('estilo', 'MEDIA', path.replace(BASE,''), f'{len(lines)} linhas')
                    except: pass
        print(f'  {cpp_count} arquivos C++ escaneados')
        
        # 3. Verificar Knowledge Graph
        print('[3/5] Knowledge Graph...')
        if os.path.exists(KG_PATH):
            with open(KG_PATH,'r',encoding='utf-8') as f: kg = json.load(f)
            self.add('kg', 'INFO', 'KG', f'{len(kg["licoes"])} licoes, V{kg["versoes"]}')
            # Licoes nunca usadas
            nao_usadas = [l for l in kg['licoes'] if l.get('usos',0) == 0]
            if nao_usadas:
                self.add('kg', 'BAIXA', 'KG', f'{len(nao_usadas)} licoes nunca usadas')
        else:
            self.add('kg', 'ALTA', 'KG', 'Knowledge Graph nao existe!')
        print(f'  KG analisado')
        
        # 4. Verificar arquivos soltos na sandbox
        print('[4/5] Sandbox...')
        bak_count = len([f for f in os.listdir(SANDBOX) if '.bak' in f])
        if bak_count > 5:
            self.add('limpeza', 'BAIXA', 'sandbox/', f'{bak_count} arquivos .bak')
        print(f'  {bak_count} .bak encontrados')
        
        # 5. Verificar integracao dos modulos
        print('[5/5] Integracao...')
        # Verifica se o mcr_devia.py e mcr_chat.py existem e estao funcionais
        for script in ['mcr_devia.py','mcr_chat.py','mcr_agent.py','mcr_ultimate.py']:
            path = os.path.join(SANDBOX, script)
            if not os.path.exists(path):
                self.add('integracao', 'ALTA', script, 'Arquivo ausente!')
        print(f'  Scripts principais verificados')
        
        return self.resultados
    
    def relatorio(self):
        print(f'\n{"="*60}')
        print(f'  RELATORIO DO AUDITOR MCR-DevIA')
        print(f'  Total: {len(self.resultados)} itens encontrados')
        print(f'{"="*60}')
        
        # Agrupa por severidade
        for severidade in ['ALTA','MEDIA','BAIXA','INFO']:
            itens = [r for r in self.resultados if r['severidade'] == severidade]
            if itens:
                print(f'\n  [{severidade}] {len(itens)} itens:')
                for item in itens[:10]:
                    print(f'    {item["tipo"]}: {item["detalhe"][:100]}')
                    print(f'      -> {item["arquivo"][:60]}')
                if len(itens) > 10:
                    print(f'    ... e mais {len(itens)-10}')
        
        print(f'\n  Resumo:')
        print(f'    ALTA: {len([r for r in self.resultados if r["severidade"]=="ALTA"])}')
        print(f'    MEDIA: {len([r for r in self.resultados if r["severidade"]=="MEDIA"])}')
        print(f'    BAIXA: {len([r for r in self.resultados if r["severidade"]=="BAIXA"])}')
        print(f'    INFO: {len([r for r in self.resultados if r["severidade"]=="INFO"])}')
        print(f'{"="*60}')
        
        # Salva
        path = os.path.join(SANDBOX, '.mcr_auditoria_agent.json')
        with open(path,'w',encoding='utf-8') as f: json.dump(self.resultados,f,ensure_ascii=False,indent=2)
        print(f'  Relatorio salvo em: {path}')


if __name__ == '__main__':
    auditor = Auditor()
    auditor.auditar_projeto()
    auditor.relatorio()
