#!/usr/bin/env python3
"""
MCR-DevIA — AUTO-MELHORIA v1.0
=================================
Aplica correcoes com base no diagnostico do auto_diagnostico.py.
Pode rodar autonomamente: diagnostico -> melhoria -> verificacao.

Uso:
    python mcr_auto_melhoria.py                         # analisa e mostra o que faria (dry-run)
    python mcr_auto_melhoria.py --aplicar               # aplica correcoes
    python mcr_auto_melhoria.py --aplicar --limpar-kg   # so limpa KG
    python mcr_auto_melhoria.py --status                # mostra o que ja foi feito

Fluxo autonomo completo:
    python mcr_auto_melhoria.py --aplicar && python mcr_auto_diagnostico.py
"""

import json, os, sys, shutil, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SANDBOX = os.path.dirname(__file__)
DEVIA_DIR = os.path.join(BASE, 'scripts', 'mcr_devia')
MCR_DEVIA_PATH = os.path.join(DEVIA_DIR, 'mcr_devia.py')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
LOG_PATH = os.path.join(SANDBOX, '.mcr_auto_melhoria_log.json')

# ============================================================
# LOG DE MELHORIAS
# ============================================================

def carregar_log():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding='utf-8') as f:
            return json.load(f)
    return {"versoes": 0, "melhorias": [], "timestamp_ultima": ""}

def salvar_log(log):
    log["timestamp_ultima"] = time.strftime("%Y-%m-%d %H:%M:%S")
    log["versoes"] += 1
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)

