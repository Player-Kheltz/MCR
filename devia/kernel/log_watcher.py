"""log_watcher.py — Monitora logs do Canary e invoca MCR-DevIA em erros.

Fluxo:
1. Watchdog detecta mudanca nos arquivos .log do servidor
2. Le as novas linhas
3. Se detectar padrao de erro (Lua, crash, exception):
   a. Extrai contexto: arquivo, linha, mensagem
   b. Invoca o DevIA via processar() para diagnosticar
   c. Salva diagnostico em cache/analises/
4. Notifica o usuario (terminal ou arquivo)
"""
import os, re, time, json
from datetime import datetime

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "analises")
os.makedirs(CACHE_DIR, exist_ok=True)

# Arquivo de checkpoint: salva a posicao de leitura dos logs para nao reprocessar historico
_POS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "log_positions.json")

def _salvar_posicoes(posicoes):
    try:
        os.makedirs(os.path.dirname(_POS_PATH), exist_ok=True)
        with open(_POS_PATH, 'w', encoding='utf-8') as f:
            json.dump(posicoes, f)
    except: pass

def _carregar_posicoes():
    try:
        if os.path.exists(_POS_PATH):
            with open(_POS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return {}

# Padroes de erro do Canary
PADROES_ERRO = [
    (r'\[error\].*', 'ERRO_GERAL'),
    (r'luaCallFunction.*attempt to index.*nil', 'ERRO_LUA_NIL'),
    (r'\[.*Lua Error.*\]', 'ERRO_LUA'),
    (r'\[crash\]', 'CRASH'),
    (r'Segmentation fault', 'CRASH_SEGV'),
    (r'FATAL:', 'ERRO_FATAL'),
    (r'Exception:', 'EXCEPTION_CPP'),
    (r'std::exception', 'EXCEPTION_STD'),
    (r'out of memory', 'ERRO_MEMORIA'),
    (r'stack overflow', 'ERRO_STACK'),
    (r'Access violation', 'ERRO_ACCESS_VIOLATION'),
]

# Diretorios de log
DIRS_LOG = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "server", "log"),
]


def detectar_erro(linha):
    """Detecta se uma linha de log contem erro."""
    for padrao, tipo in PADROES_ERRO:
        if re.search(padrao, linha, re.IGNORECASE):
            return tipo
    return None


def extrair_contexto(linha, arquivo_log, linhas_anteriores=5):
    """Extrai contexto do erro: arquivo, linha, mensagem."""
    contexto = {
        'timestamp': datetime.now().isoformat(),
        'log_file': arquivo_log,
        'linha_erro': linha.strip(),
        'contexto_anterior': '',
        'arquivo_origem': None,
        'linha_origem': None,
        'tipo': None,
    }
    
    # Tenta extrair arquivo Lua do erro ('data/scripts/X.lua:42')
    match = re.search(r'([\w/\\-]+\.lua):(\d+)', linha)
    if match:
        contexto['arquivo_origem'] = match.group(1)
        contexto['linha_origem'] = int(match.group(2))
    
    # Tenta extrair arquivo C++ do erro ('src/X.cpp:42')
    match = re.search(r'([\w/\\-]+\.cpp):(\d+)', linha)
    if match and not contexto['arquivo_origem']:
        contexto['arquivo_origem'] = match.group(1)
        contexto['linha_origem'] = int(match.group(2))
    
    return contexto


def analisar_erro(contexto, processar_func=None):
    """Invoca o DevIA para analisar o erro."""
    if not processar_func:
        return {'analise': 'MCR-DevIA nao disponivel', 'correcao': None}
    
    prompt = (
        f"analise e corrija este erro do canary:\n"
        f"ERRO: {contexto.get('linha_erro', '?')}\n"
        f"ARQUIVO ORIGEM: {contexto.get('arquivo_origem', '?')}\n"
    )
    
    resultado = processar_func(prompt)
    print(f"\n{'='*60}")
    print(f"  [LOGWATCH ANALISE] Erro detectado automaticamente")
    print(f"  Erro: {contexto.get('linha_erro', '?')[:100]}")
    resp = resultado.get('resposta', str(resultado))[:400]
    print(f"  Analise: {resp}")
    print(f"{'='*60}\n")
    return resultado


def salvar_analise(contexto, resultado):
    """Salva analise em disco."""
    nome = f"erro_{int(time.time())}.json"
    caminho = os.path.join(CACHE_DIR, nome)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump({
            'contexto': contexto,
            'resultado': str(resultado)[:2000],
        }, f, ensure_ascii=False, indent=2)
    return caminho


class LogWatcher:
    """Monitora logs do Canary em tempo real."""
    
    def __init__(self, processar_func=None):
        self.processar_func = processar_func
        self._ultimos_tamanhos = _carregar_posicoes()
        self._erros_detectados = 0
        self._analises_feitas = 0
    
    def verificar_logs(self):
        """Verifica se ha novos erros nos logs."""
        resultados = []
        
        for dir_log in DIRS_LOG:
            if not os.path.isdir(dir_log):
                continue
            
            for f in os.listdir(dir_log):
                if not f.endswith('.log') and not f.endswith('.txt'):
                    continue
                caminho = os.path.join(dir_log, f)
                try:
                    stat = os.stat(caminho)
                    tamanho = stat.st_size
                except:
                    continue
                
                ultimo_tam = self._ultimos_tamanhos.get(caminho, 0)
                if tamanho <= ultimo_tam:
                    continue
                
                self._ultimos_tamanhos[caminho] = tamanho
                _salvar_posicoes(self._ultimos_tamanhos)
                
                # Le linhas novas
                try:
                    with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
                        fh.seek(ultimo_tam)
                        novas_linhas = fh.readlines()
                except:
                    continue
                
                for linha in novas_linhas:
                    tipo = detectar_erro(linha)
                    if tipo:
                        ctx = extrair_contexto(linha, caminho)
                        ctx['tipo'] = tipo
                        resultados.append(ctx)
                        self._erros_detectados += 1
                        
                        if self.processar_func:
                            analise = analisar_erro(ctx, self.processar_func)
                            caminho_analise = salvar_analise(ctx, analise)
                            self._analises_feitas += 1
                            ctx['analise_salva_em'] = caminho_analise
        
        return resultados
    
    def stats(self):
        return {
            'erros_detectados': self._erros_detectados,
            'analises_feitas': self._analises_feitas,
            'diretorios_monitorados': DIRS_LOG,
        }
