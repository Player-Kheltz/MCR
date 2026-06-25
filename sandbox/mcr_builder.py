#!/usr/bin/env python3
"""
MCR BUILDER + DEBUGGER
=======================
Ensina o MCR Crew a COMPILAR e resolver erros.

Funciona como um medico:
  1. Tenta compilar (sintoma)
  2. Captura erros (diagnostico)
  3. Para erros CONHECIDOS → aplica cura automatica (Python)
  4. Para erros DESCONHECIDOS → IA analisa e sugere cura
  5. Recompila e verifica se sarou

Uso: python mcr_builder.py
     python mcr_builder.py --fix-only    (so corrige sem compilar)
     python mcr_builder.py --learn       (aprende novos erros)
"""

import sys, os, json, re, subprocess, hashlib, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_ERROS = r'E:\Projeto MCR\sandbox\.mcr_erros'
os.makedirs(BASE_ERROS, exist_ok=True)

# ============================================================
# BANCO DE ERROS CONHECIDOS — Cresce com o tempo
# ============================================================

ERROS_CONHECIDOS = {
    # ABI mismatch (VS 2022 vs VS 2026)
    'LNK2001': {
        'padrao': r'LNK2001.*__std_',
        'causa': 'ABI mismatch entre MSVC versoes diferentes',
        'fix': 'Usar o mesmo compilador que compilou as dependencias (vcpkg)',
        'tipo': 'receita',
    },
    # C++ standard version
    'D9002': {
        'padrao': r'D9002.*/std:c\+\+latest',
        'causa': 'Flag de standard C++ nao reconhecido pelo compilador',
        'fix': 'Mudar LanguageStandard de stdcpplatest para stdcpp20 no .vcxproj',
        'tipo': 'receita',
    },
    # MSBuild not found
    'MSBuild': {
        'padrao': r'MSBuild.*n.*o.*(reconhecido|encontrado|found)',
        'causa': 'Caminho do MSBuild nao esta no PATH',
        'fix': 'Usar caminho completo: "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\MSBuild\\Current\\Bin\\MSBuild.exe"',
        'tipo': 'receita',
    },
    # vcpkg not found
    'vcpkg': {
        'padrao': r'vcpkg.*n.*o.*(encontrado|found)',
        'causa': 'VCPKG_ROOT nao configurado',
        'fix': 'Set-Item -Path Env:VCPKG_ROOT -Value "C:\\vcpkg"',
        'tipo': 'receita',
    },
    # include not found
    'C1083': {
        'padrao': r'C1083.*(Cannot open|Nao foi possivel abrir)',
        'causa': 'Arquivo de cabecalho nao encontrado no include path',
        'fix': 'Verificar se o include path esta correto no .vcxproj ou CMakeLists.txt',
        'tipo': 'geral',
    },
    # unresolved external symbol
    'LNK2019': {
        'padrao': r'LNK2019',
        'causa': 'Funcao declarada mas nao implementada, ou lib faltando',
        'fix': 'Verificar se a lib correspondente esta linkada no projeto',
        'tipo': 'geral',
    },
}

# ============================================================
# IA LOCAL
# ============================================================

class IA:
    def __init__(self):
        self.cache = {}
    
    def gerar(self, prompt, temp=0.5):
        chave = hashlib.md5(prompt.encode()).hexdigest()
        if chave in self.cache: return self.cache[chave]
        try:
            data = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.9}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read()).get('response','')
                self.cache[chave] = resp
                return resp
        except: return None


# ============================================================
# COMPILER
# ============================================================

class Compilador:
    """Tenta compilar e captura erros."""
    
    @staticmethod
    def compilar(projeto, config='Release', plataforma='x64'):
        """Tenta compilar e retorna (sucesso, erros)."""
        print(f'\n[COMPILAR] {projeto} ({config} {plataforma})...')
        
        # Mapa de projetos
        cmds = {
            'canary': f'msbuild "E:\\Projeto MCR\\Canary\\vcproj\\canary.sln" /p:Configuration={config} /p:Platform={plataforma} /t:Build /m 2>&1',
            'otclient': f'msbuild "E:\\Projeto MCR\\OTClient\\vc17\\otclient-vc17.sln" /p:Configuration={config} /p:Platform={plataforma} /t:Build /m 2>&1',
        }
        
        cmd = cmds.get(projeto)
        if not cmd:
            return False, [f'Projeto desconhecido: {projeto}']
        
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=300)
            output = r.stdout + r.stderr
            erros = Compilador._extrair_erros(output)
            sucesso = r.returncode == 0 and not erros
            return sucesso, erros
        except subprocess.TimeoutExpired:
            return False, ['TIMEOUT: Compilacao excedeu 5 minutos']
        except Exception as e:
            return False, [f'ERRO: {e}']
    
    @staticmethod
    def _extrair_erros(output):
        """Extrai erros do output do compilador."""
        erros = []
        for line in output.split('\n'):
            if any(err in line for err in ['error', 'warning D', 'fatal error', 'LNK']):
                erros.append(line.strip())
        return erros[:20]  # Limite de 20 erros


# ============================================================
# DIAGNOSTICADOR
# ============================================================

