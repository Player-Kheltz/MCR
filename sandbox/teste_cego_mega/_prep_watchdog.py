#!/usr/bin/env python3
"""Prepara alteracao no Watchdog: adiciona indice invertido.
Depois usa JSON IPC write para MCR-DevIA salvar."""
import json, os, sys, re

WATCHDOG_PATH = r"E:\Projeto MCR\scripts\mcr_devia\modulos\watchdog.py"

# Ler watchdog atual
with open(WATCHDOG_PATH, "r", encoding="utf-8") as f:
    current = f.read()

# Metodo de consulta ao indice
INDEX_METHOD = r'''
    def consultar_indice(self, termo, max_r=5):
        """Consulta indice invertido. Retorna arquivos que contem o termo."""
        termo_lower = termo.lower()
        resultados = []
        for palavra, arquivos in self._indice.items():
            if termo_lower in palavra:
                for arq in arquivos[:3]:
                    if arq not in resultados:
                        resultados.append(arq)
        return resultados[:max_r]
    
    def _atualizar_indice(self):
        """Atualiza indice invertido com arquivos dos diretorios monitorados."""
        self._indice = {}
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        dirs = [
            os.path.join(base, 'scripts', 'mcr_devia'),
            os.path.join(base, 'sandbox'),
            os.path.join(base, 'docs'),
        ]
        for d in dirs:
            if not os.path.isdir(d): continue
            for root, dirs2, files in os.walk(d):
                dirs2[:] = [x for x in dirs2 if not x.startswith('.') and x not in ('__pycache__','node_modules','vcpkg')]
                for f in files:
                    if not f.endswith(('.py','.md','.txt','.json','.lua','.cpp','.h','.hpp')): continue
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                            conteudo = fh.read()
                        palavras = set(re.findall(r'\b[a-zA-Z_]{3,}\b', conteudo.lower()))
                        for p in palavras:
                            if p not in self._indice:
                                self._indice[p] = []
                            if fpath not in self._indice[p]:
                                self._indice[p].append(fpath)
                    except: pass
        print(f'[Watchdog] Indice: {len(self._indice)} palavras, {sum(len(v) for v in self._indice.values())} ocorrencias')
'''

# Adicionar no __init__
current = current.replace(
    "self._auto_revisor = None",
    "self._auto_revisor = None\n        self._indice = {}  # Indice invertido para ContextCrew"
)

# Adicionar atualizacao no _loop (antes do sleep)
current = current.replace(
    "        while self._rodando:\n            time.sleep(self.intervalo)",
    "        while self._rodando:\n            if not self._indice:\n                self._atualizar_indice()\n            time.sleep(self.intervalo)"
)

# Adicionar os metodos ao final da classe
# Encontra o final da classe Watchdog
last_method_end = current.rfind("            except:\n                                pass")
if last_method_end > 0:
    # Encontra o proximo \n\n apos isso
    insert_pos = current.find("\n\n", last_method_end)
    if insert_pos > 0:
        current = current[:insert_pos] + INDEX_METHOD + current[insert_pos:]

# Salva num arquivo temporario para write
with open(r"E:\Projeto MCR\sandbox\.mcr_watchdog_novo.py", "w", encoding="utf-8") as f:
    f.write(current)

print(f"Watchdog modificado: {len(current)} chars")
print("OK")
