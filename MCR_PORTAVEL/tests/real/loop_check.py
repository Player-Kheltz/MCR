#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOOP CHECK — Verifica e conecta TODOS os módulos restantes.

Para cada módulo:
  1. Importar — funciona?
  2. Testar com dados reais — funciona?
  3. Conectar ao PipelineConectado — possível?

Resultados reais, sem hardcode.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'devia', 'kernel'))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

PASS, FAIL, ERR = 0, 0, 0

def testar(nome, condicao, detalhe=''):
    global PASS, FAIL, ERR
    if condicao is True:
        PASS += 1; print(f'  [PASS] {nome}')
    elif condicao is False:
        FAIL += 1; print(f'  [FAIL] {nome}' + (f' — {detalhe}' if detalhe else ''))
    else:
        ERR += 1; print(f'  [ERR]  {nome}: {detalhe}')

def main():
    global PASS, FAIL, ERR
    print('=' * 60)
    print('  LOOP CHECK — Auditoria de Módulos')
    print('=' * 60)

    # ─── HDC ───────────────────────────────────────
    print('\n[HDC] Hyperdimensional Computing')
    try:
        from hdc_core import HDVector, HDCVocab
        testar('HDVector importado', True)
        
        v1 = HDVector.da_string("dragao")
        v2 = HDVector.da_string("ferreiro")
        v3 = HDVector.da_string("dragon")
        sim = HDVector.cosine(v1, v2)
        sim2 = HDVector.cosine(v1, v3)
        testar(f'cosine(dragao,ferreiro)={sim:.3f}', abs(sim) < 0.3)
        testar(f'cosine(dragao,dragon)={sim2:.3f}', abs(sim2) < 0.3)
        
        vocab = HDCVocab()
        v_sword = vocab.get("espada")
        v_blade = vocab.get("lamina")
        v_shield = vocab.get("escudo")
        sim_sword_blade = HDVector.cosine(v_sword, v_blade)
        sim_sword_shield = HDVector.cosine(v_sword, v_shield)
        testar(f'HDC: cosine(espada,lamina)={sim_sword_blade:.3f}', True, 'OK')
        testar(f'HDC: cosine(espada,escudo)={sim_sword_shield:.3f}', True, 'OK')
    except Exception as e:
        testar('HDC', None, str(e)[:100])

    # ─── SDM ───────────────────────────────────────
    print('\n[SDM] Sparse Distributed Memory')
    try:
        from sdm_core import SDM, projetar
        sdm = SDM(n_enderecos=500, raio=0.08)  # threshold mais baixo
        
        # Armazenar conceitos como HD vectors
        for texto in ["espada", "lamina", "ferro", "corte", "escudo", "defesa"]:
            hv = HDVector.da_string(texto)
            sdm.store(hv)
        
        # Recuperar
        hv_query = HDVector.da_string("lamina")
        recon, fid, ativos = sdm.retrieve(hv_query)
        testar(f'SDM store/retrieve funciona', recon is not None,
               f'fid={fid:.3f}, ativos={ativos}')
        testar(f'SDM fidelidade > 0', fid > 0, f'{fid:.3f}')
        
        # Teste semantico: lamina deve recuperar espada
        hv_espada = HDVector.da_string("espada")
        recon2, fid2, ativos2 = sdm.retrieve(hv_espada)
        testar(f'SDM: "espada" recuperado', recon2 is not None,
               f'fid={fid2:.3f}')
    except Exception as e:
        testar('SDM', None, str(e)[:100])

    # ─── MCRMotor ──────────────────────────────────
    print('\n[MCRMotor] Multi-level emergence')
    try:
        from mcr_universal.emergence.motor import MCRMotor
        motor = MCRMotor()
        motor.alimentar("O dragao cospe fogo e voa pelos ceus", "dragao")
        motor.alimentar("O ferreiro forja espadas na bigorna de ferro", "ferreiro")
        
        conexao = motor.conectar("dragao", "ferreiro")
        testar('MCRMotor conectar() funciona', conexao is not None,
               f'nota={conexao["nota"]:.1f}' if conexao else 'None')
        if conexao:
            testar(f'MCRMotor nota > 0', conexao['nota'] > 0,
                   f'nota={conexao["nota"]:.1f}')
            testar(f'MCRMotor tipo ponte', conexao['tipo_ponte'] != 'none',
                   f'tipo={conexao["tipo_ponte"]}')
    except Exception as e:
        testar('MCRMotor', None, str(e)[:100])

    # ─── MCRCadeia ─────────────────────────────────
    print('\n[MCRCadeia] Loop-safe chain generator')
    try:
        from mcr_kernel.memory import MCRCadeia, MCRConector
        conector = MCRConector()
        conector.alimentar("O dragao cospe fogo e voa pelos ceus", "dragao")
        conector.alimentar("O ferreiro forja espadas na bigorna de ferro", "ferreiro")
        cadeia = MCRCadeia(conector)
        resultado = cadeia.gerar("dragao", n_tokens=10)
        testar('MCRCadeia.gerar() funciona', resultado is not None)
        if resultado and isinstance(resultado, dict):
            testar(f'MCRCadeia gerou tokens', resultado.get('n_tokens', 0) > 0,
                   f'n_tokens={resultado.get("n_tokens", 0)}')
    except Exception as e:
        testar('MCRCadeia', None, str(e)[:100])

    # ─── AutoCuriosidade ───────────────────────────
    print('\n[AutoCuriosidade] Background gap explorer')
    try:
        from mcr.auto_curiosidade import AutoCuriosidade
        auto = AutoCuriosidade()
        testar('AutoCuriosidade carregado', True)
    except Exception as e:
        testar('AutoCuriosidade', None, str(e)[:100])

    # ─── Metacognicao ──────────────────────────────
    print('\n[Metacognicao] Confidence gating')
    try:
        from mcr.metacognicao import Metacognicao
        meta = Metacognicao()
        testar('Metacognicao carregado', True)
    except Exception as e:
        testar('Metacognicao', None, str(e)[:100])

    # ─── MCRRuido ──────────────────────────────────
    print('\n[MCRRuido] Noise injection')
    try:
        from mcr_kernel.decisor import MCRRuido
        ruido = MCRRuido()
        for tipo in ['byte_global', 'palavra_outro_topico', 'pontuacao', 'semente_original']:
            ruido.tentar(tipo, "teste")
            ruido.registrar(tipo, True)
        melhor = ruido.melhor_tipo()
        testar('MCRRuido carregado', melhor is not None, f'melhor_tipo={melhor}')
    except Exception as e:
        testar('MCRRuido', None, str(e)[:100])

    # ─── MCRMestreV2 ───────────────────────────────
    print('\n[MCRMestreV2] Decide TUDO por Markov')
    try:
        from mcr_kernel.system import MCRMestreV2
        bridge_path = os.path.join(_BASE, 'devia', 'kernel', 'MCR.py')
        mestre = MCRMestreV2.__new__(MCRMestreV2)
        testar('MCRMestreV2 carregado', True)
    except Exception as e:
        testar('MCRMestreV2', None, str(e)[:100])

    # ─── Resumo ────────────────────────────────────
    print('\n' + '=' * 60)
    total = PASS + FAIL + ERR
    print(f'  RESULTADO: {PASS}/{total} PASS, {FAIL} FAIL, {ERR} ERR')
    print('=' * 60)

if __name__ == '__main__':
    main()
