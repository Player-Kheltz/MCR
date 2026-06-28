#!/usr/bin/env python3
"""
MCR AUTO-BUILDER V3 — Auto-Configura + Compila + Corrige
===========================================================
Nao precisa de configuracao. Ele descobre TUDO sozinho.

Fluxo:
  1. Sabe onde esta o VS? Nao? → Descobre (mcr_env)
  2. Sabe compilar? Nao? → Configura ambiente
  3. Compila
  4. Erro? → Diagnostica, corrige, recompila (loop)

Uso: python mcr_autobuild.py
     python mcr_autobuild.py canary
     python mcr_autobuild.py otclient
     python mcr_autobuild.py --status
"""

import sys, os, json, re, subprocess, shutil, glob, urllib.request, hashlib

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
KNOWLEDGE_PATH = os.path.join(SANDBOX, '.mcr_knowledge.json')

# ============================================================
# CONHECIMENTO PERSISTENTE
# ============================================================

class Conhecimento:
    def __init__(self):
        self.path = KNOWLEDGE_PATH
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        base = {
            'msbuild_path': None,
            'vs_path': None,
            'vcvars_path': None,
            'compilou_com_sucesso': [],
            'falhas_conhecidas': {},
            'tentativas': 0,
        }
        self._save(base)
        return base
    
    def _save(self, data=None):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data or self.data, f, ensure_ascii=False, indent=2)
    
    def save(self):
        self._save(self.data)
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value
        self.save()


# ============================================================
# FASE 1: AUTO-DESCOBERTA
# ============================================================

class AutoDescobrir:
    """Descobre o ambiente de compilacao."""
    
    def __init__(self, conhecimento):
        self.conhecimento = conhecimento
    
    def executar(self):
        """Tenta descobrir o necessario para compilar."""
        print('[AUTO-DESCOBERTA]')
        
        # Ja sabemos o suficiente?
        msbuild = self.conhecimento.get('msbuild_path')
        if msbuild and os.path.exists(msbuild):
            print(f'  Ja sei: MSBuild = {os.path.basename(os.path.dirname(msbuild))}')
            return True
        
        # Procurar MSBuild
        print('  Procurando MSBuild...')
        candidatos = [
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe',
        ]
        
        for c in candidatos:
            if os.path.exists(c):
                self.conhecimento.set('msbuild_path', c)
                # Deriva VS path
                vs = c
                for _ in range(6):
                    vs = os.path.dirname(vs)
                if 'Microsoft Visual Studio' in vs:
                    self.conhecimento.set('vs_path', vs)
                print(f'  Encontrei: {c}')
                return True
        
        print('  [ERRO] MSBuild nao encontrado!')
        print('  Instale o Visual Studio ou as Build Tools.')
        return False


# ============================================================
# FASE 2: COMPILAR
# ============================================================

class Compilar:
    def __init__(self, conhecimento):
        self.conhecimento = conhecimento
    
    def executar(self, projeto='canary'):
        """Compila o projeto."""
        msbuild = self.conhecimento.get('msbuild_path')
        if not msbuild:
            print('[ERRO] MSBuild nao configurado')
            return False, []
        
        slns = {
            'canary': os.path.join(BASE, 'Canary', 'vcproj', 'canary.sln'),
            'otclient': os.path.join(BASE, 'OTClient', 'vc17', 'otclient-vc17.sln'),
        }
        sln = slns.get(projeto)
        if not sln or not os.path.exists(sln):
            print(f'[ERRO] Solucao nao encontrada: {sln}')
            return False, []
        
        print(f'[COMPILAR] {projeto}...')
        print(f'  Solucao: {os.path.basename(sln)}')
        
        cmd = f'"{msbuild}" "{sln}" /p:Configuration=Release /p:Platform=x64 /t:Build /m'
        
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=600)
            output = r.stdout + r.stderr
            erros = [l.strip() for l in output.split('\n') if any(e in l for e in 
                     ['error', 'fatal error', 'LNK', 'D9002'])]
            if erros:
                print(f'  Erros: {len(erros)}')
                for e in erros[:3]:
                    print(f'    {e[:120]}')
                return False, erros
            print(f'  [OK] Compilado com sucesso!')
            return True, []
        except subprocess.TimeoutExpired:
            print(f'  [TIMEOUT] Compilacao excedeu 10 minutos')
            return False, ['TIMEOUT']
        except Exception as e:
            print(f'  [ERRO] {e}')
            return False, [str(e)]


# ============================================================
# FASE 3: DIAGNOSTICO E CORRECAO
# ============================================================

