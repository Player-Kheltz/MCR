#!/usr/bin/env python3
"""persistence.py — Document index, fragmentation, segmentation, and persistence.

Indexação de documentos (MCRDocIndex), fragmentação de tarefas,
segmentação do próprio código, e persistência de estado.
"""
import os, re, json, time as _time
from typing import Dict, List

from .engine import MCR


class MCRDocIndex:
    """Cache de documentos para consulta rapida por termo."""
    
    def __init__(self):
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._cache_path = os.path.join(self._base, 'sandbox', '.mcr_docs_index.json')
        self._indice = {}
        self._carregado = False
        self.mk = MCR("doc_index")
    
    def _carregar(self):
        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path, 'r', encoding='utf-8') as f:
                    self._indice = json.load(f)
                self._carregado = True
                self.mk.aprender("INDEX", f"CARREGADO:{len(self._indice)}")
                return
            except Exception: pass
        self._carregado = False
    
    def _salvar(self):
        try:
            os.makedirs(os.path.dirname(self._cache_path), exist_ok=True)
            with open(self._cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._indice, f, ensure_ascii=False, indent=2)
        except Exception: pass
    
    def indexar(self, forcar=False) -> int:
        if self._carregado and not forcar:
            return len(self._indice)
        self._carregar()
        if self._carregado and not forcar:
            return len(self._indice)
        docs_dir = os.path.join(self._base, 'docs')
        if not os.path.isdir(docs_dir): return 0
        n = 0
        for root, dirs, files in os.walk(docs_dir):
            for fname in files:
                if not (fname.endswith('.md') or fname.endswith('.txt')): continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read(2000)
                    termos = set()
                    for palavra in conteudo.lower().split():
                        palavra = palavra.strip('.,;:!?()[]{}""\'')
                        if len(palavra) >= 4:
                            termos.add(palavra)
                    relpath = os.path.relpath(fpath, self._base)
                    self._indice[relpath] = {
                        'termos': list(termos),
                        'tamanho': len(conteudo),
                        'n_termos': len(termos),
                    }
                    n += 1
                except Exception: pass
        self._salvar()
        self._carregado = True
        self.mk.aprender("INDEX", f"CRIADO:{n}")
        return n
    
    def buscar(self, termo: str) -> list:
        if not self._carregado:
            self._carregar()
            if not self._carregado:
                self.indexar()
        termo = termo.lower()
        resultados = []
        for caminho, dados in self._indice.items():
            if termo in dados.get('termos', []):
                resultados.append({
                    'caminho': caminho,
                    'tamanho': dados.get('tamanho', 0),
                    'relevancia': dados.get('n_termos', 0),
                })
        resultados.sort(key=lambda x: -x['relevancia'])
        return resultados
    
    def ler(self, caminho_rel: str, max_bytes=500) -> str:
        fpath = os.path.join(self._base, caminho_rel)
        if not os.path.exists(fpath): return ''
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_bytes)
        except Exception: return ''


_MCR_DOC_INDEX = None


def _get_doc_index():
    global _MCR_DOC_INDEX
    if _MCR_DOC_INDEX is None:
        _MCR_DOC_INDEX = MCRDocIndex()
    return _MCR_DOC_INDEX


class MCRFragmento:
    """UMA parte de um ciclo que o MCR decide executar."""
    def __init__(self, nome, funcao, args=None):
        self.nome = nome
        self.funcao = funcao
        self.args = args or {}
        self.resultado = None
        self.tempo = 0.0
    
    def executar(self):
        import time
        t0 = time.time()
        try: self.resultado = self.funcao(**self.args)
        except Exception as e: self.resultado = str(e)[:50]
        self.tempo = time.time() - t0


class MCRFragmentador:
    """Agrupa fragmentos e executa em ordem MCR."""
    def __init__(self):
        self.fragmentos = []
    def adicionar(self, nome, funcao, args=None):
        self.fragmentos.append(MCRFragmento(nome, funcao, args))
    def executar_todos(self) -> list:
        resultados = []
        for f in self.fragmentos:
            f.executar()
            resultados.append(f.resultado)
        return resultados


