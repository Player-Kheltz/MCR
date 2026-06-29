"""Wrapper que faz o scanner rodar em loop autonomo"""
import subprocess, time, sys, os

SCANNER = r'E:\Projeto MCR\sandbox\resolver_ultra.py'

print('=== MCR-DevIA SCANNER AUTONOMO ===')
print('Escaneando teste_cego_ultra a cada 30s')
print()

ciclo = 0
while True:
    ciclo += 1
    print(f'[{time.strftime("%H:%M:%S")}] Ciclo {ciclo}')
    
    r = subprocess.run([sys.executable, SCANNER], capture_output=True, text=True, timeout=120)
    
    # Extrair resultado
    for line in r.stdout.split('\n'):
        if 'RESULTADO' in line or 'CORRIGIDO' in line or 'FINAL' in line:
            print(f'  {line.strip()}')
    
    # Se detectou algo, registrar progresso
    if 'CORRIGIDO' in r.stdout:
        n_corrigidos = r.stdout.count('CORRIGIDO')
        print(f'  -> {n_corrigidos} correcoes aplicadas')
    
    time.sleep(30)
