#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOOP 11 — Última Varredura: Suite Unificada + Stress + Identidade Nova

Tudo em um script. Resultados REAIS, sem hardcode.
"""
import sys, os, time, json, subprocess, re, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'devia', 'kernel'))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

PASS, FAIL, ERR = 0, 0, 0
TIMINGS = {}

def T(nome, cond, detalhe=''):
    global PASS, FAIL, ERR
    if cond is True: PASS += 1
    elif cond is False: FAIL += 1; print(f'  [FAIL] {nome} — {detalhe}')
    else: ERR += 1; print(f'  [ERR]  {nome}: {detalhe}')

def main():
    global PASS, FAIL, ERR, TIMINGS
    t0 = time.time()
    print('=' * 60)
    print('  LOOP 11 — Varredura Final')
    print('=' * 60)

    # ─── 1. Suite Unificada ─────────────────────────
    print('\n[1] Suite Unificada (todas as suites)')
    suites = [
        ('Pipeline', 'tests/real/test_final_8modulos.py'),
        ('Carga', 'tests/real/loop_check.py'),
        ('Funcional', 'tests/real/loop2_funcional.py'),
        ('Sprites', 'tests/real/loop5_sprites.py'),
        ('Qualidade', 'tests/real/loop6_qualidade.py'),
        ('Olhos', 'tests/real/loop6b_olhos.py'),
    ]
    
    total_pass = 0
    total_fail = 0
    for nome, script in suites:
        t1 = time.time()
        r = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=120)
        TIMINGS[nome] = round(time.time() - t1, 1)
        for line in r.stdout.split('\n'):
            if 'RESULTADO:' in line:
                nums = re.findall(r'(\d+)/(\d+)', line)
                if nums:
                    p, t = int(nums[0][0]), int(nums[0][1])
                    total_pass += p
                    total_fail += (t - p) if t > p else 0
                print(f'  {nome}: {line.strip()} ({TIMINGS[nome]}s)')

    taxa = total_pass / max(total_pass + total_fail, 1) * 100
    T(f'Suite Unificada: {total_pass}/{total_pass+total_fail} = {taxa:.1f}%', taxa >= 99)

    # ─── 2. Stress Test — 10 gerações concorrentes ──
    print('\n[2] Stress Test — 10 gerações concorrentes')
    from mcr.sqlite_markov import SQLiteMarkov

    resultados_concorrentes = []
    lock = threading.Lock()

    def gerar_ident(ident, results):
        try:
            mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
            t1 = time.time()
            seq = mk.gerar_com_identidade(ident, 'local', passos=20)
            tempo = time.time() - t1
            tokens = [t for t in seq if not t.startswith('B:') and len(t) < 200]
            with lock:
                results.append({'ident': ident, 'tokens': len(tokens), 'tempo_ms': round(tempo*1000, 2)})
            mk.close()
        except Exception as e:
            with lock:
                results.append({'ident': ident, 'erro': str(e)[:50]})

    identidades = ['Adrenius', 'Ahmet', 'Sapo Azul', 'Adrenius', 'Sapo Azul',
                   'Ahmet', 'Adrenius', 'Sapo Azul', 'Ahmet', 'Adrenius']
    
    t_stress = time.time()
    threads = []
    for ident in identidades:
        t = threading.Thread(target=gerar_ident, args=(ident, resultados_concorrentes))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    tempo_stress = time.time() - t_stress

    sucessos = sum(1 for r in resultados_concorrentes if 'erro' not in r)
    tokens_total = sum(r.get('tokens', 0) for r in resultados_concorrentes)
    tempos = [r.get('tempo_ms', 0) for r in resultados_concorrentes if 'erro' not in r]
    tempo_medio = sum(tempos) / len(tempos) if tempos else 0

    T(f'Stress: {sucessos}/{len(identidades)} OK, {tokens_total} tokens, '
      f'{tempo_medio:.1f}ms médio, {tempo_stress:.1f}s total',
      sucessos >= 9)

    # ─── 3. Identidade NOVA (não existe no DB) ──────
    print('\n[3] Identidade nova (Merlin, Kheltz, DragonLord)')
    identidades_novas = ['Merlin', 'Kheltz', 'DragonLord']
    for ident in identidades_novas:
        try:
            mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
            seq = mk.gerar_com_identidade(ident, 'local', passos=20)
            tokens = [t for t in seq if not t.startswith('B:') and len(t) < 200]
            mk.close()
            T(f'{ident}: {len(tokens)} tokens', len(tokens) >= 1,
              f'{"gerou" if len(tokens) > 1 else "sem dados no DB para esta identidade"}')
        except Exception as e:
            T(ident, None, str(e)[:60])

    # ─── 4. Contagem final de módulos ──────────────
    print('\n[4] Status final do PipelineConectado')
    from mcr.adaptadores import PipelineConectado
    pipe = PipelineConectado()
    s = pipe.status()
    conectados = sum(1 for v in s.values() if v)
    for k, v in s.items():
        print(f'  {k:20s} {"OK" if v else "OFF"}')
    T(f'Módulos: {conectados}/{len(s)} conectados', conectados >= 17)
    pipe.close()

    # ─── Resumo Final ───────────────────────────────
    total_tempo = time.time() - t0
    print('\n' + '=' * 60)
    print(f'  LOOP 11 — VERIFICAÇÕES: {PASS} pass, {FAIL} fail, {ERR} err')
    print(f'  Suite Unificada: {total_pass}/{total_pass+total_fail} = {taxa:.1f}%')
    print(f'  Stress: {sucessos}/10 concorrentes, {tokens_total} tokens, {tempo_stress:.1f}s')
    print(f'  Tempo total: {total_tempo:.1f}s')
    print('=' * 60)

if __name__ == '__main__':
    main()
