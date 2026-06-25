#!/usr/bin/env python3
"""
MCR BUILDER V2 — Loop Auto-Corretivo
======================================
Compila, diagnostica, aplica fix, recompila — ate passar.

O ciclo:
  1. Tenta compilar
  2. Se falhar → diagnostica
  3. Se erro CONHECIDO → Python aplica fix automatico
  4. Se erro DESCONHECIDO → IA sugere fix, Python tenta aplicar
  5. Recompila
  6. Loop ate 5x ou sucesso

Uso: python mcr_builder_v2.py canary
     python mcr_builder_v2.py otclient
     python mcr_builder_v2.py canary --learn
"""

import sys, os, json, re, subprocess, hashlib, urllib.request, shutil

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox'
BASE_ERROS = os.path.join(BASE, '.mcr_erros_v2')
os.makedirs(BASE_ERROS, exist_ok=True)

# ============================================================
# BANCO DE ERROS + FIXES AUTOMATICOS
# ============================================================

class BancoErros:
    def __init__(self):
        self.path = os.path.join(BASE_ERROS, 'erros.json')
        self.data = self._carregar()
    
    def _carregar(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'LNK2001': {
                'padrao': r'LNK2001.*__std_',
                'causa': 'ABI mismatch (MSVC 2022 vs 2026)',
                'fix': 'Usar VS 2026 para compilar OTClient',
                'tipo': 'dica',
            },
            'D9002': {
                'padrao': r'D9002',
                'causa': 'Flag C++ standard nao reconhecido',
                'fix_auto': {
                    'tipo': 'substituir_em_arquivos',
                    'arquivos': ['E:\\Projeto MCR\\OTClient\\vc17\\otclient.vcxproj'],
                    'de': 'stdcpplatest',
                    'para': 'stdcpp20',
                },
                'tipo': 'auto',
            },
            'C1083': {
                'padrao': r'C1083',
                'causa': 'Include nao encontrado',
                'fix': 'Verificar include paths no projeto',
                'tipo': 'dica',
            },
            'vcpkg': {
                'padrao': r'vcpkg',
                'causa': 'vcpkg nao configurado',
                'fix': 'Configurar VCPKG_ROOT',
                'tipo': 'dica',
            },
        }
    
    def salvar(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def aprender(self, codigo, info):
        self.data[codigo] = info
        self.salvar()


# ============================================================
# IA LOCAL (para erros desconhecidos)
# ============================================================

class IA:
    def gerar(self, prompt):
        try:
            data = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':0.4,'num_ctx':4096}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            r = json.loads(urllib.request.urlopen(req, timeout=120).read())
            return r.get('response','')
        except: return None


# ============================================================
# FIX APPLIER — Aplica correcoes em arquivos
# ============================================================

class FixApplier:
    """Aplica fixes em arquivos do projeto."""
    
    @staticmethod
    def aplicar(fix):
        """Aplica um fix automatico. Retorna True se aplicou."""
        if not isinstance(fix, dict):
            return False
        
        tipo = fix.get('tipo', '')
        
        if tipo == 'substituir_em_arquivos':
            arquivos = fix.get('arquivos', [])
            de = fix.get('de', '')
            para = fix.get('para', '')
            
            for path in arquivos:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read()
                    if de in conteudo:
                        # Backup
                        bak = path + '.bak'
                        if not os.path.exists(bak):
                            shutil.copy2(path, bak)
                        conteudo = conteudo.replace(de, para)
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(conteudo)
                        print(f'  [FIX] {os.path.basename(path)}: {de} -> {para}')
                        return True
            
            return False
        
        return False
    
    @staticmethod
    def aplicar_fix_ia(diagnostico):
        """Tenta aplicar um fix sugerido pela IA."""
        # Por enquanto, retorna dica pro usuario
        return False


# ============================================================
# COMPILADOR
# ============================================================

class CompiladorV2:
    def __init__(self):
        self.ia = IA()
        self.banco = BancoErros()
        self.applier = FixApplier()
    
    def compilar(self, projeto, config='Release', plataforma='x64'):
        cmds = {
            'canary': f'msbuild "E:\\Projeto MCR\\Canary\\vcproj\\canary.sln" /p:Configuration={config} /p:Platform={plataforma} /t:Build /m 2>&1',
            'otclient': f'msbuild "E:\\Projeto MCR\\OTClient\\vc17\\otclient-vc17.sln" /p:Configuration={config} /p:Platform={plataforma} /t:Build /m 2>&1',
        }
        cmd = cmds.get(projeto)
        if not cmd: return False, [f'Projeto: {projeto}']
        
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=300)
            output = r.stdout + r.stderr
            erros = [l.strip() for l in output.split('\n') if any(e in l for e in ['error','warning D','fatal','LNK'])]
            return r.returncode == 0, erros[:15]
        except subprocess.TimeoutExpired:
            return False, ['TIMEOUT']
        except Exception as e:
            return False, [str(e)]
    
    def diagnosticar(self, erros):
        diagnosticos = []
        for erro in erros[:5]:
            diag = None
            
            # Tenta erro conhecido
            for codigo, info in self.banco.data.items():
                if re.search(info.get('padrao','.*'), erro, re.IGNORECASE):
                    diag = {'erro': erro[:100], 'codigo': codigo, 'info': info, 'fonte': 'banco'}
                    break
            
            # Se desconhecido, IA analisa
            if not diag:
                prompt = f"Analise este erro de compilacao C++:\n{erro[:500]}\n\nResponda:\nCAUSA: (1 linha)\nFIX: (1 linha)\nARQUIVO: (arquivo afetado)"
                r = self.ia.gerar(prompt)
                causa = ''; fix = ''
                if r:
                    for line in r.split('\n'):
                        if line.upper().startswith('CAUSA:'): causa = line.split(':',1)[1].strip()
                        elif line.upper().startswith('FIX:'): fix = line.split(':',1)[1].strip()
                diag = {'erro': erro[:100], 'codigo': 'DESCONHECIDO', 'causa': causa or '?', 'fix': fix or '?', 'fonte': 'IA'}
            
            diagnosticos.append(diag)
        
        return diagnosticos
    
    def loop_auto(self, projeto, max_tentativas=5):
        """Loop principal: compila, diagnostica, corrige, repete."""
        print(f'\n{"="*60}')
        print(f'  LOOP AUTO-CORRETIVO: {projeto}')
        print(f'  Max {max_tentativas} tentativas')
        print(f'{"="*60}')
        
        for tentativa in range(1, max_tentativas + 1):
            print(f'\n--- Tentativa {tentativa}/{max_tentativas} ---')
            
            # Compila
            sucesso, erros = self.compilar(projeto)
            
            if sucesso:
                print(f'\n✅ COMPILACAO BEM-SUCEDIDA na tentativa {tentativa}!')
                return True
            
            print(f'  Erros: {len(erros)}')
            for e in erros[:3]:
                print(f'    {e[:100]}')
            
            # Diagnostica
            diagnosticos = self.diagnosticar(erros)
            
            # Tenta aplicar fixes
            fixes_aplicados = 0
            for d in diagnosticos:
                if d['fonte'] == 'banco':
                    info = d.get('info', {})
                    fix_auto = info.get('fix_auto')
                    if fix_auto:
                        if self.applier.aplicar(fix_auto):
                            fixes_aplicados += 1
                            print(f'  [FIX APLICADO] {d["codigo"]}')
                    else:
                        print(f'  [DICA] {d["codigo"]}: {info.get("fix","")}')
                else:
                    print(f'  [IA] {d["erro"][:60]}...')
                    print(f'  Causa: {d.get("causa","")}')
                    print(f'  Fix: {d.get("fix","")}')
            
            if fixes_aplicados == 0:
                print('  Nenhum fix automatico aplicado. Preciso de ajuda humana.')
                return False
        
        print(f'\n❌ Esgotaram as {max_tentativas} tentativas.')
        return False


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('projeto', nargs='?', default='canary')
    parser.add_argument('--tentativas', type=int, default=5)
    parser.add_argument('--learn', action='store_true')
    args = parser.parse_args()
    
    comp = CompiladorV2()
    
    print(f'Banco de erros: {len(comp.banco.data)} conhecidos')
    comp.loop_auto(args.projeto, args.tentativas)
    
    print(f'\nBanco de erros: {len(comp.banco.data)} conhecidos')
    print('Para adicionar mais erros: edite o banco ou aguarde a IA aprender.')

if __name__ == '__main__':
    main()