class MCRSegmentador:
    """Aprende a segmentar o proprio MCR.py em secoes."""
    
    def __init__(self):
        self.mk_tipos = MCR("segmentador_tipos")
        self.mk_transicoes = MCR("segmentador_trans")
        self._tipos_aprendidos = set()
        self._linhas_info = None
    
    def _classificar_linha(self, linha: str) -> str:
        if not linha or not linha.strip():
            return 'BLANK'
        stripped = linha.strip()
        tem_indent = len(linha) > 0 and linha[0] in (' ', '\t')
        if stripped.startswith('#'):
            return 'COMMENT'
        if stripped.startswith(('def ', 'class ', 'import ', 'from ', 'if ', 'elif ',
                                 'else:', 'for ', 'while ', 'try:', 'except', 'return ',
                                 '@', 'with ', 'print(', 'assert ', 'raise ',
                                 'self.', 'return', 'break', 'continue', 'pass')):
            return 'CODE'
        if tem_indent and len(stripped) > 5:
            return 'CODE'
        if not tem_indent and (stripped.startswith('{') or stripped.startswith('[')):
            return 'DATA'
        if not tem_indent and stripped.startswith('"') and stripped.endswith('"'):
            return 'DATA'
        if not tem_indent and stripped and stripped[0].isalpha():
            return 'CODE'
        from .signature import MCRSignature
        sig = MCRSignature.extrair(linha)
        ent = sig.get('entropia', 0)
        if ent > 5.0:
            return 'CODE'
        elif ent < 1.0:
            return 'BLANK'
        else:
            return 'OTHER'
    
    def estudar_se(self, caminho: str):
        if not os.path.exists(caminho):
            return None
        linhas_info = []
        ultimo_tipo = None
        with open(caminho, 'r', encoding='utf-8') as f:
            for num, linha in enumerate(f, 1):
                tipo = self._classificar_linha(linha)
                linhas_info.append((tipo, num, linha.rstrip('\n')))
                if ultimo_tipo and ultimo_tipo != tipo:
                    self.mk_transicoes.aprender(ultimo_tipo, tipo)
                ultimo_tipo = tipo
        self._linhas_info = linhas_info
        return linhas_info
    
    def encontrar_dados(self) -> list:
        if not self._linhas_info:
            return []
        blocos = []
        em_data = False
        inicio_bloco = 0
        for tipo, num, conteudo in self._linhas_info:
            if tipo == 'DATA' and not em_data:
                em_data = True
                inicio_bloco = num
            elif tipo != 'DATA' and em_data:
                em_data = False
                if num - inicio_bloco >= 5:
                    blocos.append((inicio_bloco, num - 1))
        if em_data:
            ultimo_num = self._linhas_info[-1][1]
            if ultimo_num - inicio_bloco >= 5:
                blocos.append((inicio_bloco, ultimo_num))
        return blocos


