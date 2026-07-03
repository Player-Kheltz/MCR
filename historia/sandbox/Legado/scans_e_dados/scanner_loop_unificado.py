"""
MCR-DevIA SCANNER AUTONOMO — Loop Unificado
Importa resolver_ultra, escaneia teste_cego_ultra em loop,
registra resultados no KG, exibe progresso.
Gerado via tools dele + complemento manual.
"""
import sys, os, time, json, importlib.util

SCANNER_PATH = r'E:\Projeto MCR\sandbox\resolver_ultra.py'
BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'
KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'

def registrar_aprendizado(texto):
    """Registra aprendizado no KG via mcr_devia.py"""
    import subprocess
    cmd = [
        'python', 'E:/Projeto MCR/scripts/mcr_devia/mcr_devia.py',
        'ensinar',
        texto[:80],
        'Descoberto durante scan autonomo',
        'Scanner loop detectou progresso',
        'autonomo'
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=15)

def licoes():
    if os.path.exists(KG_PATH):
        with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            return len(json.load(f).get('licoes', []))
    return 0

# Usa subprocess em vez de import (evita efeitos colaterais do modulo)
import subprocess, sys

# Log file para o observatorio
LOG_PATH = r'E:\Projeto MCR\sandbox\.mcr_heartbeat.log'

# Cerebro ML
sys.path.insert(0, 'E:/Projeto MCR/sandbox')
from mcr_ml_brain import CerebroML
cerebro = CerebroML()

def log_heartbeat(msg):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'[{time.strftime("%H:%M:%S")}] {msg}\n')

log_heartbeat('=== MCR-DevIA SCANNER AUTONOMO INICIADO ===')
log_heartbeat(f'Alvo: {BASE}')
log_heartbeat(f'KG inicial: {licoes()} licoes')
print('=== MCR-DevIA SCANNER AUTONOMO ===')
print(f'Alvo: {BASE}')
print(f'KG inicial: {licoes()} licoes')
print()

ciclo = 0
while True:
    ciclo += 1
    inicio = time.time()
    
    # Scan via subprocess (evita efeitos colaterais do modulo)
    r = subprocess.run([sys.executable, SCANNER_PATH], capture_output=True, text=True, timeout=120)
    output = r.stdout
    
    # Conta detectados
    encontrados = 0
    for line in output.split('\n'):
        if 'RESULTADO:' in line:
            import re
            m = re.search(r'(\d+)/(\d+)', line)
            if m: encontrados = int(m.group(1))
    
    dt = time.time() - inicio
    n_licoes = licoes()
    
    # Atualiza cerebro ML
    cerebro.data['metricas']['total_ciclos'] += 1
    for detector in ['loot_invalido', 'sql_injection', 'loop_infinito', 'setmetatable', 
                     'encoding_latin1', 'variavel_global', 'codigo_morto', 
                     'chave_string_numero', 'sintaxe_python', 'nil_desnecessario']:
        # Simula sucesso se o detector esta ativo (score basico)
        pass  # Placeholder - cada detector reporta seu status
    
    if encontrados > 0:
        cerebro.resetar_estagnacao()
    
    status = cerebro.status()
    log_heartbeat(f'Ciclo {ciclo}: {encontrados}/12 detectados | KG: {n_licoes} | ML: {status["deteccoes"]}d {status["correcoes"]}c {status["same_code"]}s')
    print(f'[{time.strftime("%H:%M:%S")}] Ciclo {ciclo}: {encontrados}/12 | KG: {n_licoes} | ML: {status["deteccoes"]}d {status["correcoes"]}c')
    
    # Crew V12: resolve problemas especificos com estrutura Python
    v12_result = sp.run(
        [sys.executable, 'E:/Projeto MCR/sandbox/mcr_crew_v12_solver.py'],
        capture_output=True, text=True, timeout=120
    )
    n_v12 = v12_result.stdout.count('CORRIGIDO')
    if n_v12 > 0:
        log_heartbeat(f'[CREW V12] {n_v12} problemas resolvidos (loop, nome, divisao)')
        cerebro.resetar_estagnacao()
    
    # Se encontrou problemas, ativa Review Crew para tentar corrigir
    if encontrados > 0:
        import subprocess as sp
        crew_result = sp.run(
            [sys.executable, 'E:/Projeto MCR/sandbox/mcr_review_crew.py'],
            capture_output=True, text=True, timeout=300
        )
        # Conta correcoes da crew
        n_crew = crew_result.stdout.count('[CREW] Implementador: correcao salva')
        if n_crew > 0:
            log_heartbeat(f'[REVIEW CREW] {n_crew} correcoes aplicadas')
            cerebro.resetar_estagnacao()
    
    # Aprendizado por reforco: se deteccao estagnou, tenta estrategia diferente
    if hasattr(sys, '_ultimos_resultados'):
        sys._ultimos_resultados.append(encontrados)
        if len(sys._ultimos_resultados) >= 5:
            ultimos = sys._ultimos_resultados[-5:]
            if max(ultimos) == min(ultimos):
                log_heartbeat(f'[REFORCO] Estagnado em {encontrados}/12 por 5 ciclos. Nova tentativa em 30s...')
                time.sleep(30)  # Pausa antes de tentar de novo
    else:
        sys._ultimos_resultados = [encontrados]
    
    # Se detectou algo novo, registra
    if encontrados > (sys._ultimos_resultados[0] if len(sys._ultimos_resultados) > 1 else 0):
        registrar_aprendizado(f'Scanner detectou {encontrados}/12 problemas autonomamente')
    
    # Sem sleep - comeca o proximo ciclo IMEDIATAMENTE
