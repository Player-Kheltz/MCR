#!/usr/bin/env python3
"""MCR Chat — Universal. Orquestra TUDO para QUALQUER pergunta.
Web, arquivos, ferramentas, conhecimento — o MCR decide o que usar.
"""
import sys, os, subprocess, datetime, glob, json, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from MCR import *
from MCR import _EQUACAO_ATUAL

m = MCRMotor()
cmd = MCRComandos(m)
estado_path = os.path.join(os.path.dirname(__file__), 'cache', 'mcr_estado.json')
if os.path.exists(estado_path):
    cmd.carregar_estado()

# ─── FERRAMENTAS DIRETAS ────────────────────────────────────

def _data():
    return f'Hoje e {datetime.date.today().strftime("%d/%m/%Y")}.'
def _hora():
    return f'Agora sao {datetime.datetime.now().strftime("%H:%M:%S")}.'
def _lista_arquivos():
    return 'Arquivos: ' + ', '.join(os.listdir('.')[:20])
def _extrair_termo(p, kw):
    t = p.lower().split()
    for i, w in enumerate(t):
        if w in kw and i + 1 < len(t):
            return ' '.join(t[i+1:]).strip('?.,!')
    return t[-1].strip('?.,!') if t else ''
def _buscar_texto(termo):
    if not termo or len(termo) < 2:
        return 'Buscar o que?'
    for f in glob.glob('**/*', recursive=True)[:30]:
        if os.path.isfile(f):
            try:
                with open(f, 'r', encoding='utf-8', errors='replace') as fp:
                    for i, linha in enumerate(fp.readlines(), 1):
                        if termo.lower() in linha.lower():
                            return f'{f}:{i} {linha.strip()[:200]}'
            except: pass
    return 'Nada encontrado.'

FERAMENTAS = [
    {'nome': 'data', 'desc': 'responder data hoje dia mes ano calendario', 'fn': lambda p: _data()},
    {'nome': 'hora', 'desc': 'responder hora atual minuto segundo relogio', 'fn': lambda p: _hora()},
    {'nome': 'lista_arquivos', 'desc': 'enumerar listar mostrar arquivos pasta diretorio', 'fn': lambda p: _lista_arquivos()},
    {'nome': 'buscar_texto', 'desc': 'encontrar achar localizar palavra texto arquivos', 'fn': lambda p: _buscar_texto(_extrair_termo(p, {'buscar','busque','encontrar','ache','procurar'}))},
]

def _escolher_ferramenta(pergunta):
    """Equacao MCR escolhe a ferramenta — sem if/else."""
    pp = [w.lower().strip('?.,!') for w in pergunta.split()]
    melhor, melhor_score = None, 0
    for f in FERAMENTAS:
        j = MCRByteUtils.jaccard_bytes(pergunta, f['desc'])
        pd = [w.lower() for w in f['desc'].split()]
        exata = any(p1 == p2 for p1 in pp for p2 in pd)
        prefixo = any(len(p1) >= 3 and len(p2) >= 3 and (p1.startswith(p2) or p2.startswith(p1)) for p1 in pp for p2 in pd)
        if not (exata or prefixo):
            continue
        score = j + sum(1 for p1 in pp for p2 in pd if p1 == p2) * 0.2 + sum(1 for p1 in pp for p2 in pd if len(p1)>=3 and len(p2)>=3 and (p1.startswith(p2) or p2.startswith(p1)) and p1 != p2) * 0.15
        if score > melhor_score:
            melhor_score, melhor = score, f
    return melhor if melhor_score > 0.2 else None

# ─── FRAGMENTACAO UNIVERSAL ─────────────────────────────────

def _fragmentar(texto: str):
    """Divide texto em partes por . ! ? , — universal, 0 hardcode."""
    import re
    partes = re.split(r'[,;.!?\n]+(?:\s+|$)', texto)
    return [p.strip() for p in partes if p.strip() and len(p.strip()) > 4]

# ─── ORQUESTRACAO UNIVERSAL ─────────────────────────────────

