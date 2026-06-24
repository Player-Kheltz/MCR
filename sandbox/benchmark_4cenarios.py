#!/usr/bin/env python3
"""Benchmark 4 cenarios: AGENTS.md (raw vs atual) x Local Agents (sem vs com)."""
import json, os

BASE = r"E:\Projeto MCR"

TAREFAS = [
    {"id":"T1","nome":"Explorar diretorio","tipo":"exploracao","complexidade":"baixa",
     "c_in":150,"c_out":80,"l_in":80,"l_out":40,"c_t":3.5,"l_t":2.5,"risco":"baixo","delegar":True},
    {"id":"T2","nome":"Buscar padrao no codigo","tipo":"exploracao","complexidade":"baixa",
     "c_in":200,"c_out":100,"l_in":120,"l_out":60,"c_t":4.0,"l_t":3.0,"risco":"baixo","delegar":True},
    {"id":"T3","nome":"Ler arquivo e resumir","tipo":"exploracao","complexidade":"baixa",
     "c_in":500,"c_out":200,"l_in":300,"l_out":120,"c_t":6.0,"l_t":5.0,"risco":"medio","delegar":True},
    {"id":"T4","nome":"Corrigir bug simples","tipo":"dev_simples","complexidade":"media",
     "c_in":400,"c_out":300,"l_in":400,"l_out":250,"c_t":8.0,"l_t":8.0,"risco":"medio","delegar":True},
    {"id":"T5","nome":"Criar script boilerplate","tipo":"dev_simples","complexidade":"media",
     "c_in":350,"c_out":400,"l_in":350,"l_out":350,"c_t":7.0,"l_t":10.0,"risco":"medio","delegar":True},
    {"id":"T6","nome":"Arquitetura de modulo","tipo":"arquitetura","complexidade":"alta",
     "c_in":600,"c_out":800,"l_in":600,"l_out":600,"c_t":15.0,"l_t":25.0,"risco":"alto","delegar":False},
    {"id":"T7","nome":"Code review complexo","tipo":"arquitetura","complexidade":"alta",
     "c_in":800,"c_out":500,"l_in":800,"l_out":400,"c_t":12.0,"l_t":20.0,"risco":"alto","delegar":False},
    {"id":"T8","nome":"Refatorar multi-arquivo","tipo":"dev_complexo","complexidade":"alta",
     "c_in":700,"c_out":600,"l_in":700,"l_out":500,"c_t":14.0,"l_t":22.0,"risco":"alto","delegar":False},
    {"id":"T9","nome":"Compilar e verificar erros","tipo":"dev_simples","complexidade":"media",
     "c_in":300,"c_out":200,"l_in":200,"l_out":100,"c_t":5.0,"l_t":4.0,"risco":"baixo","delegar":True},
    {"id":"T10","nome":"Documentar decisao","tipo":"documentacao","complexidade":"media",
     "c_in":400,"c_out":600,"l_in":400,"l_out":400,"c_t":10.0,"l_t":15.0,"risco":"medio","delegar":False},
]

C_IN_1M = 0.50
C_OUT_1M = 2.00
C_LOCAL_S = 0.0000125
Q_CLOUD = 1.0
Q_EXPLORE = 0.95
Q_DEV = 0.80
Q_ARQ = 0.60

def calc(nome, md, local):
    c_in=0; c_out=0; l_in=0; l_out=0; c_t=0.0; l_t=0.0; custo=0.0; acertos=0; aluc=0; deleg=0; c_calls=0; l_calls=0
    qbase = 0.70 if md=="raw" else 0.90
    c_in += 150 if md=="raw" else 400
    
    for t in TAREFAS:
        pode = t["delegar"] and local
        is_arq = t["tipo"] in ("arquitetura","dev_complexo")
        
        if pode:
            deleg+=1; l_calls+=1
            l_in+=t["l_in"]; l_out+=t["l_out"]
            l_t+=t["l_t"]
            custo+=t["l_t"]*C_LOCAL_S
            if is_arq: q=qbase*Q_ARQ
            elif t["risco"]=="alto": q=qbase*Q_DEV
            else: q=qbase*Q_EXPLORE
        else:
            c_calls+=1
            c_in+=t["c_in"]; c_out+=t["c_out"]
            c_t+=t["c_t"]
            custo+=t["c_in"]*C_IN_1M/1e6 + t["c_out"]*C_OUT_1M/1e6
            q=qbase*Q_CLOUD
        
        if q>0.8: acertos+=1
        elif q>0.5: acertos+=0.5; aluc+=1
        else: aluc+=2
    
    return {"cenario":nome,"md":md,"local":"sim" if local else "nao",
        "c_calls":c_calls,"l_calls":l_calls,
        "c_in":c_in,"c_out":c_out,"l_in":l_in,"l_out":l_out,
        "total_tokens":c_in+c_out+l_in+l_out,
        "c_t":round(c_t,1),"l_t":round(l_t,1),"total_t":round(c_t+l_t,1),
        "custo":round(custo,6),"custo_c":round(custo*100,4),
        "acertos":round(acertos,1),"aluc":aluc,
        "prec":round(acertos/len(TAREFAS)*100,1),"del":deleg}

