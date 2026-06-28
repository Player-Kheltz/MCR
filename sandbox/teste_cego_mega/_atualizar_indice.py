#!/usr/bin/env python3
"""Atualiza watchdog para salvar indice em arquivo.
Depois modifica ContextCrew para ler do arquivo.
Tudo via JSON IPC write."""
import json, subprocess, sys, os

WATCHDOG_PATH = r"E:\Projeto MCR\scripts\mcr_devia\modulos\watchdog.py"
CONTEXT_CREW_PATH = r"E:\Projeto MCR\scripts\mcr_devia\context_crew.py"
CMD_FILE = r"E:\Projeto MCR\sandbox\.mcr_cmd.json"

def ipc_write(path, conteudo):
    """Escreve arquivo via JSON IPC."""
    cmd = {"cmd": "write", "args": [path, conteudo]}
    with open(CMD_FILE, "w", encoding="utf-8") as f:
        json.dump(cmd, f, ensure_ascii=False)
    r = subprocess.run(
        [sys.executable, r"E:\Projeto MCR\scripts\mcr_devia\MCR_DevIA-Kernel.py", "--json", CMD_FILE],
        capture_output=True, text=True, errors="replace", timeout=30
    )
    return r.stdout

# === 1. Watchdog: salvar indice em arquivo ===
print("1. Atualizando Watchdog...")
with open(WATCHDOG_PATH, "r", encoding="utf-8") as f:
    wd = f.read()

# Adicionar salvamento do indice em arquivo
old = '        print(f\'[Watchdog] Indice: {len(self._indice)} palavras, {sum(len(v) for v in self._indice.values())} ocorrencias\')'
new = '''        indice_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'sandbox', '.mcr_devia', 'indice_watchdog.json')
        try:
            os.makedirs(os.path.dirname(indice_path), exist_ok=True)
            with open(indice_path, 'w', encoding='utf-8') as _f:
                import json as _jj
                _jj.dump(self._indice, _f, ensure_ascii=False)
        except:
            pass
        print(f'[Watchdog] Indice: {len(self._indice)} palavras, {sum(len(v) for v in self._indice.values())} ocorrencias')'''

if old in wd:
    wd = wd.replace(old, new)
    out = ipc_write(WATCHDOG_PATH, wd)
    if "Write]" in out:
        print("  Watchdog OK")
    else:
        print("  Watchdog ERRO:", out[-200:])
else:
    print("  AVISO: old string nao encontrada no watchdog")

# === 2. ContextCrew: ler indice do arquivo ===
print("2. Atualizando ContextCrew...")
with open(CONTEXT_CREW_PATH, "r", encoding="utf-8") as f:
    cc = f.read()

# Substituir _buscar_codigo para usar indice
old_cc = '''    def _buscar_codigo(self, termos, max_r=8):
        """Grep universal em diretorios CHAVE do projeto.
        ContextCrew ESTUDA, nunca modifica. Acesso universal a todo codigo relevante."""
        resultados = []'''

new_cc = '''    def _buscar_codigo(self, termos, max_r=8):
        """Grep usando INDICE do Watchdog (cache em arquivo). Fallback: varredura."""
        resultados = []
        
        # Tenta ler indice do watchdog (cache em arquivo)
        indice_path = os.path.join(SANDBOX, '.mcr_devia', 'indice_watchdog.json')
        if os.path.exists(indice_path):
            try:
                with open(indice_path, 'r', encoding='utf-8') as _f:
                    indice = json.load(_f)
                # Procura termos no indice
                arquivos_para_ler = set()
                for t in termos[:3]:
                    for palavra, arquivos in indice.items():
                        if t.lower() in palavra.lower():
                            for arq in arquivos[:3]:
                                if arq not in arquivos_para_ler:
                                    arquivos_para_ler.add(arq)
                # Le apenas os arquivos encontrados
                for fpath in arquivos_para_ler:
                    try:
                        if os.path.getsize(fpath) > 256000: continue
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                            lines = fh.readlines()
                        for i, line in enumerate(lines[:100]):
                            line_lower = line.lower()
                            score = sum(1 for t in termos if t in line_lower)
                            if score > 0 and len(line.strip()) > 20:
                                ctx_antes = ''.join(lines[max(0,i-1):i])
                                ctx_depois = ''.join(lines[i:min(len(lines),i+2)])
                                trecho = ctx_antes + line + ctx_depois
                                rel = os.path.relpath(fpath, BASE)
                                resultados.append((score, trecho[:200], f'Code:{rel}:L{i+1}'))
                                break
                    except: pass
                if resultados:
                    resultados.sort(key=lambda x: -x[0])
                    return [(r[1], r[2]) for r in resultados[:max_r]]
            except:
                pass
        
        # Fallback: varredura direta'''

if old_cc in cc:
    cc = cc.replace(old_cc, new_cc)
    out = ipc_write(CONTEXT_CREW_PATH, cc)
    if "Write]" in out:
        print("  ContextCrew OK")
    else:
        print("  ContextCrew ERRO:", out[-200:])
else:
    print("  AVISO: old_cc nao encontrado")
    # Mostra parte do arquivo para debug
    pos = cc.find("def _buscar_codigo")
    if pos >= 0:
        print(cc[pos:pos+300])

print("Concluido!")