def _responder_unico(pergunta):
    """Processa UMA pergunta individual com TODAS as fontes."""
    # 1. Ferramenta direta
    ferr = _escolher_ferramenta(pergunta)
    if ferr:
        try:
            return f'MCR [{ferr["nome"]}]: {ferr["fn"](pergunta)}'
        except Exception as e:
            return f'MCR: Erro na ferramenta {ferr["nome"]}: {e}'

    def _resposta_valida(resposta):
        if not resposta or len(resposta) < 30:
            return False
        j = MCRByteUtils.jaccard_bytes(pergunta, resposta)
        if j >= 0.6:
            return False
        h = MCRByteUtils.entropia_bytes(resposta)
        if h < 0.5 or h > 7.5:
            return False
        primeira_linha = resposta.strip().split('\n')[0].strip()
        codigos = ['import ', 'from ', 'def ', 'class ', 'print(', 'testes =', '```', '#!', 'os.', 'sys.']
        if any(primeira_linha.startswith(c) for c in codigos):
            return False
        return True

    # 2. Tenta responder com conhecimento EXISTENTE primeiro
    resposta = cmd._buscar_resposta(pergunta)
    if _resposta_valida(resposta):
        return f'MCR [conhecimento]: {resposta[:500]}'

    # 3. WebLearn (busca na web)
    tentou_web = False
    if MCRByteUtils.entropia_bytes(pergunta) > 2.0:
        w = MCRWebLearn(m)
        nw = w.buscar(pergunta)
        tentou_web = nw > 0

    # 4. Auto-hunt local (busca em arquivos so se necessario)
    termo = pergunta.split()[-1].strip('?.,!')
    if len(termo) > 2 and m.mk_palavra.total < 100:
        cmd._auto_cacar_conhecimento(termo)

    # 5. Tenta responder com NOVO conhecimento
    if tentou_web:
        resposta = cmd._buscar_resposta(pergunta)
        if _resposta_valida(resposta):
            return f'MCR [web]: {resposta[:500]}'

    # 6. Gera por assinatura como ultimo recurso
    resultado = cmd.master(pergunta)
    texto = resultado.get('resposta', str(resultado))
    # Se a resposta e a propria pergunta (eco), tenta expandir com radar
    if texto.strip().lower().startswith(pergunta.lower()[:20]):
        radar = MCRRadar(m)
        varredura = radar.varrer(pergunta, max_pulsos=5)
        if varredura.get('saiu_do_loop'):
            texto = varredura['direcao']
    return f'MCR: {texto[:500]}'

def _responder(pergunta):
    """Orquestra: fragmentos + multiplas ferramentas + cada parte."""
    # 1. Fragmentacao por pontuacao
    fragmentos = _fragmentar(pergunta)
    if len(fragmentos) > 1:
        respostas = []
        for frag in fragmentos:
            r = _responder_unico(frag)
            if ']: ' in r:
                r = r.split(']: ', 1)[1]
            elif r.startswith('MCR: '):
                r = r[5:]
            r = r.strip()
            if len(r) > 10 and not r.lower().startswith(frag.lower()[:15]):
                respostas.append(r)
        if respostas:
            texto = ' | '.join(r[:300] for r in respostas)
            return 'MCR: ' + texto[:800]
        return _responder_unico(fragmentos[0])

    # 2. Multiplas ferramentas na mesma frase
    pp = [w.lower().strip('?.,!') for w in pergunta.split()]
    ferramentas_ativas = []
    for f in FERAMENTAS:
        pd = f['desc'].lower().split()
        if any(p1 == p2 or (len(p1)>=3 and len(p2)>=3 and (p1.startswith(p2) or p2.startswith(p1))) for p1 in pp for p2 in pd):
            ferramentas_ativas.append(f)

    if len(ferramentas_ativas) >= 2:
        respostas = []
        for f in ferramentas_ativas:
            try:
                r = f['fn'](pergunta)
                if r:
                    respostas.append(r)
            except: pass
        if respostas:
            return 'MCR: ' + ' '.join(respostas)[:500]

    return _responder_unico(pergunta)

# ─── CHAT ───────────────────────────────────────────────────

print()
print('= ' * 30)
print('  MCR CHAT — UNIVERSAL')
print('  Web + Arquivos + Ferramentas + Geracao')
print(f'  {len(m.topicos)} conhecimentos, {len(FERAMENTAS)} ferramentas')
print('  "sair" para encerrar.')
print('= ' * 30)
print()

while True:
    try:
        pergunta = input('voce: ').strip()
    except (EOFError, KeyboardInterrupt):
        print(); break
    if not pergunta: continue

    if pergunta.lower() in ('sair', 'exit', 'quit', 'q'):
        cmd.salvar_estado()
        print('MCR: Ate logo!'); break

    resposta = _responder(pergunta)
    try:
        print(resposta)
    except UnicodeEncodeError:
        safe = resposta.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(safe)

    if cmd.total_execucoes % 5 == 0:
        cmd.salvar_estado()

print()
