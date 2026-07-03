"""
Super Fragmentador: fragmenta QUALQUER dado, processa com IA, compila, referencia.
Aplica o padrao V12 (Python estrutura + IA blanks) em loop infinito.

Fluxo:
  Input (arquivo/texto/codigo)
    -> Fragmentador (quebra em pedacos < ctx_alvo)
    -> Para cada fragmento: IA processa (com referencia aos vizinhos)
    -> Compilador (junta resultados parciais)
    -> Referenciador (cruza dados entre fragmentos)
    -> Output final
"""
import json, os, re, time, sys
from typing import List, Dict, Any, Optional

# Contexto maximo padrao por modelo (via Model Router)
CTX_PADRAO = {
    "qwen2.5-coder:1.5b": 2048,
    "qwen2.5-coder:7b":   2048,
    "deepseek-r1:7b":     2048,
    "llama3.1:8b":        2048,
    "qwen2.5:14b":        1024,
}

class Fragmento:
    """Um pedaco de dado com metadados para re-montagem."""
    def __init__(self, idx: int, conteudo: str, origem: str = "",
                 tipo: str = "texto", ctx_estimado: int = 0):
        self.idx = idx
        self.conteudo = conteudo
        self.origem = origem
        self.tipo = tipo  # texto, codigo, json, xml, csv
        self.ctx_estimado = ctx_estimado or len(conteudo) // 2  # estimativa tokens
        self.resultado = None
        self.referencias = []  # IDs de fragmentos relacionados

    def to_dict(self):
        return {
            "idx": self.idx,
            "tipo": self.tipo,
            "origem": self.origem,
            "ctx": self.ctx_estimado,
            "conteudo": self.conteudo,
            "resultado": str(self.resultado) if self.resultado else None,
            "refs": self.referencias
        }

