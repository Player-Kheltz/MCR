#!/usr/bin/env python3
"""
MCR ENVIRONMENT LEARNER
=======================
Ensina o sistema a DESCOBRIR o ambiente sozinho.

Nao tem nada hardcoded. Ele procura, tenta, erra, aprende.

Ciclo de auto-descoberta:
  1. Tenta rodar MSBuild
  2. Se falhar, PROCURA onde esta o VS
  3. Tenta cada local possivel
  4. Quando achar, SALVA o conhecimento
  5. Proxima vez, ja sabe onde esta

Uso: python mcr_env.py
     python mcr_env.py --forget  (esquece tudo, reaprende)
"""

import sys, os, json, re, subprocess, glob as glob_mod

BASE = r'E:\Projeto MCR\sandbox'
KNOWLEDGE_PATH = os.path.join(BASE, '.mcr_knowledge.json')

# ============================================================
# CONHECIMENTO — O que o sistema ja aprendeu
# ============================================================

class Conhecimento:
    """O que o sistema ja descobriu sobre o ambiente."""
    
    def __init__(self):
        self.path = KNOWLEDGE_PATH
        self.data = self._carregar()
    
    def _carregar(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'vs_paths': {},       # caminhos de VS encontrados
            'msbuild_path': None,  # caminho do MSBuild
            'vcvars_path': None,   # caminho do vcvars64.bat
            'tentativas': 0,       # quantas vezes tentou
            'sucessos': 0,         # quantas vezes funcionou
            'historico': [],       # o que ja tentou
        }
    
    def salvar(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def aprender(self, chave, valor):
        """Aprende algo novo."""
        self.data[chave] = valor
        self.data['tentativas'] += 1
        self.salvar()
        print(f'  [APRENDIDO] {chave} = {str(valor)[:60]}')
    
    def registrar_historico(self, acao, resultado):
        """Registra o que tentou e o que aconteceu."""
        self.data['historico'].append({
            'acao': acao,
            'resultado': str(resultado)[:100],
            'data': str(__import__('datetime').datetime.now()),
        })
        if len(self.data['historico']) > 50:
            self.data['historico'] = self.data['historico'][-50:]
        self.salvar()


# ============================================================
# DESCOBRIDOR DE AMBIENTE — Procura ate achar
# ============================================================

class Descobridor:
    """Tenta varias estrategias ate descobrir o ambiente."""
    
    def __init__(self, conhecimento):
        self.conhecimento = conhecimento
    
    def descobrir_tudo(self):
        """Roda todas as descobertas."""
        print('\n[MCR ENVIRONMENT] Descobrindo ambiente...')
        
        # 1. Ja sabemos algo?
        if self.conhecimento.data.get('msbuild_path'):
            print(f'  Ja sei: MSBuild em {self.conhecimento.data["msbuild_path"]}')
            if self._testar_msbuild(self.conhecimento.data['msbuild_path']):
                return True
        
        # 2. Nao sabemos. Procurar!
        msbuild = self._procurar_msbuild()
        if msbuild:
            self.conhecimento.aprender('msbuild_path', msbuild)
            return True
        
        # 3. Procurar VS e derivar
        vs_path = self._procurar_vs()
        if vs_path:
            self.conhecimento.aprender('vs_path', vs_path)
            # Deriva MSBuild path
            msbuild_paths = [
                os.path.join(vs_path, 'MSBuild', 'Current', 'Bin', 'amd64', 'MSBuild.exe'),
                os.path.join(vs_path, 'MSBuild', 'Current', 'Bin', 'MSBuild.exe'),
            ]
            for p in msbuild_paths:
                if os.path.exists(p):
                    self.conhecimento.aprender('msbuild_path', p)
                    if self._testar_msbuild(p):
                        return True
        
        # 4. Procurar vcvars64.bat
        vcvars = self._procurar_vcvars()
        if vcvars:
            self.conhecimento.aprender('vcvars_path', vcvars)
        
        print('\n  Nao consegui descobrir o ambiente.')
        print('  Sugestoes:')
        print('    - Verifique se o Visual Studio esta instalado')
        print('    - Caminhos comuns: C:\\Program Files\\Microsoft Visual Studio\\2022\\Community')
        print('    - Ou use: python mcr_env.py --help')
        return False
    
    def _procurar_msbuild(self):
        """Procura MSBuild.exe em lugares comuns."""
        print('\n  Procurando MSBuild...')
        candidatos = [
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\MSBuild.exe',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe',
        ]
        
        for caminho in candidatos:
            self.conhecimento.registrar_historico('procurar_msbuild', caminho)
            if os.path.exists(caminho):
                print(f'  Encontrei! {caminho}')
                return caminho
        
        # Procura no ProgramData (VS Build Tools)
        for root, dirs, files in os.walk(r'C:\ProgramData'):
            for f in files:
                if f.lower() == 'msbuild.exe':
                    path = os.path.join(root, f)
                    print(f'  Encontrei! {path}')
                    return path
        
        print('  Nao encontrei MSBuild.')
        return None
    
    def _procurar_vs(self):
        """Procura diretorio do Visual Studio."""
        print('\n  Procurando Visual Studio...')
        bases = [
            r'C:\Program Files\Microsoft Visual Studio',
            r'C:\Program Files (x86)\Microsoft Visual Studio',
        ]
        
        for base in bases:
            if os.path.exists(base):
                for ano in sorted(os.listdir(base), reverse=True):  # Mais recente primeiro
                    path = os.path.join(base, ano, 'Community')
                    if os.path.exists(path):
                        print(f'  VS encontrado: {path}')
                        return path
                    path_pro = os.path.join(base, ano, 'Professional')
                    if os.path.exists(path_pro):
                        print(f'  VS encontrado: {path_pro}')
                        return path_pro
                    path_ent = os.path.join(base, ano, 'Enterprise')
                    if os.path.exists(path_ent):
                        print(f'  VS encontrado: {path_ent}')
                        return path_ent
        
        print('  Nao encontrei VS.')
        return None
    
    def _procurar_vcvars(self):
        """Procura vcvars64.bat (para configurar ambiente)."""
        print('\n  Procurando vcvars64.bat...')
        # Tenta a partir do VS que ja encontramos
        vs_path = self.conhecimento.data.get('vs_path', '')
        if vs_path:
            vcvars = os.path.join(vs_path, 'VC', 'Auxiliary', 'Build', 'vcvars64.bat')
            if os.path.exists(vcvars):
                print(f'  Encontrei! {vcvars}')
                return vcvars
        
        # Procura em lugares comuns
        candidatos = [
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat',
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\VC\Auxiliary\Build\vcvars64.bat',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat',
        ]
        for c in candidatos:
            if os.path.exists(c):
                print(f'  Encontrei! {c}')
                return c
        
        print('  Nao encontrei vcvars64.bat.')
        return None
    
    def _testar_msbuild(self, caminho):
        """Testa se o MSBuild funciona."""
        print(f'\n  Testando MSBuild...')
        try:
            r = subprocess.run([caminho, '/version'], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                versao = r.stdout.strip()[:50]
                print(f'  MSBuild funciona! Versao: {versao}')
                self.conhecimento.aprender('msbuild_version', versao)
                self.conhecimento.data['sucessos'] += 1
                self.conhecimento.salvar()
                return True
        except:
            pass
        print('  MSBuild nao funciona neste caminho.')
        return False


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='MCR Environment Learner')
    parser.add_argument('--forget', action='store_true', help='Esquece tudo e reaprende')
    parser.add_argument('--status', action='store_true', help='Mostra o que ja sabe')
    args = parser.parse_args()
    
    conhecimento = Conhecimento()
    
    if args.status:
        print('\n[MCR ENVIRONMENT] Conhecimento atual:')
        for chave, valor in conhecimento.data.items():
            if chave != 'historico':
                print(f'  {chave}: {str(valor)[:80]}')
        print(f'  Historico: {len(conhecimento.data.get("historico",[]))} entradas')
        return
    
    if args.forget:
        if os.path.exists(KNOWLEDGE_PATH):
            os.remove(KNOWLEDGE_PATH)
            print('Conhecimento esquecido!')
        conhecimento = Conhecimento()
    
    descobridor = Descobridor(conhecimento)
    descobridor.descobrir_tudo()
    
    print(f'\n[MCR ENVIRONMENT] Conhecimento salvo em: {KNOWLEDGE_PATH}')
    print(f'  Tentativas: {conhecimento.data["tentativas"]}')
    print(f'  Sucessos: {conhecimento.data["sucessos"]}')
    if conhecimento.data.get('msbuild_path'):
        print(f'  MSBuild: {conhecimento.data["msbuild_path"]}')
    if conhecimento.data.get('vcvars_path'):
        print(f'  Vcvars: {conhecimento.data["vcvars_path"]}')

if __name__ == '__main__':
    main()