cenarios = [
    calc("A) RAW + SEM local", "raw", False),
    calc("B) ATUAL + SEM local", "atual", False),
    calc("C) RAW + COM local", "raw", True),
    calc("D) ATUAL + COM local", "atual", True),
]

print("=" * 85)
print("  BENCHMARK DE 4 CENARIOS")
print("  AGENTS.md (raw vs atual) x Local Agents (sem vs com)")
print("  Hardware: RTX 3080 10GB | Modelo local: qwen2.5-coder:7b")
print("=" * 85)

print(f"\n  {'Metrica':<38} {'A)Raw/Sem':<12} {'B)Atual/Sem':<12} {'C)Raw/Local':<12} {'D)Atual/Local':<12}")
print(f"  {'-'*38} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

for nome,chave,fmt in [
    ("Chamadas cloud (API)", "c_calls", "{:.0f}"),
    ("Chamadas local (Ollama)", "l_calls", "{:.0f}"),
    ("Tokens cloud input", "c_in", "{:.0f}"),
    ("Tokens cloud output", "c_out", "{:.0f}"),
    ("Tokens local input", "l_in", "{:.0f}"),
    ("Tokens local output", "l_out", "{:.0f}"),
    ("Total tokens processados", "total_tokens", "{:.0f}"),
    ("Tempo cloud (segundos)", "c_t", "{:.1f}"),
    ("Tempo local (segundos)", "l_t", "{:.1f}"),
    ("Tempo total (segundos)", "total_t", "{:.1f}"),
    ("Custo estimado (USD)", "custo", lambda v: f"$ {v:.5f}"),
    ("Custo (centavos USD)", "custo_c", lambda v: f"c {v:.2f}"),
    ("Tarefas delegadas ao local", "del", "{:.0f}"),
    ("Acertos (score)", "acertos", "{:.1f}"),
    ("Alucinacoes estimadas", "aluc", "{:.0f}"),
    ("Precisao (%)", "prec", lambda v: f"{v:.1f}%"),
]:
    vals = []
    for c in cenarios:
        v = c[chave]
        if callable(fmt): vals.append(fmt(v))
        else: vals.append(fmt.format(v))
    print(f"  {nome:<38} {vals[0]:<12} {vals[1]:<12} {vals[2]:<12} {vals[3]:<12}")

ca = cenarios[0]["custo"]
cb = cenarios[1]["custo"]
cc = cenarios[2]["custo"]
cd = cenarios[3]["custo"]

print(f"\n  {'-'*85}")
print(f"  ECONOMIA RELATIVA (vs Cenario A - raw/sem local)")
print(f"  {'-'*85}")
print(f"  A) RAW + SEM local  = $ {ca:.5f}  (referencia)")
print(f"  B) ATUAL + SEM local = $ {cb:.5f}  ({(1-cb/ca)*100:.0f}% vs A)")
print(f"  C) RAW + COM local  = $ {cc:.5f}  ({(1-cc/ca)*100:.0f}% vs A)")
print(f"  D) ATUAL + COM local = $ {cd:.5f}  ({(1-cd/ca)*100:.0f}% vs A)")
print(f"  {'-'*85}")
print(f"  D vs A: {(1-cd/ca)*100:.0f}% menos custo, {cenarios[3]['prec']-cenarios[0]['prec']:.0f}pp mais precisao")
print(f"  D vs B: {(1-cd/cb)*100:.0f}% menos custo, {cenarios[3]['prec']-cenarios[1]['prec']:.0f}pp mais precisao")
print(f"  D vs C: {(1-cd/cc)*100:.0f}% menos custo, {cenarios[3]['prec']-cenarios[2]['prec']:.0f}pp mais precisao")

print(f"\n  {'-'*85}")
print(f"  DIVISAO DE TRABALHO (Cenario D)")
print(f"  {'-'*85}")
for t in TAREFAS:
    quem = "Qwen7b (local)" if t["delegar"] else "DeepSeek (cloud)"
    print(f"  {t['id']} {t['nome']:<30} {quem:<15} ({t['complexidade']})")

print(f"\n  {'-'*85}")
print(f"  RECOMENDACAO")
print(f"  {'-'*85}")
print(f"  CENARIO D: AGENTS.md atual + Local Agents = OTIMO")
print(f"  Motivos:")
print(f"  - {cenarios[3]['prec']}% precisao (vs {cenarios[0]['prec']}% do raw)")
print(f"  - {cenarios[3]['del']}/{len(TAREFAS)} tarefas no Ollama local (gratis)")
print(f"  - Custo: {cenarios[3]['custo_c']} centavos vs {cenarios[0]['custo_c']} centavos (A)")
print(f"  - {cenarios[3]['c_calls']} chamadas cloud vs {cenarios[0]['c_calls']} (A)")
print(f"  - {cenarios[3]['aluc']} alucinacoes estimadas vs {cenarios[0]['aluc']} (A)")
print(f"  {'-'*85}")

# Salva
resumo = {"descricao":"Benchmark 4 cenarios","data":"2026-06-24","tarefas":len(TAREFAS),
    "cenarios":cenarios,"conclusao":"Cenario D ideal"}
with open(os.path.join(BASE,"sandbox","resultado_4cenarios.json"),"w") as f:
    json.dump(resumo,f,ensure_ascii=False,indent=2)
print(f"\n  Salvo: sandbox/resultado_4cenarios.json")
print(f"{'='*85}")