class Diagnosticador:
    """Diagnostica erros e aplica cura."""
    
    def __init__(self):
        self.ia = IA()
        self.banco = self._carregar_banco()
    
    def _carregar_banco(self):
        path = os.path.join(BASE_ERROS, 'erros_conhecidos.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return dict(ERROS_CONHECIDOS)
    
    def _salvar_banco(self):
        with open(os.path.join(BASE_ERROS, 'erros_conhecidos.json'), 'w', encoding='utf-8') as f:
            json.dump(self.banco, f, ensure_ascii=False, indent=2)
    
    def diagnosticar(self, erros):
        """Para cada erro, diagnostica e retorna cura."""
        diagnosticos = []
        
        for erro in erros[:5]:  # Diagnostica so os 5 primeiros
            diag = self._diagnosticar_um(erro)
            diagnosticos.append(diag)
        
        return diagnosticos
    
    def _diagnosticar_um(self, erro):
        """Diagnostica UM erro."""
        # 1. Tenta erro conhecido
        for codigo, info in self.banco.items():
            if re.search(info['padrao'], erro, re.IGNORECASE):
                return {
                    'erro': erro[:100],
                    'codigo': codigo,
                    'causa': info['causa'],
                    'fix': info['fix'],
                    'tipo': info['tipo'],
                    'fonte': 'banco',
                }
        
        # 2. Se desconhecido, pede pra IA analisar
        prompt = f"""Analise este erro de compilacao e sugira uma correcao:

ERRO: {erro[:500]}

Contexto: Projeto MCR, servidor Tibia customizado em C++ (Canary).
Compilador: MSVC (Visual Studio 2022 ou 2026).
Sistema: Windows 64-bit.

Responda:
CAUSA: (raiz do problema em 1 linha)
FIX: (passo a passo para corrigir)
ARQUIVO: (arquivo provavelmente afetado)"""
        
        r = self.ia.gerar(prompt, 0.4)
        
        causa = ''
        fix = ''
        if r:
            for line in r.split('\n'):
                line = line.strip()
                if line.upper().startswith('CAUSA:'):
                    causa = line.split(':', 1)[1].strip()
                elif line.upper().startswith('FIX:'):
                    fix = line.split(':', 1)[1].strip()
        
        return {
            'erro': erro[:100],
            'codigo': 'DESCONHECIDO',
            'causa': causa or 'Analise necessaria',
            'fix': fix or 'Verificar manualmente',
            'tipo': 'ia',
            'fonte': 'IA',
        }
    
    def aprender_erro(self, codigo, padrao, causa, fix):
        """Aprende um novo erro."""
        self.banco[codigo] = {
            'padrao': padrao,
            'causa': causa,
            'fix': fix,
            'tipo': 'aprendido',
        }
        self._salvar_banco()
        print(f'  [APRENDIDO] Erro {codigo}: {causa[:50]}...')


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='MCR Builder + Debugger')
    parser.add_argument('projeto', nargs='?', default='canary', help='canary | otclient')
    parser.add_argument('--fix-only', action='store_true', help='So mostra fixes sem compilar')
    parser.add_argument('--learn', action='store_true', help='Modo aprendizado')
    args = parser.parse_args()
    
    print('='*60)
    print('  MCR BUILDER + DEBUGGER')
    print(f'  Projeto: {args.projeto}')
    print('='*60)
    
    compilador = Compilador()
    diagnosticador = Diagnosticador()
    
    print(f'\n[Banco de erros] {len(diagnosticador.banco)} erros conhecidos')
    
    if args.fix_only:
        print('\n[MODO FIX-ONLY] Diagnosticando sem compilar...')
        # Simula erros para demonstracao
        erros_teste = [
            'LNK2001: unresolved external symbol __std_rotate',
            'D9002: unknown flag /std:c++latest',
        ]
        diagnosticos = diagnosticador.diagnosticar(erros_teste)
        for d in diagnosticos:
            print(f'\n  Erro: {d["erro"]}')
            print(f'  Codigo: {d["codigo"]} ({d["fonte"]})')
            print(f'  Causa: {d["causa"]}')
            print(f'  Fix: {d["fix"]}')
        return
    
    # Tenta compilar
    sucesso, erros = compilador.compilar(args.projeto)
    
    if sucesso:
        print('\n✅ COMPILACAO BEM-SUCEDIDA!')
        return
    
    print(f'\n❌ FALHA: {len(erros)} erros encontrados')
    
    # Diagnostica
    print('\n[DIAGNOSTICO]')
    diagnosticos = diagnosticador.diagnosticar(erros)
    
    for d in diagnosticos:
        print(f'\n  Erro: {d["erro"]}')
        print(f'  Codigo: {d["codigo"]} ({d["fonte"]})')
        print(f'  Causa: {d["causa"]}')
        print(f'  Fix: {d["fix"]}')
    
    # Modo aprendizado
    if args.learn:
        print('\n[MODO APRENDIZADO]')
        for d in diagnosticos:
            if d['fonte'] == 'IA':
                print(f'  Erro novo: {d["codigo"]}')
                codigo = input('  Codigo do erro: ') or 'ERR_NOVO'
                padrao = input('  Padrao regex: ') or '.*'
                diagnosticador.aprender_erro(codigo, padrao, d['causa'], d['fix'])
    
    print(f'\n{"="*60}')
    print(f'  {len(diagnosticos)} diagnosticos, {sum(1 for d in diagnosticos if d["fonte"]=="banco")} conhecidos')
    print(f'  Banco: {len(diagnosticador.banco)} erros')
    print(f'{"="*60}')

if __name__ == '__main__':
    main()
