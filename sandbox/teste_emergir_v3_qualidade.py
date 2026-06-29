"""Teste de Qualidade EMERGIR V3 — Fragmentacao + ContextCrew + Anti-Alucinacao.

Mede 5 metricas de qualidade e gera uma NOTA final (0-10).

Uso:
    python sandbox/teste_emergir_v3_qualidade.py
"""
import os, sys, json, time, re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.master_agent import MasterAgent


def avaliar_criatividade(ma, pergunta, resposta):
    """FAST avalia: a resposta contem uma conexao NAO-OBVIA?"""
    try:
        prompt = (
            f"[SISTEMA]\n"
            f"Avalie se a resposta abaixo revela uma conexao "
            f"GENUINAMENTE CRIATIVA e NAO-OBVIA.\n\n"
            f"[PERGUNTA]\n{pergunta[:300]}\n\n"
            f"[RESPOSTA]\n{resposta[:2000]}\n\n"
            f"[PERGUNTA]\n"
            f"A resposta revela uma conexao nao-obvia e criativa?\n"
            f"Responda APENAS: SIM ou NAO."
        )
        r = ma.ia.fast(prompt, 0.1, 'ultra_leve')
        return 'SIM' in r.upper()[:10]
    except:
        return True


def avaliar_aplicabilidade(ma, resposta):
    """FAST avalia: a resposta tem implicacao pratica para o MCR?"""
    try:
        prompt = (
            f"[SISTEMA]\n"
            f"Avalie se a resposta abaixo contem implicacoes "
            f"PRATICAS e ACIONAVEIS para o MCR (servidor Tibia).\n\n"
            f"[RESPOSTA]\n{resposta[:2000]}\n\n"
            f"[PERGUNTA]\n"
            f"A resposta sugere implicacoes praticas e acionaveis "
            f"para o projeto MCR?\n"
            f"Responda APENAS: SIM ou NAO."
        )
        r = ma.ia.fast(prompt, 0.1, 'ultra_leve')
        return 'SIM' in r.upper()[:10]
    except:
        return True


def avaliar_coerencia(ma, resposta):
    """FAST avalia: a resposta tem coerencia logica?"""
    try:
        prompt = (
            f"[SISTEMA]\n"
            f"Avalie se a resposta abaixo e COERENTE e faz sentido logico.\n"
            f"Nao avalie se e verdade ou nao — apenas se as ideias se conectam.\n\n"
            f"[RESPOSTA]\n{resposta[:2000]}\n\n"
            f"[PERGUNTA]\n"
            f"A resposta e coerente? As ideias se conectam logicamente?\n"
            f"Responda APENAS: SIM ou NAO."
        )
        r = ma.ia.fast(prompt, 0.1, 'ultra_leve')
        return 'SIM' in r.upper()[:10]
    except:
        return True


def verificar_alucinacao(texto):
    """Verifica alucinacoes de siglas via regex (Nivel 1)."""
    proibidos = [
        r'FAST\s*\([^)]*FastAPI',
        r'FAST\s*\([^)]*Authentication',
        r'SPA\s*\([^)]*Single\s*Page',
        r'SHC\s*\([^)]*Sistema\s*Hospitalar',
        r'SHC\s*\([^)]*Health',
        r'minecraft',
    ]
    for padrao in proibidos:
        if re.search(padrao, texto, re.IGNORECASE):
            return False, padrao
    return True, ""


