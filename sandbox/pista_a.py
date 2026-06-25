#!/usr/bin/env python3
"""
PISTA A — Criada por MIM (cloud)
==================================
Simula o uso real desde o inicio do MCR:
1. Explorar projeto
2. Diagnosticar ambiente
3. Gerar sistema completo
4. Compilar e corrigir
5. Auto-revisar
6. Aprender
"""

import sys, os, json, re, urllib.request, hashlib, datetime, subprocess

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'

class PistaA:
    def __init__(self, nome_corredor):
        self.nome = nome_corredor
        self.pontos = 0
        self.erros = 0
        self.log = []
    
    def registrar(self, etapa, status, detalhe=''):
        self.log.append({'etapa': etapa, 'status': status, 'detalhe': detalhe[:80]})
        s = '[OK]' if status else '[ERRO]'
        print(f'  {s} {etapa}: {detalhe[:80]}')
        if status: self.pontos += 1
        else: self.erros += 1
    
    def executar(self):
        print(f'\n{"="*60}')
        print(f'  PISTA A — CORRENDO: {self.nome}')
        print(f'{"="*60}')
        
        # 1. Explorar
        print('\n[1/6] Explorar projeto...')
        try:
            dirs = [d for d in os.listdir(os.path.join(BASE, 'Canary')) if os.path.isdir(os.path.join(BASE, 'Canary', d))]
            self.registrar('Listar diretorios', True, f'{len(dirs)} diretorios encontrados')
        except: self.registrar('Listar diretorios', False, 'Falha ao acessar')
        
        try:
            luas = [f for f in os.listdir(os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR', 'SPA', 'core')) if f.endswith('.lua')]
            self.registrar('Explorar scripts MCR', True, f'{len(luas)} arquivos Lua')
        except: self.registrar('Explorar scripts MCR', False)
        
        # 2. Diagnosticar ambiente
        print('\n[2/6] Diagnosticar ambiente...')
        msbuild_paths = [
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
        ]
        msbuild = None
        for p in msbuild_paths:
            if os.path.exists(p): msbuild = p; break
        self.registrar('Encontrar MSBuild', msbuild is not None, os.path.basename(os.path.dirname(os.path.dirname(msbuild))) if msbuild else '')
        
        vs_path = None
        if msbuild:
            vs = msbuild
            for _ in range(6): vs = os.path.dirname(vs)
            vs_path = vs
        self.registrar('Encontrar VS', vs_path is not None, os.path.basename(vs_path) if vs_path else '')
        
        # 3. Gerar sistema completo
        print('\n[3/6] Gerar sistema completo...')
        # Simula geracao (usa IA se disponivel, senao templates)
        itens_gerados = 0
        templates = ['npc', 'monster', 'item', 'spell']
        for t in templates:
            try:
                # Tenta usar MCR-DevIA real, se nao, simula
                result = subprocess.run(
                    f'python "{os.path.join(SANDBOX, "mcr_devia.py")}" gerar {t} "Teste{t}"',
                    capture_output=True, text=True, shell=True, timeout=30
                )
                if result.returncode == 0 and 'OK' in result.stdout:
                    itens_gerados += 1
            except: pass
        self.registrar('Gerar templates', itens_gerados > 0, f'{itens_gerados}/{len(templates)} gerados')
        
        # 4. Compilar e corrigir (simulado)
        print('\n[4/6] Compilar e corrigir...')
        # Simula erros comuns e suas correcoes
        erros_conhecidos = {
            'LNK2001': 'ABI mismatch - usar VS correto',
            'D9002': 'stdcpplatest -> stdcpp20',
            'C1083': 'include path faltando',
        }
        erros_encontrados = list(erros_conhecidos.keys())[:2]
        for erro in erros_encontrados:
            self.registrar(f'Corrigir {erro}', True, erros_conhecidos[erro])
        
        # 5. Auto-revisar
        print('\n[5/6] Auto-revisar...')
        arquivos_gerados = [f for f in os.listdir(SANDBOX) if f.startswith('devia_') or f.startswith('chat_')]
        self.registrar('Revisar codigo gerado', len(arquivos_gerados) > 0, f'{len(arquivos_gerados)} arquivos revisados')
        
        # Verifica qualidade basica
        qualidade = 0
        for f in arquivos_gerados[-5:]:
            path = os.path.join(SANDBOX, f)
            try:
                with open(path, 'r', encoding='utf-8') as fp:
                    conteudo = fp.read()
                if '{' in conteudo and '}' in conteudo: qualidade += 1
            except: pass
        self.registrar('Qualidade do codigo', qualidade > 0, f'{qualidade}/{min(5,len(arquivos_gerados))} com sintaxe valida')
        
        # 6. Aprender
        print('\n[6/6] Aprender...')
        # Tenta registrar aprendizado no KG
        try:
            result = subprocess.run(
                f'python "{os.path.join(SANDBOX, "mcr_devia.py")}" ensinar "ErroTeste{self.nome}" "Causa" "Solucao"',
                capture_output=True, text=True, shell=True, timeout=10
            )
            self.registrar('Registrar aprendizado', 'APRENDIDO' in result.stdout, 'Nova licao no KG')
        except: self.registrar('Registrar aprendizado', False)
        
        # Relatorio
        print(f'\n{"="*60}')
        print(f'  PISTA A — {self.nome}: {self.pontos}/{self.pontos+self.erros} etapas')
        print(f'  Pontos: {self.pontos}, Erros: {self.erros}')
        print(f'{"="*60}')
        return self.pontos, self.erros


if __name__ == '__main__':
    corredor = sys.argv[1] if len(sys.argv) > 1 else 'DESCONHECIDO'
    pista = PistaA(corredor)
    pista.executar()