class MCRPersistencia:
    """Gerencia salvamento dos dados no proprio MCR.py."""
    
    def __init__(self, caminho_mcr_py=None):
        self._caminho = caminho_mcr_py or os.path.abspath(__file__)
        self.segmentador = MCRSegmentador()
        self.dados = {}
        self._mudancas_pendentes = 0
        self._ultimo_salvamento = 0
        from .decisor import MCRDecisor, MCRThreshold
        self.decisor = MCRDecisor('persistencia')
        self.thr_salvar = MCRThreshold('salvamento')
    
    def carregar_dados(self) -> dict:
        linhas_info = self.segmentador.estudar_se(self._caminho)
        if not linhas_info:
            return {}
        dados_linhas = []
        em_dados = False
        for tipo, num, conteudo in linhas_info:
            if tipo == 'DATA' and not em_dados:
                em_dados = True
            if em_dados and tipo == 'DATA':
                dados_linhas.append(conteudo)
            elif em_dados and tipo in ('BLANK', 'CODE', 'COMMENT'):
                if len(dados_linhas) > 10:
                    break
                em_dados = False
        if not dados_linhas:
            return {}
        dados = {'licoes': [], 'assinaturas': {}, 'cache': {}, 'estado': {}}
        for linha in dados_linhas:
            try:
                obj = json.loads(linha.strip())
                if isinstance(obj, dict):
                    if 'erro' in obj and 'solucao' in obj:
                        dados['licoes'].append(obj)
                    elif 'autor' in obj:
                        autor = obj['autor']
                        dados['assinaturas'].setdefault(autor, []).append(obj)
                    elif 'cache_key' in obj:
                        dados['cache'][obj['cache_key']] = obj['valor']
                    elif 'estado_key' in obj:
                        dados['estado'][obj['estado_key']] = obj['valor']
            except (json.JSONDecodeError, ValueError):
                pass
        self.dados = dados
        self._ultimo_salvamento = _time.time()
        return dados
    
    def marcar_mudanca(self):
        self._mudancas_pendentes += 1
        self.thr_salvar.observar(self._mudancas_pendentes)
    
    def salvar_se_precisar(self, estado_extra: str = '') -> bool:
        agora = _time.time()
        tempo_desde = agora - self._ultimo_salvamento
        estado = (
            f"mud:{self._mudancas_pendentes}_"
            f"tempo:{int(tempo_desde)}_"
            f"dados:{len(self.dados.get('licoes', []))}_"
            f"{estado_extra}"
        )
        acao = self.decisor.decidir(estado)
        if 'pular' in str(acao).lower() or self._mudancas_pendentes == 0:
            return False
        sucesso = self._salvar_agora()
        if sucesso:
            self._mudancas_pendentes = 0
            self._ultimo_salvamento = agora
            self.thr_salvar.aprender('salvou', self._mudancas_pendentes)
        return sucesso
    
    def _salvar_agora(self) -> bool:
        try:
            linhas_data = []
            for l in self.dados.get('licoes', []):
                linhas_data.append(json.dumps(l, ensure_ascii=False))
            for autor, ass_list in self.dados.get('assinaturas', {}).items():
                for a in ass_list:
                    a_copy = dict(a)
                    a_copy['autor'] = autor
                    linhas_data.append(json.dumps(a_copy, ensure_ascii=False))
            for k, v in self.dados.get('cache', {}).items():
                try: linhas_data.append(json.dumps({'cache_key': k, 'valor': v}, ensure_ascii=False))
                except Exception: pass
            for k, v in self.dados.get('estado', {}).items():
                try: linhas_data.append(json.dumps({'estado_key': k, 'valor': v}, ensure_ascii=False))
                except Exception: pass
            if not linhas_data:
                return True
            data_str = '\n'.join(linhas_data)
            data_block = f'\n_MCR_DATA = """\n{data_str}\n"""\n'
            with open(self._caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            import re as _re
            conteudo = _re.sub(r'\n_MCR_DATA\s*=\s*""".*?"""\s*\n', '\n', conteudo, flags=_re.DOTALL)
            linhas = conteudo.split('\n')
            while linhas and (linhas[-1].strip().startswith('{') or linhas[-1].strip() == ''):
                linhas.pop()
            conteudo = '\n'.join(linhas)
            marcador = "\nif __name__ == '__main__':"
            ultimo_if = conteudo.rfind(marcador)
            if ultimo_if >= 0:
                conteudo = conteudo + data_block + conteudo[ultimo_if:]
            else:
                conteudo += data_block
            temp_path = self._caminho + '.temp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            if os.path.exists(self._caminho + '.bak2'):
                os.remove(self._caminho + '.bak2')
            if os.path.exists(self._caminho + '.bak'):
                os.rename(self._caminho + '.bak', self._caminho + '.bak2')
            os.rename(self._caminho, self._caminho + '.bak')
            os.rename(temp_path, self._caminho)
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
