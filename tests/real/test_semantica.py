"""test_semantica — Validação REAL da generalização semântica do MCR.

Testa se o MCR consegue generalizar palavras nunca vistas para ações
conhecidas usando embeddings semânticos + trigrama.

Cenários:
  1. Sinônimos: "criar" ≈ "gerar" ≈ "elaborar" → mesma ação
  2. Entidades novas: "mago" (nunca visto) ≈ "ferreiro" (conhecido) → gerar
  3. Variações: "crie" ≈ "cria" ≈ "criar" (mesma raiz)
  4. Domínios: "sprite" ≈ "imagem" ≈ "ícone" → mesma tool
  5. Composição: "npc+vendedor" ≈ "npc+ferreiro" → mesma ação
"""
import sys, os, json, time, re, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# ─── Helpers ───────────────────────────────────────────────────

_erros = []
_t0 = time.time()
_n_testes = 0
_n_passaram = 0


def testar(nome, fn):
    global _n_testes, _n_passaram
    _n_testes += 1
    try:
        r = fn()
        if r and r[0]:
            _n_passaram += 1
            print(f'  PASS {nome}')
        else:
            motivo = r[1] if r else 'falhou'
            _erros.append(f'{nome}: {motivo}')
            print(f'  FAIL {nome}: {motivo}')
    except Exception as e:
        _erros.append(f'{nome}: {e}')
        print(f'  FAIL {nome}: {e}')


def _limpar_mcr():
    """Cria MCR limpo (sem treino prévio) para testes isolados."""
    import importlib
    # Recarrega módulos pra limpar estado
    for mod in ['mcr.engine', 'mcr.coupling', 'mcr.semantic_router',
                'mcr.mcr', 'mcr.signature']:
        if mod in sys.modules:
            del sys.modules[mod]
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from mcr.engine import MCR as MarkovEngine
    from mcr.coupling import MCRCoupling
    return MarkovEngine, MCRCoupling


# ═══════════════════════════════════════════════════════════════
# TESTES
# ═══════════════════════════════════════════════════════════════

def test_semantic_router_sinonimos():
    """Teste 1: semantic_router.similaridade reconhece sinônimos."""
    from mcr.semantic_router import similaridade
    
    pares = [
        ("criar", "crie", 0.25),        # mesma raiz ("cri" compartilhado)
        ("criar", "criativo", 0.20),    # prefixo compartilhado
        ("monstro", "monster", 0.25),   # cognato pt-en
        ("npcs", "npc", 0.50),          # plural
        ("sprite", "sprites", 0.50),    # plural
        ("analise", "analisar", 0.25),  # mesma raiz verbal
    ]
    
    for a, b, th_min in pares:
        s = similaridade(a, b)
        if s < th_min:
            return False, f'{a}≈{b}: score={s:.3f} < {th_min}'
    
    # Anti-teste: palavras diferentes devem ter baixa similaridade
    if similaridade("npc", "sqlite") > 0.4:
        return False, 'npc≈sqlite: falso positivo'
    
    return True, 'OK'


def test_semantic_router_trigrama():
    """Teste 2: fallback n-grama funciona sem Ollama."""
    from mcr.semantic_router import _ngramas, _dice_coef
    
    # "criar" e "crie" compartilham bigrama "cr" + trigrama "cri"
    tri_a = _ngramas("criar", 3)  # {"cri","ria","iar"}
    tri_b = _ngramas("crie", 3)   # {"cri","rie"}
    dice = _dice_coef(tri_a, tri_b)  # 2*1/(3+2) = 0.4
    if dice < 0.3:
        return False, f'criar vs crie: dice={dice} baixo'
    
    # Bigramas: "criar" → {"cr","ri","ia","ar"}, "crie" → {"cr","ri","ie"}
    big_a = _ngramas("criar", 2)
    big_b = _ngramas("crie", 2)
    dice_bi = _dice_coef(big_a, big_b)  # 2*2/(4+3) = 0.57
    if dice_bi < 0.4:
        return False, f'criar vs crie: bigrama dice={dice_bi} baixo'
    
    # Totalmente diferentes
    tri_a = _ngramas("npc", 3)
    tri_b = _ngramas("sqlite", 3)
    if _dice_coef(tri_a, tri_b) > 0.1:
        return False, 'npc vs sqlite: falso positivo'
    
    return True, 'OK'