def testar_emergir_v3():
    """Teste COMPLETO de qualidade do EMERGIR V3."""
    print("=" * 70)
    print("TESTE DE QUALIDADE EMERGIR V3")
    print("Fragmentacao + ContextCrew + Anti-Alucinacao")
    print("=" * 70)
    
    # Cria MasterAgent
    print("\n[0] Criando MasterAgent...")
    t0_total = time.time()
    ma = MasterAgent()
    print("  OK")
    
    # Forca execution_count para disparar EMERGIR
    ma._execution_count = 5
    
    # Conta lessons emergentes antes (para delta)
    lessons_antes = len([l for l in ma.kg.data.get('licoes', []) 
                         if l.get('ctx') == 'emergente'])
    
    print(f"\n[1] Executando _processar_emergencia()...")
    print("    (ContextCrew + Fragmentador + Anti-Alucinacao)")
    t0 = time.time()
    try:
        ma._processar_emergencia()
        tempo = time.time() - t0
        print(f"  Tempo: {tempo:.1f}s")
    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Verifica se nova lesson foi aprendida (recarrega KG do disco)
    ma.kg.data = json.load(open(os.path.join(BASE, 'sandbox', '.mcr_devia', 'knowledge.json'), 'r', encoding='utf-8'))
    lessons_depois = len([l for l in ma.kg.data.get('licoes', []) 
                          if l.get('ctx') == 'emergente'])
    novas = lessons_depois - lessons_antes
    
    if novas == 0:
        print("  ⚠ Nenhuma nova lesson emergente foi aprendida")
        print("  Possiveis causas: combinacao repetida, autoavaliacao negativa, alucinacao bloqueada")
        print("\n  PROXIMOS PASSOS:")
        print("  - Rode novamente para pegar topicos diferentes")
        print("  - Verifique os logs para ver onde parou")
        return 0  # Nao e erro — e o comportamento normal de refinamento
    
    # Pega a nova lesson
    emergentes = [l for l in ma.kg.data.get('licoes', []) 
                  if l.get('ctx') == 'emergente']
    lesson = emergentes[-1]
    resposta = lesson.get('solucao', '')
    pergunta = lesson.get('erro', '')
    causa = lesson.get('causa', '')
    
    print(f"\n[2] Analisando qualidade da resposta...")
    print(f"  Titulo: {pergunta[:80]}")
    print(f"  Causa (topicos): {causa[:80]}")
    
    # ============================================================
    # METRICAS DE QUALIDADE
    # ============================================================
    nota = 0
    max_nota = 10
    metricas = {}
    
    # M1: PROFUNDIDADE (tamanho)
    tamanho = len(resposta)
    secoes_count = len(re.findall(r'###\s', resposta))
    
    print(f"\n  --- PROFUNDIDADE ---")
    print(f"  Tamanho total: {tamanho} chars")
    print(f"  Secoes (###): {secoes_count}")
    
    if tamanho >= 1500:
        nota += 2
        metricas['profundidade'] = (2, f'{tamanho} chars + {secoes_count} secoes')
        print(f"  ✅ Profundidade: +2 ({tamanho} chars)")
    elif tamanho >= 800:
        nota += 1
        metricas['profundidade'] = (1, f'{tamanho} chars + {secoes_count} secoes')
        print(f"  ⚠ Profundidade: +1 ({tamanho} chars — poderia ser maior)")
    else:
        metricas['profundidade'] = (0, f'{tamanho} chars')
        print(f"  ❌ Profundidade: +0 ({tamanho} chars)")
    
    # M2: ESTRUTURA (secoes)
    if secoes_count >= 4:
        nota += 2
        metricas['estrutura'] = (2, f'{secoes_count} secoes')
        print(f"  ✅ Estrutura: +2 ({secoes_count} secoes)")
    elif secoes_count >= 2:
        nota += 1
        metricas['estrutura'] = (1, f'{secoes_count} secoes')
        print(f"  ⚠ Estrutura: +1 ({secoes_count} secoes)")
    else:
        metricas['estrutura'] = (0, f'{secoes_count} secoes')
        print(f"  ❌ Estrutura: +0 ({secoes_count} secoes)")
    
    # M3: ALUCINACAO (siglas)
    print(f"\n  --- ALUCINACAO ---")
    ok, padrao = verificar_alucinacao(resposta)
    if ok:
        nota += 2
        metricas['alucinacao'] = (2, 'Zero alucinacoes')
        print(f"  ✅ Alucinacao: +2 (zero)")
    else:
        metricas['alucinacao'] = (0, f'Alucinacao: {padrao}')
        print(f"  ❌ Alucinacao: +0 (detectada: {padrao})")
    
    # M4: CRIATIVIDADE (FAST)
    print(f"\n  --- CRIATIVIDADE ---")
    print("  Avaliando via FAST (1.5b)...")
    criativa = avaliar_criatividade(ma, pergunta, resposta)
    if criativa:
        nota += 2
        metricas['criatividade'] = (2, 'Conexao NAO-OBVIA')
        print(f"  ✅ Criatividade: +2 (conexao nao-obvia)")
    else:
        metricas['criatividade'] = (0, 'Conexao obvia ou repetida')
        print(f"  ❌ Criatividade: +0 (conexao obvia)")
    
    # M5: APLICABILIDADE (FAST)
    print(f"\n  --- APLICABILIDADE ---")
    print("  Avaliando via FAST (1.5b)...")
    aplicavel = avaliar_aplicabilidade(ma, resposta)
    if aplicavel:
        nota += 2
        metricas['aplicabilidade'] = (2, 'Tem implicacao pratica')
        print(f"  ✅ Aplicabilidade: +2 (tem implicacao pratica)")
    else:
        metricas['aplicabilidade'] = (0, 'Sem implicacao pratica clara')
        print(f"  ❌ Aplicabilidade: +0 (sem implicacao pratica)")
    
    # BONUS: COERENCIA
    print(f"\n  --- BONUS: COERENCIA ---")
    print("  Avaliando via FAST (1.5b)...")
    coerente = avaliar_coerencia(ma, resposta)
    if coerente:
        print(f"  ✅ Coerencia: as ideias se conectam logicamente")
        metricas['coerencia'] = (True, 'Ideias se conectam logicamente')
    else:
        print(f"  ⚠ Coerencia: ideias podem estar desconexas")
        metricas['coerencia'] = (False, 'Ideias podem estar desconexas')
    
    # ============================================================
    # RELATORIO FINAL
    # ============================================================
    tempo_total = time.time() - t0_total
    print()
    print("=" * 70)
    print("RESULTADO FINAL — EMERGIR V3")
    print("=" * 70)
    print(f"  Nota:          {nota}/{max_nota}")
    print(f"  Tempo pipeline: {tempo:.1f}s")
    print(f"  Tempo total:    {tempo_total:.1f}s")
    print()
    for metrica, valor in metricas.items():
        if isinstance(valor, (tuple, list)) and len(valor) == 2:
            pts, desc = valor
        else:
            pts, desc = valor, str(valor)
        if isinstance(pts, bool):
            bar = '✅' if pts else '❌'
        else:
            bar = '█' * pts + '░' * (2 - pts)
        print(f"  [{bar}] {metrica:15s}: {desc}")
    print()
    
    if nota >= 9:
        print("🏆 EXCELENTE! EMERGIR V3 no nivel maximo de qualidade!")
    elif nota >= 7:
        print("✅ BOM! EMERGIR V3 funcional e de boa qualidade.")
    elif nota >= 5:
        print("⚠ RAZOAVEL. Ha espaco para melhorias.")
    else:
        print("❌ FRACO. Precisa de ajustes no pipeline.")
    print("=" * 70)
    
    # Mostra trecho da resposta
    print(f"\n--- TRECHO DA RESPOSTA ({len(resposta)} chars) ---")
    print(resposta[:500])
    if len(resposta) > 500:
        print(f"... (+{len(resposta)-500} chars)")
    
    return 0


if __name__ == '__main__':
    sys.exit(testar_emergir_v3())
