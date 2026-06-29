"""Teste rapido do Self-Study - scan + metricas."""
import sys, os, time
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))
from modulos.master_agent import MasterAgent

ma = MasterAgent()
print('Escaneando projeto...')
t0 = time.time()
arquivos = ma._escanear_projeto(max_arquivos=60)
print('Encontrados', len(arquivos), 'arquivos em', round(time.time()-t0,1), 's')
metricas = ma._extrair_metricas(arquivos)
print('Total:', metricas['total_arquivos'], 'arquivos,', metricas['total_linhas'], 'linhas')
print('Modulos:', metricas['total_modulos'], '| Classes:', metricas['total_classes'], '| Funcoes:', metricas['total_funcoes'])
print('Media linhas/arquivo:', metricas['media_linhas_arquivo'])
print()
print('Top 5 maiores:')
for a in metricas['top5_maiores']:
    print(' ', a['dir_prio'], a['nome'], '-', a['linhas'], 'linhas,', a['funcoes'], 'funcoes')