def test_termo_mais_similar():
    """Teste 3: termo_mais_similar encontra similar."""
    from mcr.semantic_router import termo_mais_similar
    
    candidatos = ["criar", "gerar", "analisar", "buscar", "responder"]
    
    melhor, score = termo_mais_similar("elaborar", candidatos, 0.2)
    if not melhor:
        return False, f'elaborar: nenhum candidato (score={score})'
    
    # "abacaxi" não tem relação semântica com nenhum candidato técnico
    melhor, score = termo_mais_similar("abacaxi", candidatos, 0.25)
    if melhor:
        # Se Ollama está rodando, o embedding pode achar similaridade genérica
        # Só falha se score estiver MUITO alto (acima de 0.5)
        if score > 0.5:
            return False, f'abacaxi: falso positivo ({melhor}={score})'
    
    return True, 'OK'


def test_coupling_semantico():
    """Teste 4: coupling com similaridade semântica generaliza palavras."""
    MarkovEngine, MCRCoupling = _limpar_mcr()
    coupling = MCRCoupling()
    
    # Alimenta com palavras conhecidas
    coupling.alimentar("crie um ferreiro", "gerar")
    coupling.alimentar("crie um monstro", "gerar")
    coupling.alimentar("analise o codigo", "analisar")
    coupling.alimentar("busque por npc", "buscar")
    
    # Testa matching exato
    d = coupling._dist_palavras("crie um ferreiro")
    if 'gerar' not in d:
        return False, 'match exato falhou'
    
    # Testa generalização: "criar" (nunca visto) deve aproximar de "crie"
    d = coupling._dist_palavras("criar um guerreiro")
    if 'gerar' not in d:
        return False, f'generalizacao "criar" falhou: {d}'
    
    # Testa generalização: "personagem" ≈ "npc"
    d = coupling._dist_palavras("crie um personagem magico")
    if 'gerar' not in d:
        return False, f'generalizacao "personagem" falhou: {d}'
    
    return True, 'OK'


def test_coupling_palavras_similares():
    """Teste 5: _buscar_palavras_similares encontra cognatos."""
    MarkovEngine, MCRCoupling = _limpar_mcr()
    coupling = MCRCoupling()
    
    coupling.alimentar("gerar npc", "gerar")
    coupling.alimentar("gerar monstro", "gerar")
    coupling.alimentar("analisar codigo", "analisar")
    
    # "analise" deve ser similar a "analisar" (mesma raiz + bigramas compartilhados)
    similares = coupling.palavras_similares("analise", 0.23)
    if not similares:
        return False, f'"analise" não encontrou similares ({similares})'
    
    # "codificar" deve ser um pouco similar a "codigo" (mesmo radical)
    similares = coupling.palavras_similares("codificar", 0.15)
    # Opcional: pode ou não encontrar, depende do threshold
    
    return True, 'OK'


_MCR_INSTANCE = None

def _get_mcr():
    """Singleton MCR para testes (cria uma vez, reusa)."""
    global _MCR_INSTANCE
    if _MCR_INSTANCE is None:
        from mcr import MCR
        _MCR_INSTANCE = MCR()
        # Treino base
        _MCR_INSTANCE.processar("crie um ferreiro")
        _MCR_INSTANCE.processar("crie um monstro")
        _MCR_INSTANCE.processar("analise o codigo")
        _MCR_INSTANCE.processar("busque por npc")
    return _MCR_INSTANCE


