#!/usr/bin/env python3
"""Verifica e corrige arquivos de habilidade com chaves desbalanceadas."""
import os

BASE = r"E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades"
BKP = os.path.join(BASE, "_broken_bkp")

files_to_check = [
    "arcos.lua", "armas_punho.lua", "bastoes_arcanos.lua",
    "clavas_leves.lua", "clavas_pesadas.lua", "espadas_pesadas.lua",
    "lutador.lua", "machados_pesados.lua", "sobrevivencia.lua", "terra.lua"
]

os.makedirs(BKP, exist_ok=True)
fixed = 0

for fname in files_to_check:
    fpath = os.path.join(BASE, fname)
    if not os.path.exists(fpath):
        print(f"❌ {fname}: arquivo nao encontrado")
        continue
    
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    # Conta chaves
    opens = content.count("{")
    closes = content.count("}")
    diff = opens - closes
    
    if diff == 0:
        print(f"✅ {fname}: chaves balanceadas ({opens})")
        continue
    
    if diff > 0:
        print(f"⚠️  {fname}: faltam {diff} }} (opens={opens}, closes={closes})")
        # Faz backup
        import shutil
        shutil.copy2(fpath, os.path.join(BKP, fname))
        
        # Adiciona chaves faltando no final
        content = content.rstrip() + "\n" + "}" * diff + "\n"
        
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Verifica novamente
        opens2 = content.count("{")
        closes2 = content.count("}")
        if opens2 == closes2:
            print(f"  ✅ Corrigido! Adicionadas {diff} }} faltando")
            fixed += 1
        else:
            print(f"  ❌ Ainda desbalanceado: {opens2-closes2} diff")
    else:
        print(f"⚠️  {fname}: {abs(diff)} }} extras (opens={opens}, closes={closes})")

print(f"\nTotal corrigidos: {fixed}/{len(files_to_check)}")
