"""Modulo: Memoria - Fragmentada por data, compactada automaticamente."""
import os, json, time, gzip
from datetime import datetime, timedelta

SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox'))
MEMORIA_DIR = os.path.join(SANDBOX, '.mcr_devia', 'memoria')
MAX_ENTRIES_POR_DIA = 50000
_MAX_DIAS_SEM_COMPRESSAO = 7
_MAX_DIAS_COMPACTADOS = 30
_SESSAO_ID = None

def init_module(contexto):
    global _SESSAO_ID
    _SESSAO_ID = str(int(time.time()))
    mem = Memoria()
    mem._limpar_antigos()  # Compacta/prune na carga
    contexto['memoria'] = mem
    kernel = contexto.get('kernel')
    if kernel:
        kernel.events.on('pos_exec', mem._hook_pos_exec)
    return 'memoria', mem


class Memoria:
    """Memoria fragmentada por data. Cada dia = um arquivo."""
    
    def __init__(self):
        os.makedirs(MEMORIA_DIR, exist_ok=True)
        self._cache = {}
        self._carregar_hoje()
    
    def _arquivo_hoje(self):
        return os.path.join(MEMORIA_DIR, f'{datetime.now().strftime("%Y-%m-%d")}.jsonl')
    
    def _arquivo_por_data(self, data_str):
        return os.path.join(MEMORIA_DIR, f'{data_str}.jsonl')
    
    def _carregar_hoje(self):
        """Carrega entradas de hoje para cache."""
        fpath = self._arquivo_hoje()
        self._cache = {'arquivo': fpath, 'entradas': []}
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try: self._cache['entradas'].append(json.loads(line))
                            except Exception: pass
            except Exception: pass
        return len(self._cache['entradas'])
    
    def registrar(self, cmd, args=None, resultado=None, erro=None):
        """Registra uma interacao no arquivo de hoje."""
        entrada = {
            "ts": datetime.now().isoformat(),
            "ts_unix": time.time(),
            "sessao": _SESSAO_ID,
            "cmd": cmd,
            "args": (args or []),
            "resultado": resultado,
            "erro": str(erro) if erro else None,
        }
        
        # Append no arquivo do dia
        fpath = self._arquivo_hoje()
        try:
            with open(fpath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entrada, ensure_ascii=False) + '\n')
        except Exception: pass
        
        # Cache
        if self._cache.get('arquivo') == fpath:
            self._cache['entradas'].append(entrada)
            # Prune se necessario
            if len(self._cache['entradas']) > MAX_ENTRIES_POR_DIA:
                self._cache['entradas'] = self._cache['entradas'][-MAX_ENTRIES_POR_DIA:]
        else:
            self._carregar_hoje()
        
        return entrada
    
    def _hook_pos_exec(self, **kw):
        self.registrar(
            cmd=kw.get('cmd', '?'),
            args=kw.get('args'),
            resultado=kw.get('resultado'),
            erro=kw.get('erro'),
        )
    
    def consultar(self, cmd=None, limite=10, desde=None, ate=None, dias=7):
        """Consulta historico nos ultimos N dias."""
        resultados = []
        data_atual = datetime.now()
        
        for i in range(dias):
            data_str = (data_atual - timedelta(days=i)).strftime('%Y-%m-%d')
            entradas = self._ler_arquivo(data_str)
            resultados = entradas + resultados
        
        if cmd:
            resultados = [e for e in resultados if e.get('cmd') == cmd]
        if desde:
            resultados = [e for e in resultados if e.get('ts', '') >= desde]
        if ate:
            resultados = [e for e in resultados if e.get('ts', '') <= ate]
        
        return resultados[-limite:]
    
    def _ler_arquivo(self, data_str):
        """Le arquivo .jsonl ou .jsonl.gz de uma data."""
        # Tenta .jsonl primeiro
        fpath = self._arquivo_por_data(data_str)
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    return [json.loads(line) for line in f if line.strip()]
            except Exception: pass
        
        # Tenta .jsonl.gz
        fpath_gz = fpath + '.gz'
        if os.path.exists(fpath_gz):
            try:
                with gzip.open(fpath_gz, 'rt', encoding='utf-8') as f:
                    return [json.loads(line) for line in f if line.strip()]
            except Exception: pass
        
        return []
    
    def _limpar_antigos(self):
        """Compacta dias antigos. NUNCA deleta. Memoria infinita."""
        hoje = datetime.now()
        for f in os.listdir(MEMORIA_DIR):
            if not f.endswith(".jsonl") and not f.endswith(".jsonl.gz"):
                continue
            fpath = os.path.join(MEMORIA_DIR, f)
            data_str = f.split(".")[0]
            try:
                data = datetime.strptime(data_str, "%Y-%m-%d")
            except Exception as e:
                print(f"[Fix] ERRO: {e}")
            dias_atras = (hoje - data).days
            # So compacta se mais de 7 dias. NUNCA deleta.
            if dias_atras > 7 and f.endswith(".jsonl"):
                try:
                    with open(fpath, "r", encoding="utf-8") as f_in:
                        with gzip.open(fpath + ".gz", "wt", encoding="utf-8") as f_out:
                            f_out.write(f_in.read())
                    os.remove(fpath)
                except Exception: pass
    def estatisticas(self, dias=30):
        """Estatisticas dos ultimos N dias."""
        entradas = self.consultar(limite=999999, dias=dias)
        if not entradas:
            return {"total": 0, "dias": dias}
        
        cmds = {}
        for e in entradas:
            c = e.get('cmd', '?')
            cmds[c] = cmds.get(c, 0) + 1
        
        sessoes = len(set(e.get('sessao', '') for e in entradas))
        arquivos = len([f for f in os.listdir(MEMORIA_DIR) if f.endswith(('.jsonl', '.jsonl.gz'))])
        tamanho = sum(os.path.getsize(os.path.join(MEMORIA_DIR, f)) for f in os.listdir(MEMORIA_DIR) if f.endswith(('.jsonl', '.jsonl.gz')))
        
        return {
            "total": len(entradas),
            "comandos_distintos": len(cmds),
            "cmd_mais_usado": max(cmds, key=cmds.get) if cmds else '?',
            "sessoes": sessoes,
            "arquivos": arquivos,
            "tamanho_kb": tamanho // 1024,
            "dias_consultados": dias,
            "ultimo_registro": entradas[-1].get('ts', '?') if entradas else '?',
        }