def registrar_melhoria(log, tipo, descricao, detalhes=None):
    log["melhorias"].append({
        "versao": log["versoes"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tipo": tipo,
        "descricao": descricao,
        "detalhes": detalhes or {}
    })

# ============================================================
# 1. LIMPEZA DO KG (remover lessons inativas)
# ============================================================

def limpar_kg(dry_run=True) -> dict:
    """Remove lessons inativas do arquivo KG."""
    resultado = {"acao": "dry-run" if dry_run else "aplicado", "removidas": 0, "tamanho_antes": 0, "tamanho_depois": 0}
    
    if not os.path.exists(KG_PATH):
        resultado["erro"] = "KG nao encontrado"
        return resultado
    
    # Backup
    backup_path = KG_PATH + '.backup'
    if not dry_run and not os.path.exists(backup_path):
        shutil.copy2(KG_PATH, backup_path)
        resultado["backup"] = backup_path
    
    with open(KG_PATH, encoding='utf-8') as f:
        kg = json.load(f)
    
    resultado["tamanho_antes"] = os.path.getsize(KG_PATH)
    
    licoes = kg.get('licoes', [])
    ativas = [l for l in licoes if not l.get('inactive', False)]
    removidas = len(licoes) - len(ativas)
    
    if dry_run:
        resultado["removidas"] = removidas
        resultado["restantes"] = len(ativas)
        resultado["economia_kb"] = round((resultado["tamanho_antes"] - (resultado["tamanho_antes"] * len(ativas) // max(1, len(licoes)))) / 1024, 1)
        return resultado
    
    # Aplicar: substituir licoes por apenas as ativas
    kg['licoes'] = ativas
    
    with open(KG_PATH, 'w', encoding='utf-8') as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)
    
    resultado["tamanho_depois"] = os.path.getsize(KG_PATH)
    resultado["removidas"] = removidas
    resultado["restantes"] = len(ativas)
    resultado["economia_kb"] = round((resultado["tamanho_antes"] - resultado["tamanho_depois"]) / 1024, 1)
    
    return resultado


# ============================================================
# 2. DEDUP DO KG (mesclar duplicatas)
# ============================================================

def dedup_kg(dry_run=True) -> dict:
    """Mescla lessons duplicadas (mesma solucao)."""
    resultado = {"acao": "dry-run" if dry_run else "aplicado", "mescladas": 0, "poupadas": 0}
    
    if not os.path.exists(KG_PATH):
        resultado["erro"] = "KG nao encontrado"
        return resultado
    
    with open(KG_PATH, encoding='utf-8') as f:
        kg = json.load(f)
    
    licoes = kg.get('licoes', [])
    # So opera em ativas
    ativas_idx = [i for i, l in enumerate(licoes) if not l.get('inactive', False)]
    inativas_idx = [i for i, l in enumerate(licoes) if l.get('inactive', False)]
    
    # Agrupa por solucao (primeiros 100 chars)
    grupos = {}
    for idx in ativas_idx:
        l = licoes[idx]
        chave = l.get('solucao', '')[:100].strip().lower()
        if chave not in grupos:
            grupos[chave] = []
        grupos[chave].append(idx)
    
    mescladas = 0
    novas_ativas = []
    for chave, idxs in grupos.items():
        if len(idxs) > 1:
            mescladas += len(idxs) - 1
            # Mantem a primeira, marca as outras como inativas
            principal = idxs[0]
            for i in idxs[1:]:
                licoes[i]['inactive'] = True
                licoes[i]['ctx'] = 'merged_duplicate'
    
    if dry_run:
        resultado["mescladas"] = mescladas
        return resultado
    
    # Salva
    with open(KG_PATH, 'w', encoding='utf-8') as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)
    
    resultado["mescladas"] = mescladas
    return resultado


# ============================================================
# 3. MARCAR LESSONS DE TESTE COMO INATIVAS
# ============================================================

def marcar_lessons_teste(dry_run=True) -> dict:
    """Marca lessons com 'teste' no erro como inativas."""
    resultado = {"acao": "dry-run" if dry_run else "aplicado", "marcadas": 0}
    
    if not os.path.exists(KG_PATH):
        resultado["erro"] = "KG nao encontrado"
        return resultado
    
    with open(KG_PATH, encoding='utf-8') as f:
        kg = json.load(f)
    
    licoes = kg.get('licoes', [])
    marcadas = 0
    for l in licoes:
        if not l.get('inactive', False) and 'teste' in l.get('erro', '').lower():
            if not dry_run:
                l['inactive'] = True
                l['ctx'] = 'test_auto_marked'
            marcadas += 1
    
    if marcadas and not dry_run:
        with open(KG_PATH, 'w', encoding='utf-8') as f:
            json.dump(kg, f, indent=2, ensure_ascii=False)
    
    resultado["marcadas"] = marcadas
    return resultado


# ============================================================
# 4. AUTO-MELHORIA COMPLETA
# ============================================================

def auto_melhoria(dry_run=True, etapas=None):
    """Executa todas as melhorias ou as especificadas."""
    log = carregar_log()
    
    if etapas is None:
        etapas = ['limpar_kg', 'dedup_kg', 'marcar_teste']
    
    resultados = {}
    
    if 'limpar_kg' in etapas:
        print(f'\n[Auto-Melhoria] Limpando lessons inativas do KG...')
        r = limpar_kg(dry_run)
        resultados['limpar_kg'] = r
        if dry_run:
            print(f'  [DRY-RUN] Removeria {r["removidas"]} lessons inativas (economia ~{r.get("economia_kb",0)} KB)')
        else:
            print(f'  [OK] Removidas {r["removidas"]} lessons inativas. Economia: {r.get("economia_kb",0)} KB')
            registrar_melhoria(log, 'kg_limpio', f'Removidas {r["removidas"]} lessons inativas do KG', r)
    
    if 'dedup_kg' in etapas:
        print(f'\n[Auto-Melhoria] Mesclando lessons duplicadas...')
        r = dedup_kg(dry_run)
        resultados['dedup_kg'] = r
        if dry_run:
            print(f'  [DRY-RUN] Mesclaria {r["mescladas"]} duplicatas')
        else:
            print(f'  [OK] Mescladas {r["mescladas"]} duplicatas')
            registrar_melhoria(log, 'kg_dedup', f'Mescladas {r["mescladas"]} lessons duplicadas', r)
    
    if 'marcar_teste' in etapas:
        print(f'\n[Auto-Melhoria] Marcando lessons de teste como inativas...')
        r = marcar_lessons_teste(dry_run)
        resultados['marcar_teste'] = r
        if dry_run:
            print(f'  [DRY-RUN] Marcar {r["marcadas"]} lessons de teste como inativas')
        else:
            print(f'  [OK] {r["marcadas"]} lessons de teste marcadas como inativas')
            registrar_melhoria(log, 'kg_marcar_teste', f'{r["marcadas"]} lessons de teste inativadas', r)
    
    if not dry_run:
        salvar_log(log)
    
    return resultados


def mostrar_status():
    """Mostra o que ja foi feito."""
    log = carregar_log()
    print(f"\n[Auto-Melhoria] Versao {log['versoes']} — Ultima: {log['timestamp_ultima']}")
    print(f"  Total de melhorias aplicadas: {len(log['melhorias'])}")
    for m in log['melhorias'][-10:]:
        print(f"  [{m['timestamp']}] {m['tipo']}: {m['descricao'][:100]}")


if __name__ == '__main__':
    if '--status' in sys.argv:
        mostrar_status()
    elif '--aplicar' in sys.argv:
        dry_run = False
        etapas = None
        if '--limpar-kg' in sys.argv:
            etapas = ['limpar_kg']
        elif '--dedup' in sys.argv:
            etapas = ['dedup_kg']
        elif '--marcar-teste' in sys.argv:
            etapas = ['marcar_teste']
        
        print("=" * 60)
        print("  MCR-DevIA — AUTO-MELHORIA (APLICANDO)")
        print("=" * 60)
        auto_melhoria(dry_run=False, etapas=etapas)
        print(f"\n[Auto-Melhoria] Concluido! Execute o diagnostico para verificar.")
    else:
        # Dry-run (padrao)
        print("=" * 60)
        print("  MCR-DevIA — AUTO-MELHORIA (DRY-RUN)")
        print("  Use --aplicar para aplicar as mudancas")
        print("=" * 60)
        auto_melhoria(dry_run=True)
        print(f"\n[Auto-Melhoria] DRY-RUN concluido. Nada foi alterado.")
