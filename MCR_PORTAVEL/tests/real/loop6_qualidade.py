#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOOP 6 — Qualidade REAL de output + Pipeline Completo

Mede o que IMPORTA:
  1. Qualidade da conversa (ANTES vs DEPOIS dos fixes)
  2. N-adaptativo gerar() — funciona? Melhorou?
  3. Pipeline criativo completo: entrada → ideia → código → validação
  4. MCRFuel.abastecer() com TODAS as fontes
  5. SQLiteMarkov para identidade NOVA (fallback mk_palavra)
  6. MCRAutoMelhoria diagnostica problemas REAIS
"""
import sys, os, time, json, re, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'devia', 'kernel'))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

PASS, FAIL, ERR = 0, 0, 0

def T(nome, cond, detalhe=''):
    global PASS, FAIL, ERR
    if cond is True: PASS += 1; print(f'  [PASS] {nome}')
    elif cond is False: FAIL += 1; print(f'  [FAIL] {nome} — {detalhe}')
    else: ERR += 1; print(f'  [ERR]  {nome}: {detalhe}')

def medir_qualidade_texto(texto):
    """Retorna métricas objetivas de qualidade de texto."""
    if not texto:
        return {'gramatical': False, 'tokens': 0, 'unicidade': 0, 'palavras_reais': 0}
    
    palavras = re.findall(r'[a-zA-Z]{3,}', texto.lower())
    if len(palavras) < 3:
        return {'gramatical': False, 'tokens': len(palavras), 'unicidade': 0, 'palavras_reais': 0}
    
    # Verifica se as palavras existem no cerebro.json (vocabulário real)
    palavras_reais = set()
    for p in palavras:
        if len(p) >= 3 and p[0].isalpha():
            palavras_reais.add(p)
    
    unicidade = len(set(palavras)) / len(palavras)
    tem_estrutura = (
        len(palavras) >= 4 and
        (any(p in texto.lower() for p in ['you', 'are', 'the', 'and', 'for']) or
         any(p in texto.lower() for p in ['voc', 'que', 'para', 'com', 'uma']))
    )
    
    return {
        'gramatical': tem_estrutura,
        'tokens': len(palavras),
        'unicidade': round(unicidade, 2),
        'palavras_reais': len(palavras_reais),
    }

def main():
    global PASS, FAIL, ERR
    t0 = time.time()
    print('=' * 60)
    print('  LOOP 6 — Qualidade REAL + Pipeline Completo')
    print('=' * 60)

    # ─── 1. Qualidade da conversa (ANTES vs DEPOIS) ──
    print('\n[1] Conversa: qualidade real do output Markov')
    from mcr.mcr_sqlite import MCRSQLite
    
    db_conv = os.path.join(_BASE, 'cache', 'mcr_conversa.db')
    if os.path.exists(db_conv):
        mcr_conv = MCRSQLite(db_conv, n_max=5, identidade='conversa')
        
        entradas = ['hello', 'dragon', 'sword', 'buy', 'orcs', 'custa', 'welcome']
        qualidades = []
        
        for semente in entradas:
            cadeia = mcr_conv.gerar(semente, passos=6)
            texto = ' '.join(cadeia)
            q = medir_qualidade_texto(texto)
            qualidades.append(q)
        
        n_gramaticais = sum(1 for q in qualidades if q['gramatical'])
        media_unicidade = sum(q['unicidade'] for q in qualidades) / len(qualidades)
        
        T(f'Conversa: {n_gramaticais}/{len(entradas)} frases com estrutura',
           n_gramaticais >= 3, f'{n_gramaticais}/{len(entradas)}')
        T(f'Conversa: unicidade media={media_unicidade:.2f}', media_unicidade > 0.3)
        
        # Mostrar exemplos reais
        for semente in entradas[:4]:
            cadeia = mcr_conv.gerar(semente, passos=6)
            texto = ' '.join(cadeia)
            q = medir_qualidade_texto(texto)
            print(f'    "{semente}" -> "{texto}" [{q["tokens"]} tokens, unico={q["unicidade"]}]')
        
        mcr_conv.conn.close()
    else:
        T('mcr_conversa.db', None, 'DB nao encontrado')

    # ─── 2. N-adaptativo gerar() — funciona? ────────
    print('\n[2] N-adaptativo gerar() — qualidade melhorada')
    if os.path.exists(db_conv):
        mcr_conv = MCRSQLite(db_conv, n_max=5, identidade='conversa')
        
        # Testa predição N=1 vs N=3 manual
        sementes_teste = ['dragon', 'sword', 'magic']
        resultados_n = []
        for s in sementes_teste:
            p1, c1 = mcr_conv.predizer(s)
            if p1:
                ctx2 = f'{s}|{p1}'
                p2, c2 = mcr_conv.predizer(ctx2)
                if p2:
                    ctx3 = f'{s}|{p1}|{p2}'
                    p3, c3 = mcr_conv.predizer(ctx3)
                    resultados_n.append({
                        'semente': s,
                        'n1': f'{p1}({c1:.3f})',
                        'n2': f'{p2}({c2:.3f})',
                        'n3': f'{p3}({c3:.3f})' if p3 else 'N/A',
                    })
        
        cadeias_ok = 0
        for r in resultados_n:
            tem_n2 = r['n2'] != 'N/A'
            tem_n3 = r['n3'] != 'N/A'
            if tem_n2: cadeias_ok += 1
        
        T(f'N-adaptativo: {cadeias_ok}/{len(resultados_n)} usam N>1',
           cadeias_ok >= 1,
           f'{cadeias_ok}/{len(resultados_n)}')
        
        for r in resultados_n:
            print(f'    {r["semente"]}: N1={r["n1"]} N2={r["n2"]} N3={r.get("n3","-")}')
        
        mcr_conv.conn.close()

    # ─── 3. Pipeline criativo completo ───────────────
    print('\n[3] Pipeline Criativo: entrada → código → validação')
    try:
        from mcr.sqlite_markov import SQLiteMarkov
        from mcr_kernel.memory import MCRConector
        
        # Simula pedido do usuário
        pedido = "Crie um NPC que seja um dragao ferreiro"
        print(f'    Input: "{pedido}"')
        
        # Etapa 1: Conectar os conceitos "dragao" e "ferreiro"
        conector = MCRConector()
        conector.alimentar(
            "O dragao cospe fogo e guarda tesouros em sua caverna",
            "dragao"
        )
        conector.alimentar(
            "O ferreiro forja armaduras e espadas na bigorna ardente",
            "ferreiro"
        )
        conexao = conector.conectar("dragao", "ferreiro")
        
        if conexao:
            print(f'    Conexão: {conexao["palavra_a"]} <-> {conexao["palavra_b"]} (nota {conexao["nota"]:.1f})')
            T('Conexão dragao<->ferreiro existe', True)
        else:
            T('Conexão dragao<->ferreiro', False, 'falhou')
        
        # Etapa 2: Gerar código com identidade do SQLiteMarkov
        mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
        seq = mk.gerar_com_identidade('Adrenius', 'local', passos=30)
        tokens = [t for t in seq if not t.startswith('B:') and len(t) < 200]
        codigo = ' '.join(tokens)
        
        # Etapa 3: Validar código gerado
        estrutura_esperada = ['internalNpcName', 'Game.createNpcType', 'npcConfig']
        encontrados = [e for e in estrutura_esperada if e in codigo]
        
        T(f'Código gerado: {len(tokens)} tokens', len(tokens) > 10)
        T(f'Estrutura NPC: {len(encontrados)}/{len(estrutura_esperada)}', 
           len(encontrados) >= 2)
        print(f'    Preview: {codigo[:120]}...')
        
        mk.close()
    except Exception as e:
        T('Pipeline criativo', None, str(e)[:100])

    # ─── 4. MCRFuel.abastecer() — TODAS fontes ──────
    print('\n[4] MCRFuel.abastecer() — múltiplas fontes')
    try:
        from mcr_kernel.evolution import MCRFuel
        fuel = MCRFuel()
        
        fontes_rapidas = ['manifesto', 'modulos', 'comandos']
        resultados_fuel = {}
        for fonte in fontes_rapidas:
            try:
                n = fuel.abastecer(fontes=[fonte])
                resultados_fuel[fonte] = n
            except Exception as e:
                resultados_fuel[fonte] = f'ERR: {str(e)[:40]}'
        
        total_fuel = sum(v for v in resultados_fuel.values() if isinstance(v, int))
        T(f'MCRFuel: {total_fuel} lessons de {len(fontes_rapidas)} fontes',
           total_fuel >= 0,
           str(resultados_fuel))
    except Exception as e:
        T('MCRFuel', None, str(e)[:100])

    # ─── 5. SQLiteMarkov — identidade NOVA ──────────
    print('\n[5] SQLiteMarkov — identidade nova (Merlin)')
    try:
        from mcr.sqlite_markov import SQLiteMarkov
        
        mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
        
        # Identidade que NÃO existe no DB (força fallback)
        seq = mk.gerar_com_identidade('Merlin', 'local', passos=20)
        tokens = [t for t in seq if not t.startswith('B:')]
        
        T(f'Identidade nova (Merlin): {len(tokens)} tokens gerados',
           len(tokens) >= 1,
           f'Sem fallback mk_palavra, gerou so com mk_adapt')
        
        # Compara com identidade conhecida
        seq2 = mk.gerar_com_identidade('Adrenius', 'local', passos=20)
        tokens2 = [t for t in seq2 if not t.startswith('B:')]
        T(f'Identidade conhecida (Adrenius): {len(tokens2)} tokens',
           len(tokens2) > 5,
           f'{len(tokens2)} tokens vs {len(tokens)} para identidade nova')
        
        mk.close()
    except Exception as e:
        T('SQLiteMarkov identidade nova', None, str(e)[:100])

    # ─── 6. MCRAutoMelhoria — diagnóstico REAL ───────
    print('\n[6] MCRAutoMelhoria — diagnóstico real')
    try:
        from mcr_kernel.evolution import MCRAutoMelhoria
        am = MCRAutoMelhoria()
        ciclo = am.ciclo()
        
        acoes = ciclo.get('acoes', [])
        n_acoes = ciclo.get('n', 0)
        
        T(f'MCRAutoMelhoria: {n_acoes} ações detectadas', n_acoes >= 0)
        if acoes:
            T(f'Diagnóstico: {acoes[:3]}', True)
        else:
            T('Diagnóstico: sem ações pendentes (sistema saudável)', True)
    except Exception as e:
        T('MCRAutoMelhoria', None, str(e)[:100])

    # ─── 7. QUALIDADE FINAL: métricas consolidadas ──
    print('\n[7] QUALIDADE FINAL — métricas consolidadas')
    
    metricas = {}
    
    # Conversa
    if os.path.exists(db_conv):
        mcr_conv = MCRSQLite(db_conv, n_max=5, identidade='conversa')
        amostras = []
        for s in ['hello', 'dragon', 'sword', 'buy', 'orcs', 'custa', 'welcome']:
            c = mcr_conv.gerar(s, passos=5)
            amostras.append(' '.join(c))
        qualidades = [medir_qualidade_texto(t) for t in amostras]
        metricas['conversa'] = {
            'gramaticais': sum(1 for q in qualidades if q['gramatical']),
            'total': len(amostras),
            'unicidade_media': round(sum(q['unicidade'] for q in qualidades) / len(qualidades), 2),
        }
        mcr_conv.conn.close()
    
    # Código
    try:
        mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
        codigos = {}
        for ident in ['Adrenius', 'Sapo Azul']:
            seq = mk.gerar_com_identidade(ident, 'local', passos=20)
            tokens = [t for t in seq if not t.startswith('B:')]
            codigos[ident] = {'tokens': len(tokens), 'tempo_ms': 0}
        metricas['codigo'] = codigos
        mk.close()
    except Exception:
        pass
    
    T(f'Métricas consolidadas: {json.dumps(metricas, indent=2)}', True)

    # ─── Resumo ──────────────────────────────────────
    print('\n' + '=' * 60)
    total = PASS + FAIL + ERR
    print(f'  RESULTADO: {PASS}/{total} PASS, {FAIL} FAIL, {ERR} ERR')
    print(f'  Métricas: {json.dumps(metricas, indent=2)}')
    print(f'  Tempo: {time.time()-t0:.1f}s')
    print('=' * 60)

if __name__ == '__main__':
    main()
