"""Memoria do Conselho — Memoria persistente INDIVIDUAL com SCORE de qualidade.
Cada arquétipo tem seu proprio arquivo .jsonl com historico de:
- observacoes, padrões, lessons aprendidas, decisoes passadas.
- score: qualidade da contribuicao (0-100), permite aprendizado.

Diretorio: sandbox/.mcr_devia/conselho_memoria/{nome}.jsonl

CICLO DE APRENDIZADO:
1. Membro da perspectiva (score=50 default)
2. Resposta final e gerada
3. Auto-Revisor avalia qualidade da contribuicao de cada membro
4. Score e atualizado na memoria
5. Proxima vez, membro prioriza o que teve alto score
"""
import os, json, time
from modulos.util import safe_ler_linhas, safe_escrever_arquivo, re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MEMORIA_DIR = os.path.join(BASE, 'sandbox', '.mcr_devia', 'conselho_memoria')

MEMBROS = [
    'analista', 'critico', 'estrategista', 'arquiteto',
    'contador_historias', 'psicologo', 'revisor_codigo', 'tecnico',
    'especialista'
]

def _init_membro(nome):
    os.makedirs(MEMORIA_DIR, exist_ok=True)
    path = os.path.join(MEMORIA_DIR, f'{nome}.jsonl')
    if not os.path.exists(path):
        safe_escrever_arquivo(path, '')
    return path

def carregar(nome, max_entradas=20):
    """Carrega as ultimas N entradas da memoria de um membro.
    Retorna lista de dicts com {ts, tarefa, observacao, padrao, categoria, score}"""
    path = _init_membro(nome)
    entradas = []
    try:
        for linha in safe_ler_linhas(path):
                linha = linha.strip()
                if linha:
                    try:
                        entradas.append(json.loads(linha))
                    except Exception:
                        pass
    except Exception:
        pass
    return entradas[-max_entradas:]

def salvar(nome, tarefa, observacao, padrao="", categoria="geral", score=50):
    """Salva uma nova entrada na memoria do membro, com score de qualidade."""
    path = _init_membro(nome)
    entrada = {
        "ts": time.time(),
        "tarefa": tarefa,
        "observacao": observacao,
        "padrao": padrao,
        "categoria": categoria,
        "score": min(100, max(0, score)),  # 0-100
    }
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + '\n')
        return True
    except Exception:
        return False

def avaliar(nome, tarefa, score, justificativa=""):
    """Atualiza o score da ULTIMA entrada de um membro (feedback loop).
    Chamado apos a resposta final ser avaliada."""
    path = _init_membro(nome)
    try:
        entradas = [json.loads(l) for l in safe_ler_linhas(path) if l.strip()]
        if entradas:
            entradas[-1]['score'] = min(100, max(0, score))
            entradas[-1]['feedback'] = justificativa
            with open(path, 'w', encoding='utf-8') as f:
                for e in entradas:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')
        return True
    except Exception:
        pass
    return False

def carregar_melhores(nome, max_entradas=5, score_minimo=60):
    """Carrega as entradas de MAIOR score de um membro.
    Prioriza aprendizado de qualidade sobre quantidade."""
    entradas = carregar(nome, 100)
    # Filtra por score minimo
    boas = [e for e in entradas if e.get('score', 50) >= score_minimo]
    if not boas:
        boas = entradas[-max_entradas:]  # fallback: ultimas
    # Ordena por score (melhores primeiro)
    boas.sort(key=lambda e: -e.get('score', 50))
    return boas

def resumo_para_prompt(nome, max_entradas=5):
    """Gera resumo priorizando memorias de ALTO SCORE.
    O membro 'aprende' com o que funcionou antes."""
    entradas = carregar_melhores(nome, max_entradas)
    if not entradas:
        return f"[{nome.upper()}] Sem memorias anteriores."
    
    linhas = [f"[MEMORIA DO {nome.upper()}]"]
    for e in entradas:
        score = e.get('score', 50)
        obs = e.get('observacao', '')
        padrao = e.get('padrao', '')
        cat = e.get('categoria', '')
        linha = f"- (score:{score}) {obs}"
        if padrao:
            linha += f" | {padrao}"
        if cat:
            linha += f" [{cat}]"
        linhas.append(linha)
    return '\n'.join(linhas)

def estatisticas():
    stats = {}
    for nome in MEMBROS:
        entradas = carregar(nome, 999999)
        stats[nome] = {
            "total": len(entradas),
            "score_medio": round(sum(e.get('score', 50) for e in entradas) / max(1, len(entradas)), 1),
            "categorias": list(set(e.get('categoria', '') for e in entradas if e.get('categoria'))),
        }
    return stats

if __name__ == "__main__":
    # Teste
    salvar("analista", "teste", "Bug de path relativo em cmd_fix_excepts.py", "os.path.dirname", "bugfix")
    salvar("critico", "teste", "Risco de seguranca: URL sem validacao", "ssrf", "seguranca")
    print("Memorias salvas!")
    print(json.dumps(estatisticas(), ensure_ascii=False, indent=2))