class DiagnosticarCorrigir:
    def __init__(self, conhecimento):
        self.conhecimento = conhecimento
        self.ia_available = self._check_ia()
    
    def _check_ia(self):
        try:
            from modulos.util import fast as _fast_ab
            resp = _fast_ab("teste de conectividade", 0.1, "fast")
            return bool(resp)
        except:
            return False
    
    def executar(self, erros):
        """Diagnostica erros e aplica correcoes."""
        print(f'\n[DIAGNOSTICO] {len(erros)} erros')
        fixes_aplicados = []
        
        for erro in erros[:5]:
            fix = self._diagnosticar_um(erro)
            if fix:
                print(f'  Diagnostico: {fix.get("causa","?")[:80]}')
                if fix.get('acao'):
                    resultado = self._aplicar_fix(fix)
                    if resultado:
                        fixes_aplicados.append(fix)
                        print(f'  [FIX] Aplicado!')
        
        return len(fixes_aplicados) > 0
    
    def _diagnosticar_um(self, erro):
        """Diagnostica UM erro."""
        erro_lower = erro.lower()
        
        # Erros conhecidos
        if 'LNK2001' in erro and '__std_' in erro:
            return {'causa': 'ABI mismatch (VS 2022 vs VS 2026)', 'dica': 'Use o VS correto para este projeto', 'acao': 'dica'}
        
        if 'D9002' in erro:
            return {'causa': 'Flag C++ standard invalido', 'dica': 'stdcpplatest -> stdcpp20', 'acao': 'fix_vcxproj', 'de': 'stdcpplatest', 'para': 'stdcpp20'}
        
        if 'C1083' in erro:
            return {'causa': 'Include nao encontrado', 'dica': 'Verifique os include paths', 'acao': None}
        
        # Se IA disponivel, tenta
        if self.ia_available:
            prompt = f"Responda em formato JSON:\n{{\"causa\":\"...\",\"solucao\":\"...\",\"arquivo\":\"...\"}}\n\nErro de compilacao C++:\n{erro[:500]}"
            try:
                from modulos.util import gerar as _gerar_ab
                r = _gerar_ab(prompt, 0.3, "fast") or ""
                
                import json as j
                try:
                    parsed = j.loads(re.search(r'\{.*\}', r, re.DOTALL).group())
                    return {'causa': parsed.get('causa','?'), 'dica': parsed.get('solucao','?'), 'arquivo': parsed.get('arquivo',''), 'acao': 'ia'}
                except Exception as e:
                    print(f"[Fix] ERRO: {e}")
            except:
                pass
        
        return None
    
    def _aplicar_fix(self, fix):
        """Aplica uma correcao."""
        acao = fix.get('acao')
        
        if acao == 'fix_vcxproj':
            de = fix.get('de', '')
            para = fix.get('para', '')
            if not de or not para:
                return False
            
            # Procura arquivos vcxproj
            for root, dirs, files in os.walk(os.path.join(BASE, 'OTClient', 'vc17')):
                for f in files:
                    if f.endswith('.vcxproj'):
                                path = os.path.join(root, f)
                                with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                                    conteudo = fp.read()
                                if de in conteudo:
                                    shutil.copy2(path, path + '.bak_autofix')
                                    conteudo = conteudo.replace(de, para)
                                    with open(path, 'w', encoding='utf-8') as fp:
                                        fp.write(conteudo)
                                    return True
            return False
        
        if acao == 'dica' or acao == 'ia':
            return False  # So mostra dica, nao aplica automatico
        
        return False


# ============================================================
# MAIN — Orquestrador
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='MCR Auto-Builder V3')
    parser.add_argument('projeto', nargs='?', default='canary', help='canary | otclient')
    parser.add_argument('--status', action='store_true', help='Mostra conhecimento atual')
    parser.add_argument('--forget', action='store_true', help='Esquece tudo')
    args = parser.parse_args()
    
    conhecimento = Conhecimento()
    
    if args.status:
        print('\n[MCR AUTO-BUILDER] Conhecimento:')
        for k, v in conhecimento.data.items():
            if v: print(f'  {k}: {str(v)[:80]}')
        return
    
    if args.forget:
        if os.path.exists(KNOWLEDGE_PATH):
            os.remove(KNOWLEDGE_PATH)
            print('Conhecimento resetado!')
        return
    
    print(f'{"="*60}')
    print(f'  MCR AUTO-BUILDER V3')
    print(f'  Projeto: {args.projeto}')
    print(f'  Conhecimento: {sum(1 for v in conhecimento.data.values() if v)} itens')
    print(f'{"="*60}')
    
    # FASE 1: Auto-descobrir
    descobrir = AutoDescobrir(conhecimento)
    if not descobrir.executar():
        return
    
    # FASE 2-3: Loop compilar + corrigir
    compilar = Compilar(conhecimento)
    corrigir = DiagnosticarCorrigir(conhecimento)
    
    for tentativa in range(1, 6):
        print(f'\n--- Tentativa {tentativa}/5 ---')
        
        sucesso, erros = compilar.executar(args.projeto)
        
        if sucesso:
            conhecimento.data['compilou_com_sucesso'].append(args.projeto)
            conhecimento.save()
            print(f'\n✅ SUCESSO! Projeto compilado.')
            return
        
        if not erros:
            print('  Sem erros detectados (msbuild pode nao ter rodado)')
            return
        
        if not corrigir.executar(erros):
            print('  Nao foi possivel corrigir automaticamente.')
            return
    
    print(f'\n❌ Esgotaram as tentativas.')

if __name__ == '__main__':
    main()