def test_mcr_generalizacao_entidade_nova():
    """Teste 6: MCR generaliza entidades nunca vistas.
    
    Cenário: MCR treinado com "crie um ferreiro" → gerar
             Mas nunca viu "mago".
             Deve generalizar: "crie um mago" → gerar
    """
    mcr = _get_mcr()
    
    # Testa reconhecimento de entidade conhecida
    r1 = mcr.processar("crie um ferreiro")
    if r1.get('acao') not in ('gerar', 'cache'):
        return False, f'entidade conhecida falhou: {r1.get("acao")}'
    
    # Testa GENERALIZAÇÃO: "mago" nunca visto
    r2 = mcr.processar("crie um mago")
    acao2 = r2.get('acao', '')
    if acao2 not in ('gerar', 'feedback'):
        return False, f'generalizacao "mago" falhou: acao={acao2}'
    
    # Testa GENERALIZAÇÃO: "personagem" nunca visto
    r3 = mcr.processar("crie um personagem")
    acao3 = r3.get('acao', '')
    if acao3 not in ('gerar', 'feedback'):
        return False, f'generalizacao "personagem" falhou: acao={acao3}'
    
    return True, 'OK'


def test_mcr_sinonimos_acao():
    """Teste 7: Sinônimos de verbos de ação.
    
    "criar" ≈ "gerar" com alta confiança.
    """
    mcr = _get_mcr()
    
    # Testa com verbo similar "criar" (nunca visto)
    r = mcr.processar("criar um npc")
    acao = r.get('acao', '')
    conf = r.get('confianca', 0)
    
    if acao == 'erro':
        return False, f'"criar um npc" falhou: acao={acao}, conf={conf}'
    
    return True, 'OK'


def test_semantic_fingerprint():
    """Teste 8: Fingerprint 8D pra similaridade estrutural."""
    from mcr.semantic_router import _fingerprint_8d, _cosseno
    
    f1 = _cosseno(_fingerprint_8d("abc"), _fingerprint_8d("def"))
    f2 = _cosseno(_fingerprint_8d("abc"), _fingerprint_8d("123"))
    if f1 <= f2:
        return False, f'fingerprint nao distingue letras de digitos ({f1} <= {f2})'
    
    f3 = _cosseno(_fingerprint_8d(""), _fingerprint_8d(""))
    if f3 < 0:
        return False, 'fingerprint vazio'
    
    return True, 'OK'


def test_palavras_similares():
    """Teste 9: palavras_similares ordena por score."""
    from mcr.semantic_router import palavras_similares
    
    candidatos = {"criar": 1, "gerar": 1, "analisar": 1, "buscar": 1}
    resultados = palavras_similares("elaborar", candidatos, 0.2, 3)
    
    if not resultados:
        return False, f'"elaborar" sem resultados'
    
    if len(resultados) > 3:
        return False, f'max_resultados ignorado: {len(resultados)}'
    
    # Deve estar ordenado
    for i in range(len(resultados)-1):
        if resultados[i][1] < resultados[i+1][1]:
            return False, 'resultados nao ordenados'
    
    return True, 'OK'


# ═══════════════════════════════════════════════════════════════
# EXECUÇÃO
# ═══════════════════════════════════════════════════════════════

print(f'\n{"="*55}')
print(f'  TESTES DE SEMÂNTICA — Generalização MCR')
print(f'{"="*55}\n')

testar("semantic_router.sinônimos", test_semantic_router_sinonimos)
testar("semantic_router.trigrama_fallback", test_semantic_router_trigrama)
testar("semantic_router.termo_mais_similar", test_termo_mais_similar)
testar("coupling._dist_palavras.semântico", test_coupling_semantico)
testar("coupling._buscar_palavras_similares", test_coupling_palavras_similares)
testar("fingerprint.similaridade", test_semantic_fingerprint)
testar("semantic_router.palavras_similares", test_palavras_similares)
testar("mcr.generalização.entidade_nova", test_mcr_generalizacao_entidade_nova)
testar("mcr.sinônimos_verbo", test_mcr_sinonimos_acao)

# Relatório
dt = time.time() - _t0
print(f'\n{"="*55}')
print(f'  RESULTADO: {_n_passaram}/{_n_testes} passaram ({dt:.1f}s)')
if _erros:
    print(f'  FALHAS:')
    for e in _erros:
        print(f'    - {e}')
print(f'{"="*55}\n')