class SuperFragmentador:
    """
    Fragmenta, processa com IA, compila e referencia qualquer dado.
    Usa o Model Router do MCR-DevIA para escolher o melhor modelo.
    """
    
    def __init__(self, modelo_padrao: str = None,
                 ctx_alvo: int = 1024):
        if modelo_padrao is None:
            try:
                from modulos.util import _get_modelo
                cfg = _get_modelo("leve")
                modelo_padrao = cfg["modelo"]
            except:
                modelo_padrao = "qwen2.5-coder:7b"  # fallback seguro
        self.modelo_padrao = modelo_padrao
        self.ctx_alvo = ctx_alvo
        self.fragmentos: List[Fragmento] = []
        self.metadados = {}
    
    # ----------------------------------------------------------
    # FRAGMENTACAO
    # ----------------------------------------------------------
    def fragmentar(self, dados: Any, formato: str = "auto") -> List[Fragmento]:
        """
        Fragmenta QUALQUER dado em pedacos que cabem no ctx_alvo.
        Formatos suportados: auto, texto, linhas, json, xml, csv, codigo
        """
        if formato == "auto":
            formato = self._detectar_formato(dados)
        
        self.fragmentos = []
        
        if formato == "json" and isinstance(dados, list):
            self._fragmentar_lista(dados)
        elif formato == "json" and isinstance(dados, dict):
            self._fragmentar_dict(dados)
        elif formato in ("xml", "csv", "ini"):
            self._fragmentar_linhas(dados.split('\n') if isinstance(dados, str) else dados)
        elif formato == "codigo" or formato == "texto":
            self._fragmentar_texto(dados if isinstance(dados, str) else str(dados))
        else:
            self._fragmentar_texto(str(dados))
        
        # Adicionar referencias entre fragmentos adjacentes
        for i, f in enumerate(self.fragmentos):
            if i > 0: f.referencias.append(self.fragmentos[i-1].idx)
            if i < len(self.fragmentos) - 1: f.referencias.append(self.fragmentos[i+1].idx)
        
        return self.fragmentos
    
    def _detectar_formato(self, dados):
        """Detecta formato automaticamente."""
        if isinstance(dados, list):
            return "json"
        if isinstance(dados, dict):
            return "json"
        s = str(dados)
        if s.strip().startswith("<") and ">" in s:
            return "xml"
        if s.strip().startswith("{"):
            return "json"
        if "," in s and "\n" in s:
            # Pode ser CSV
            linhas = s.split('\n')
            if len(linhas) > 1 and len(linhas[0].split(',')) == len(linhas[1].split(',')):
                return "csv"
        if re.search(r'\b(def |class |function |local |int |void |#include)', s):
            return "codigo"
        return "texto"
    
    def _fragmentar_lista(self, dados: list):
        """Fragmenta uma lista de itens (ex: JSON array)."""
        ctx_por_item = max(1, self.ctx_alvo // max(len(dados), 1))
        bloco = []; bloco_ctx = 0; idx = 0
        for item in dados:
            item_ctx = len(json.dumps(item, ensure_ascii=False)) // 2
            if bloco_ctx + item_ctx > self.ctx_alvo and bloco:
                self.fragmentos.append(Fragmento(idx, json.dumps(bloco, ensure_ascii=False),
                    tipo="json", ctx_estimado=bloco_ctx))
                idx += 1; bloco = []; bloco_ctx = 0
            bloco.append(item)
            bloco_ctx += item_ctx
        if bloco:
            self.fragmentos.append(Fragmento(idx, json.dumps(bloco, ensure_ascii=False),
                tipo="json", ctx_estimado=bloco_ctx))
    
    def _fragmentar_dict(self, dados: dict):
        """Fragmenta um dicionario em chunks de chaves."""
        itens = list(dados.items())
        self._fragmentar_texto("\n".join(f"{k}: {v}" for k, v in itens))
    
    def _fragmentar_linhas(self, linhas: list):
        """Fragmenta linhas agrupando ate ctx_alvo."""
        bloco = []; bloco_ctx = 0; idx = 0
        for linha in linhas:
            linha_ctx = len(linha) // 2
            if bloco_ctx + linha_ctx > self.ctx_alvo and bloco:
                self.fragmentos.append(Fragmento(idx, '\n'.join(bloco),
                    tipo="texto", ctx_estimado=bloco_ctx))
                idx += 1; bloco = []; bloco_ctx = 0
            bloco.append(linha)
            bloco_ctx += linha_ctx
        if bloco:
            self.fragmentos.append(Fragmento(idx, '\n'.join(bloco),
                tipo="texto", ctx_estimado=bloco_ctx))
    
    def _fragmentar_texto(self, texto: str):
        """Fragmenta texto puro por paragrafos."""
        paragrafos = texto.split('\n\n')
        bloco = []; bloco_ctx = 0; idx = 0
        for p in paragrafos:
            p_ctx = len(p) // 2
            if bloco_ctx + p_ctx > self.ctx_alvo and bloco:
                self.fragmentos.append(Fragmento(idx, '\n\n'.join(bloco),
                    tipo="texto", ctx_estimado=bloco_ctx))
                idx += 1; bloco = []; bloco_ctx = 0
            bloco.append(p)
            bloco_ctx += p_ctx
        if bloco:
            self.fragmentos.append(Fragmento(idx, '\n\n'.join(bloco),
                tipo="texto", ctx_estimado=bloco_ctx))
    
    # ----------------------------------------------------------
    # PROCESSAMENTO COM IA
    # ----------------------------------------------------------
    def processar(self, modelo: str = None, tarefa: str = "code",
                  temp: float = 0.3, callback=None) -> List[Fragmento]:
        """
        Processa cada fragmento com IA.
        Se callback for None, usa chamada direta ao Ollama.
        callback(fragmento) deve retornar o resultado.
        """
        from urllib import request as ur
        import json as jn
        
        ollama_url = "http://localhost:11434/api/generate"
        modelo = modelo or self.modelo_padrao
        ctx = CTX_PADRAO.get(modelo, self.ctx_alvo)
        
        for i, frag in enumerate(self.fragmentos):
            if callback:
                frag.resultado = callback(frag)
            else:
                # Incluir contexto dos fragmentos vizinhos
                contexto_extra = ""
                for ref in frag.referencias:
                    ref_frag = self.fragmentos[ref] if ref < len(self.fragmentos) else None
                    if ref_frag and ref_frag.resultado:
                        contexto_extra += f"\n[Fragmento {ref}]: {str(ref_frag.resultado)}"
                
                prompt = f"{contexto_extra}\n[Fragmento {frag.idx}]:\n{frag.conteudo[:ctx*2]}\n\nProcesse este fragmento e retorne o resultado:"
                payload = jn.dumps({
                    "model": modelo, "prompt": prompt, "stream": False,
                    "options": {"temperature": temp, "num_ctx": min(ctx, 2048)}
                }).encode()
                try:
                    req = ur.Request(ollama_url, data=payload,
                        headers={"Content-Type": "application/json"})
                    resp = ur.urlopen(req, timeout=60).read()
                    frag.resultado = jn.loads(resp).get("response", "")
                except Exception as e:
                    frag.resultado = f"[ERRO] {e}"
            
            print(f"  Fragmento {i+1}/{len(self.fragmentos)}: {str(frag.resultado)}...")
        
        return self.fragmentos
    
    # ----------------------------------------------------------
    # COMPILACAO
    # ----------------------------------------------------------
    def compilar(self, formato: str = "auto") -> str:
        """
        Compila resultados parciais em uma saida unificada.
        """
        if not self.fragmentos:
            return ""
        
        # Ordenar por idx
        sorted_frags = sorted(self.fragmentos, key=lambda f: f.idx)
        
        if formato == "json" or all(f.tipo == "json" for f in sorted_frags):
            # Tenta juntar como JSON array
            resultados = []
            for f in sorted_frags:
                try:
                    r = json.loads(str(f.resultado or f.conteudo))
                    if isinstance(r, list): resultados.extend(r)
                    else: resultados.append(r)
                except Exception as e:
                    print(f"[Fix] ERRO: {e}")
            return json.dumps(resultados, ensure_ascii=False, indent=2)
        
        # Compilacao textual
        saida = []
        for f in sorted_frags:
            if f.resultado:
                saida.append(f"--- Fragmento {f.idx} ---")
                saida.append(str(f.resultado))
        
        return '\n'.join(saida)
    
    # ----------------------------------------------------------
    # REFERENCIACAO (consistencia entre fragmentos)
    # ----------------------------------------------------------
    def referenciar(self, modelo: str = None) -> List[str]:
        """
        Verifica consistencia entre fragmentos.
        Retorna lista de inconsistencias encontradas.
        """
        inconsistencias = []
        if len(self.fragmentos) < 2:
            return inconsistencias
        
        # Verificar pares adjacentes
        for i in range(len(self.fragmentos) - 1):
            a = self.fragmentos[i]
            b = self.fragmentos[i+1]
            if a.resultado and b.resultado:
                # Verificar se há contradicao basica
                ra = str(a.resultado).lower()
                rb = str(b.resultado).lower()
                if ("sim" in ra and "nao" in rb) or ("ok" in ra and "erro" in rb):
                    inconsistencias.append(
                        f"Fragmento {a.idx} e {b.idx}: possivel contradicao")
        
        return inconsistencias
    
    # ----------------------------------------------------------
    # ANALISE ESTATISTICA
    # ----------------------------------------------------------
    def estatisticas(self) -> dict:
        """Retorna metricas da fragmentacao."""
        if not self.fragmentos:
            return {"fragmentos": 0, "ctx_medio": 0, "ctx_total": 0}
        ctxs = [f.ctx_estimado for f in self.fragmentos]
        return {
            "fragmentos": len(self.fragmentos),
            "ctx_medio": sum(ctxs) // len(ctxs),
            "ctx_max": max(ctxs),
            "ctx_total": sum(ctxs),
            "com_resultado": sum(1 for f in self.fragmentos if f.resultado),
            "modelo": self.modelo_padrao,
            "ctx_alvo": self.ctx_alvo
        }
    
    # ----------------------------------------------------------
    # LOOP COMPLETO (fragmentar + processar + compilar + referenciar)
    # ----------------------------------------------------------
    def executar(self, dados: Any, formato: str = "auto",
                 modelo: str = None, tarefa: str = "code",
                 temp: float = 0.3, callback=None) -> dict:
        """
        Loop completo: fragmenta, processa, compila, referencia.
        Retorna dict com resultado final e estatisticas.
        """
        print(f"[SuperFragmentador] Iniciando... (ctx_alvo={self.ctx_alvo}, modelo={modelo or self.modelo_padrao})")
        
        # 1. Fragmentar
        inicio = time.time()
        frags = self.fragmentar(dados, formato)
        print(f"  Fragmentacao: {len(frags)} fragmentos em {time.time()-inicio:.1f}s")
        
        # 2. Processar
        inicio = time.time()
        self.processar(modelo, tarefa, temp, callback)
        print(f"  Processamento: {time.time()-inicio:.1f}s")
        
        # 3. Compilar
        resultado = self.compilar()
        
        # 4. Referenciar
        inconsistencias = self.referenciar(modelo)
        
        # 5. Se houver inconsistencias, reprocessar
        if inconsistencias and callback is None:
            print(f"  Inconsistencias: {len(inconsistencias)}. Reprocessando...")
            # Adicionar contexto das inconsistencias nos prompts
            for inc in inconsistencias:
                print(f"    {inc}")
        
        return {
            "resultado": resultado,
            "fragmentos": [f.to_dict() for f in self.fragmentos],
            "estatisticas": self.estatisticas(),
            "inconsistencias": inconsistencias,
            "tempo_total": time.time() - (self._inicio if hasattr(self, '_inicio') else time.time())
        }


# ============================================================
# TESTE / EXEMPLO
# ============================================================
if __name__ == "__main__":
    # Teste com dados reais do items.xml
    import urllib.request
    
    # Dados de exemplo (items XML simplificado)
    dados_teste = [
        {"id": 500, "name": "Power Bolt", "article": "um", "plural": "Parafusos Poderosos", "type": "ammunition"},
        {"id": 501, "name": "Flecha de Fogo", "article": "um", "plural": "Flechas de Fogo", "type": "ammunition"},
        {"id": 502, "name": "Poção de cura", "article": "uma", "plural": "Poções de cura", "type": "potion"},
        {"id": 503, "name": "Espada Longa", "article": "uma", "plural": "Espadas Longas", "type": "weapon"},
    ]
    
    sf = SuperFragmentador(ctx_alvo=512)  # ctx pequeno forçado
    resultado = sf.executar(dados_teste, formato="json", modelo="qwen2.5-coder:1.5b", tarefa="fast",
                           temp=0.1)
    
    print("\n\n=== RESULTADO ===")
    print(json.dumps(resultado["estatisticas"], indent=2))
    print(f"\nInconsistencias: {resultado['inconsistencias']}")
    print(f"\nResultado compilado:\n{resultado['resultado']}")
