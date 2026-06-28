#!/usr/bin/env python3
"""Benchmark: compara respostas SEM conselho vs COM conselho."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.util import fast, gerar
from kernel import MCRKernel
from personalidades.personalidade_analista import Analista
from personalidades.personalidade_critico import Critico

k = MCRKernel()
k.inicializar()

kg = k.contexto.get('kg')
ctx = f"MCR V{kg.data.get('versoes',0)} {len(kg.data.get('licoes',[]))} lessons"

perguntas = [
    "Qual a prioridade do projeto?",
    "Devemos migrar todos os comandos para o kernel?",
    "O watchdog e confiavel?",
]

print(f'{"="*80}')
print(f'BENCHMARK: SEM Conselho vs COM Conselho')
print(f'Contexto: {ctx}')
print(f'Perguntas: {len(perguntas)}')
print(f'{"="*80}')

resultados = []

for pergunta in perguntas:
    print(f'\n{"-"*80}')
    print(f'Pergunta: {pergunta}')
    print(f'{"-"*80}')
    
    row = {'pergunta': pergunta}
    
    # SEM conselho (resposta direta da IA)
    t0 = time.time()
    resposta_direta = fast(f"Pergunta: {pergunta}\nContexto: {ctx}\nResponda diretamente:", 0.3, "leve")
    t_direta = time.time() - t0
    row['sem_conselho'] = (resposta_direta or '')[:100]
    row['tempo_sem'] = round(t_direta, 1)
    
    print(f'  [DIRETA] ({t_direta:.1f}s) {resposta_direta[:80] if resposta_direta else "sem resposta"}...')
    
    # COM conselho (debate entre personalidades)
    t0 = time.time()
    analista = Analista()
    critico = Critico()
    op1 = analista.pensar(pergunta, ctx)
    op2 = critico.pensar(pergunta, ctx)
    
    debate_prompt = f"""Analista: {op1[:300]}
Critico: {op2[:300]}
Pergunta original: {pergunta}
Veredito final (2-3 frases):"""
    veredito = fast(debate_prompt, 0.3, "leve")
    t_conselho = time.time() - t0
    row['com_conselho'] = (veredito or '')[:100]
    row['tempo_com'] = round(t_conselho, 1)
    
    print(f'  [CONSELHO] ({t_conselho:.1f}s) {veredito[:80] if veredito else "sem resposta"}...')
    
    resultados.append(row)

print(f'\n{"="*80}')
print(f'TABELA DE COMPARACAO')
print(f'{"="*80}')
print(f'{"Pergunta":30s} {"Direta":20s} {"Conselho":20s} {"Ganho":10s}')
print(f'{"-"*30} {"-"*20} {"-"*20} {"-"*10}')
for r in resultados:
    t_sem = r['tempo_sem']
    t_com = r['tempo_com']
    ganho = f'{(t_com/t_sem-1)*100:+.0f}%'
    print(f'{r["pergunta"][:28]:30s} {t_sem:6.1f}s {t_com:6.1f}s {ganho:>10s}')

print(f'\n{"="*80}')
print(f'RESUMO:')
tempos_sem = [r['tempo_sem'] for r in resultados]
tempos_com = [r['tempo_com'] for r in resultados]
print(f'  Tempo medio SEM conselho: {sum(tempos_sem)/len(tempos_sem):.1f}s')
print(f'  Tempo medio COM conselho: {sum(tempos_com)/len(tempos_com):.1f}s')
print(f'  Diferenca: {(sum(tempos_com)/sum(tempos_sem)-1)*100:+.0f}%')
print(f'  Qualidade: Conselho oferece 2 perspectivas + debate vs 1 resposta direta')
print(f'{"="*80}')
