#!/usr/bin/env python3
"""SCAN DE SEGURANCA MCR — Varre TUDO em busca de dados sensiveis.
Usa MCR concepts + regex. Nao publicar ate scan estar LIMPO."""
import os, sys, re, subprocess, json, time as _time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

T0 = _time.time()
def log(msg):
    print(f'[{_time.time()-T0:.1f}s] {msg}', flush=True)

# ============================================================
# PADROES DE SEGURANCA
# ============================================================

SENSITIVE_PATTERNS = [
    # Senhas e tokens genericos
    (r'(?i)(?:senha|password|passwd|pwd|secret)\s*[=:]\s*["\']?[A-Za-z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{8,}', 'SENHA/TOKEN'),
    (r'(?i)(?:token|api_key|apikey|acess_token|refresh_token)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', 'TOKEN_API'),
    (r'(?:ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{36}', 'GITHUB_TOKEN'),
    (r'-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----', 'CHAVE_PRIVADA'),
    (r'(?i)(?:connection_string|conn_str|conn_string)\s*[=:]\s*.+', 'CONNECTION_STRING'),
    (r'(?i)mongodb(?:\+srv)?:\/\/[^\s]+', 'MONGODB_URI'),
    (r'postgresql:\/\/[^\s]+', 'POSTGRES_URI'),
    (r'mysql:\/\/[^\s]+', 'MYSQL_URI'),
    (r'redis:\/\/[^\s]+', 'REDIS_URI'),
    (r'sqlite:\/\/[^\s]+', 'SQLITE_URI'),
    
    # Dados pessoais
    (r'(?i)(?:cpf|cnpj)\s*[=:]\s*["\']?\d{3}\.\d{3}\.\d{3}-\d{2}', 'CPF'),
    (r'(?i)(?:rg|identidade)\s*[=:]\s*["\']?\d{1,2}\.?\d{3}\.?\d{3}-?\w', 'RG'),
    (r'(?i)(?:telefone|celular|phone|whatsapp)\s*[=:]\s*["\']?\(?\d{2,3}\)?\s?\d{4,5}-?\d{4}', 'TELEFONE'),
    (r'(?:cartao|cartão|card_number|cc_num)\s*[=:]\s*["\']?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}', 'CARTAO'),
    
    # Caminhos locais
    (r'[A-Za-z]:\\[A-Za-z0-9_\-\\]+', 'CAMINHO_LOCAL'),
    (r'/mnt/[A-Za-z0-9_\-/]+', 'CAMINHO_LINUX'),
    
    # Ambiente
    (r'\$\{?[A-Z_]+_TOKEN\}?', 'VAR_AMBIENTE_TOKEN'),
    (r'\$\{?[A-Z_]+_PASSWORD\}?', 'VAR_AMBIENTE_SENHA'),
    (r'\$\{?[A-Z_]+_SECRET\}?', 'VAR_AMBIENTE_SECRET'),
    (r'\$\{?[A-Z_]+_KEY\}?', 'VAR_AMBIENTE_KEY'),
    
    # IPs internos
    (r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b', 'IP_INTERNO'),
]

# ============================================================
# SCAN POR FINGERPRINT MCR (entropia anomala)
# ============================================================

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from MCR_AGI import MCRByteUtils
    HAS_MCR = True
except:
    HAS_MCR = False
    log('MCR_AGI nao encontrado, scan usando regex apenas')

def entropia_anomala(conteudo: str) -> float:
    """Retorna entropia do conteudo. Quanto mais alta,
    menos provavel de ser codigo normal."""
    if not HAS_MCR or not conteudo:
        return 0.0
    return MCRByteUtils.entropia_bytes(conteudo.encode('utf-8')[:2000])

# ============================================================
# SCANNER
# ============================================================

class ScannerMCR:
    def __init__(self):
        self.resultados = []  # [{tipo, arquivo, linha, padrao, conteudo}]
        self.alertas_entropia = []
    
    def scan_arquivo(self, caminho: str):
        """Escaneia UM arquivo por dados sensiveis."""
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                linhas = f.readlines()
        except:
            try:
                with open(caminho, 'rb') as f:
                    dados = f.read(5000)
                # Arquivo binario — verifica entropia
                if HAS_MCR:
                    ent = MCRByteUtils.entropia_bytes(dados)
                    if ent > 7.0:
                        self.alertas_entropia.append({
                            'arquivo': caminho,
                            'entropia': round(ent, 2),
                            'tamanho': len(dados),
                            'tipo': 'BINARIO_ENTROPIA_ALTA'
                        })
                return
            except:
                return
        
        for i, linha in enumerate(linhas, 1):
            for pattern, tipo in SENSITIVE_PATTERNS:
                if re.search(pattern, linha):
                    # Filtra falsos positivos comuns
                    if self._falso_positivo(linha, tipo):
                        continue
                    self.resultados.append({
                        'tipo': tipo,
                        'arquivo': caminho,
                        'linha': i,
                        'conteudo': linha.strip()[:120],
                    })
                    break  # So o primeiro match por linha
    
    def _falso_positivo(self, linha: str, tipo: str) -> bool:
        """Filtra falsos positivos OBVIOS."""
        linha_lower = linha.lower()
        
        # Se a linha contem "exemplo" ou "placeholder", e provavelmente nao real
        if any(w in linha_lower for w in ['exemplo', 'placeholder', 'your_token', 'your_password',
                                           'seu_token', 'sua_senha', 'example', 'changeme']):
            return True
        
        # Se o "token" e muito curto (< 10 chars), provavelmente nao e real
        for match in re.finditer(r'["\'][A-Za-z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{4,20}["\']', linha):
            if len(match.group()) < 10:
                return True
        
        return False
    
    def scan_repositorio(self, repo_path: str, nome: str):
        """Escaneia UM repositorio Git (working tree + historico)."""
        log(f'Scan: {nome}')
        repo_path = os.path.abspath(repo_path)
        if not os.path.exists(os.path.join(repo_path, '.git')):
            log(f'  {repo_path} nao e um repositorio Git')
            return
        
        # 1. Working tree
        log(f'  [1/3] Working tree...')
        for root, dirs, files in os.walk(repo_path):
            # Pula .git e __pycache__
            if '.git' in dirs: dirs.remove('.git')
            if '__pycache__' in dirs: dirs.remove('__pycache__')
            if 'node_modules' in dirs: dirs.remove('node_modules')
            if 'vcpkg' in dirs: dirs.remove('vcpkg')
            
            for fname in files:
                fpath = os.path.join(root, fname)
                self.scan_arquivo(fpath)
        
        # 2. Git history (cada commit)
        log(f'  [2/3] Git history...')
        try:
            result = subprocess.run(
                ['git', '-C', repo_path, 'log', '--all', '--format=%H', '--reverse'],
                capture_output=True, text=True, timeout=60
            )
            hashes = [h.strip() for h in result.stdout.split('\n') if h.strip()]
            log(f'  {len(hashes)} commits para escanear')
            
            for i, h in enumerate(hashes):
                try:
                    # Mostra arquivos do commit
                    show_r = subprocess.run(
                        ['git', '-C', repo_path, 'show', '--format=', '--name-only', h],
                        capture_output=True, text=True, timeout=10
                    )
                    arquivos_commit = [a for a in show_r.stdout.split('\n') if a.strip()]
                    
                    for arq in arquivos_commit:
                        if not arq.strip():
                            continue
                        try:
                            content_r = subprocess.run(
                                ['git', '-C', repo_path, 'show', f'{h}:{arq}'],
                                capture_output=True, text=True, timeout=10
                            )
                            if content_r.returncode == 0:
                                for j, linha in enumerate(content_r.stdout.split('\n'), 1):
                                    for pattern, tipo in SENSITIVE_PATTERNS:
                                        if re.search(pattern, linha):
                                            self.resultados.append({
                                                'tipo': tipo,
                                                'arquivo': f'[COMMIT {h[:8]}] {arq}',
                                                'linha': j,
                                                'conteudo': linha.strip()[:120],
                                            })
                                            break
                        except:
                            pass
                except:
                    pass
                    
                if (i+1) % 50 == 0:
                    log(f'    {i+1}/{len(hashes)} commits escaneados...')
        except Exception as e:
            log(f'  Erro no git history: {e}')
        
        # 3. Entropia alta (MCR)
        log(f'  [3/3] Entropia (MCR)...')
        for alerta in self.alertas_entropia:
            log(f'    Entropia alta: {alerta["arquivo"]} ({alerta["entropia"]})')
    
    def relatorio(self):
        """Gera relatorio final."""
        print()
        print('=' * 70)
        print('RELATORIO DE SEGURANCA')
        print('=' * 70)
        
        if not self.resultados:
            print('\n✅ NENHUM DADO SENSIVEL ENCONTRADO')
        else:
            print(f'\n⚠️  {len(self.resultados)} ALERTAS ENCONTRADOS:')
            print()
            
            # Agrupa por tipo
            por_tipo = {}
            for r in self.resultados:
                por_tipo.setdefault(r['tipo'], []).append(r)
            
            for tipo, items in sorted(por_tipo.items()):
                print(f'  [{tipo}] {len(items)} ocorrencia(s):')
                for item in items[:5]:  # Mostra so 5 por tipo
                    print(f'    {item["arquivo"]}:{item["linha"]}')
                    print(f'      {item["conteudo"][:100]}')
                if len(items) > 5:
                    print(f'    ... e mais {len(items)-5}')
                print()
        
        if self.alertas_entropia:
            print(f'\n⚠️  {len(self.alertas_entropia)} ALERTAS DE ENTROPIA (MCR):')
            for a in self.alertas_entropia[:5]:
                print(f'  {a["arquivo"]}: entropia={a["entropia"]}')
        
        print(f'\nTotal: {len(self.resultados)} alertas, {len(self.alertas_entropia)} alertas de entropia')
        print('=' * 70)


if __name__ == '__main__':
    scanner = ScannerMCR()
    
    # Escaneia ambos os repositorios
    for path, nome in [
        (r'E:\Projeto MCR', 'ProjetoMCR'),
        (r'E:\MCR', 'MCR'),
    ]:
        if os.path.exists(path):
            scanner.scan_repositorio(path, nome)
        else:
            log(f'{nome}: caminho nao encontrado ({path})')
    
    scanner.relatorio()
