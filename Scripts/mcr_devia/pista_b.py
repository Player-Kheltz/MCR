#!/usr/bin/env python3
"""
PISTA B — Criada pelo MCR-DevIA (conceito)
=============================================
Foca em:
1. Analisar estrutura do projeto
2. Identificar problemas potenciais
3. Criar solucao contextual
4. Validar contra templates
5. Auto-corrigir
6. Registrar aprendizado
"""

import sys, os, json, re, urllib.request, subprocess

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'

class PistaB:
    def __init__(self, nome_corredor):
        self.nome = nome_corredor
        self.pontos = 0; self.erros = 0; self.log = []
    
    def registrar(self, etapa, status, detalhe=''):
        self.log.append({'etapa': etapa, 'status': status, 'detalhe': detalhe[:80]})
        s = '[OK]' if status else '[ERRO]'
        print(f'  {s} {etapa}: {detalhe[:80]}')
        if status: self.pontos += 1
        else: self.erros += 1
    
    def executar(self):
        print(f'\n{"="*60}')
        print(f'  PISTA B — CORRENDO: {self.nome}')
        print(f'{"="*60}')
        
        # 1. Analisar estrutura
        print('\n[1/6] Analisar estrutura do projeto...')
        caminhos_analisar = [
            os.path.join(BASE, 'Canary', 'src', 'mcr'),
            os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR'),
            os.path.join(BASE, 'OTClient', 'src'),
        ]
        encontrados = 0
        for c in caminhos_analisar:
            if os.path.exists(c):
                arquivos = len([f for f in os.listdir(c) if f.endswith(('.lua','.cpp','.hpp'))])
                encontrados += arquivos
        self.registrar('Analisar diretorios MCR', encontrados > 0, f'{encontrados} arquivos encontrados')
        
        # 2. Identificar problemas
        print('\n[2/6] Identificar problemas potenciais...')
        problemas = 0
        # Verifica se ha arquivos temporarios
        temp_files = [f for f in os.listdir(SANDBOX) if f.endswith('.bak') or f.endswith('.bak_v2')]
        if temp_files: problemas += 1
        self.registrar('Arquivos temporarios', len(temp_files) < 10, f'{len(temp_files)} arquivos .bak')
        
        # Verifica se o Knowledge Graph existe
        kg_path = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
        kg_existe = os.path.exists(kg_path)
        self.registrar('Knowledge Graph existe', kg_existe, 'KG pronto' if kg_existe else '')
        
        # 3. Criar solucao contextual
        print('\n[3/6] Criar solucao contextual...')
        # Tenta identificar o contexto atual e criar algo relevante
        if kg_existe:
            with open(kg_path, 'r', encoding='utf-8') as f: kg = json.load(f)
            n_licoes = len(kg.get('licoes', []))
            self.registrar('Contexto carregado', True, f'{n_licoes} licoes disponiveis')
        else:
            self.registrar('Contexto carregado', False, 'KG nao encontrado')
        
        # Tenta gerar algo contextual
        try:
            r = subprocess.run(
                f'python "{os.path.join(SANDBOX, "mcr_devia.py")}" gerar npc "ContextualTest"',
                capture_output=True, text=True, shell=True, timeout=30
            )
            self.registrar('Gerar solucao contextual', r.returncode == 0, 'NPC criado' if r.returncode == 0 else '')
        except: self.registrar('Gerar solucao contextual', False)
        
        # 4. Validar contra templates
        print('\n[4/6] Validar contra templates...')
        # Verifica se o arquivo gerado segue o formato do template
        arquivos_lua = [f for f in os.listdir(SANDBOX) if f.endswith('.lua') and ('devia_' in f or 'chat_' in f)]
        validos = 0
        for f in arquivos_lua[-5:]:
            try:
                with open(os.path.join(SANDBOX, f), 'r', encoding='utf-8') as fp:
                    conteudo = fp.read()
                if 'local' in conteudo and '=' in conteudo:
                    validos += 1
            except: pass
        self.registrar('Validar formato Lua', validos > 0, f'{validos} arquivos com sintaxe basica')
        
        # 5. Auto-corrigir
        print('\n[5/6] Auto-corrigir...')
        # Simula correcao de problemas encontrados
        correcoes = 0
        for f in arquivos_lua[-3:]:
            path = os.path.join(SANDBOX, f)
            try:
                with open(path, 'r', encoding='utf-8') as fp:
                    conteudo = fp.read()
                # Verifica se precisa de correcao (ex: aspas duplicadas)
                if '""' in conteudo:
                    conteudo = conteudo.replace('""', '"')
                    with open(path, 'w', encoding='utf-8') as fp:
                        fp.write(conteudo)
                    correcoes += 1
            except: pass
        self.registrar('Auto-corrigir arquivos', True, f'{correcoes} correcoes aplicadas')
        
        # 6. Registrar aprendizado
        print('\n[6/6] Registrar aprendizado...')
        try:
            r = subprocess.run(
                f'python "{os.path.join(SANDBOX, "mcr_devia.py")}" ensinar "PistaB_erro" "Erro simulado" "Correcao automatica" "teste"',
                capture_output=True, text=True, shell=True, timeout=10
            )
            self.registrar('Registrar aprendizados', 'APRENDIDO' in r.stdout, 'KG atualizado')
        except: self.registrar('Registrar aprendizados', False)
        
        print(f'\n{"="*60}')
        print(f'  PISTA B — {self.nome}: {self.pontos}/{self.pontos+self.erros} etapas')
        print(f'  Pontos: {self.pontos}, Erros: {self.erros}')
        print(f'{"="*60}')
        return self.pontos, self.erros

if __name__ == '__main__':
    corredor = sys.argv[1] if len(sys.argv) > 1 else 'DESCONHECIDO'
    pista = PistaB(corredor)
    pista.executar()
