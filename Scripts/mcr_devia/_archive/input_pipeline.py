"""
INPUT PIPELINE v1.0 — Processamento de Entrada Infinita
=========================================================
Aplica o Crew Pattern na ENTRADA: fragmentar → processar peca por peca → montar.

Isso permite processar QUALQUER entrada, de QUALQUER tamanho:
  1. Fragmenta em pedacos atomicos (cabem no contexto do modelo)
  2. Processa CADA pedaco independentemente (reusa CrewPipeline)
  3. Monta resposta final com SCRIPT PYTHON (V12: 0 IA na montagem)

Fluxo:
  ENTRADA BRUTA (texto, arquivos, comandos)
       ↓
  [Fragmentador] - Divide em fragmentos atomicos
       ↓
  [Processador]  - CrewPipeline.processar() em CADA fragmento
       ↓
  [Buffer]       - Resultados intermediarios com ID
       ↓
  [Montador]     - Script Python monta resposta final (0 IA)
       ↓
  SAIDA FINAL
"""

import os, re, sys, json, time
from typing import List, Dict, Optional, Callable, Any, Union

OLLAMA_URL = 'http://localhost:11434/api/generate'

# ============================================================
# 1. FRAGMENTADOR DE ENTRADA
# ============================================================

class Fragmento:
    """Um pedaco atomico de entrada."""
    def __init__(self, idx: int, conteudo: str, tipo: str = "texto",
                 origem: str = "", metadados: dict = None):
        self.idx = idx
        self.conteudo = conteudo
        self.tipo = tipo  # texto, pergunta, comando, arquivo, codigo
        self.origem = origem
        self.metadados = metadados or {}
        self.resultado = None  # Preenchido pelo processador
        self.tempo = 0.0
        self.origem_resposta = None  # v12, crew, ia, none
    
    def to_dict(self):
        return {
            "idx": self.idx,
            "tipo": self.tipo,
            "origem": self.origem,
            "conteudo": self.conteudo[:150],
            "resultado": str(self.resultado)[:150] if self.resultado else None,
            "origem_resposta": self.origem_resposta,
            "tempo": round(self.tempo, 2)
        }


class FragmentadorEntrada:
    """
    Fragmenta entrada bruta em pedacos atomicos.
    Suporta: texto, perguntas multiplas, comandos, arquivos referenciados, JSON, XML.
    """
    
    def __init__(self, ctx_max: int = 1024):
        self.ctx_max = ctx_max
    
    def fragmentar(self, entrada: Union[str, list, dict],
                   formato: str = "auto") -> List[Fragmento]:
        """Detecta formato e fragmenta."""
        if formato == "auto":
            formato = self._detectar_formato(entrada)
        
        if formato == "multiplas_perguntas":
            return self._fragmentar_perguntas(entrada)
        elif formato == "json" and isinstance(entrada, list):
            return self._fragmentar_lista(entrada)
        elif formato == "json" and isinstance(entrada, dict):
            return self._fragmentar_dict(entrada)
        elif formato == "arquivos":
            return self._fragmentar_arquivos(entrada)
        elif formato == "comandos":
            return self._fragmentar_comandos(entrada)
        else:  # texto
            return self._fragmentar_texto(str(entrada))
    
    def _detectar_formato(self, entrada) -> str:
        """Detecta formato automaticamente da entrada."""
        s = str(entrada) if not isinstance(entrada, str) else entrada
        
        # --- DETECTAR MULTIPLOS FRAGMENTOS ---
        # 1) Multiplos '?' na mesma linha
        qtd_interrogacoes = s.count('?')
        if qtd_interrogacoes >= 2:
            return "multiplas_perguntas"
        
        # 2) Multiplos '. ' com frases autonomas (cada sentenca parece uma instrucao)
        # Quebra por '. ' e ve quantas sentencas tem pelo menos 3 palavras
        sentencas = re.split(r'\.\s+', s)
        sentencas_validas = [se for se in sentencas if len(se.strip().split()) >= 3 and
                             any(c.isupper() for c in se[:3])]
        if len(sentencas_validas) >= 3:
            return "multiplas_perguntas"
        
        # 3) Multiplos '?' em linhas separadas
        linhas = s.strip().split('\n')
        perguntas = [l for l in linhas if '?' in l and len(l) > 10]
        if len(perguntas) >= 2:
            return "multiplas_perguntas"
        
        # Detectar comandos (linhas com verbos de acao)
        verbos = {'analisar', 'criar', 'gerar', 'compilar', 'buscar', 'comparar',
                  'listar', 'explicar', 'mostrar', 'executar', 'processar'}
        comandos = [l for l in linhas if any(v in l.lower() for v in verbos) and len(l) > 15]
        if len(comandos) >= 2:
            return "comandos"
        
        # Detectar arquivos (.py, .lua, .xml, etc)
        arquivos = re.findall(r'[\w\-\/]+\.(?:py|lua|xml|json|txt|md|cpp|h|ts|js)', s)
        if len(arquivos) >= 2:
            return "arquivos"
        
        # Detectar JSON
        if s.strip().startswith('[') or s.strip().startswith('{'):
            return "json"
        
        return "texto"
    
    def _fragmentar_perguntas(self, texto: str) -> List[Fragmento]:
        """Divide texto em perguntas individuais.
        Suporta:
        - Perguntas na mesma linha separadas por '?' (ex: 'O que e X? O que e Y?')
        - Perguntas em linhas separadas
        - Instrucoes compostas separadas por '. ' (ex: 'Explique X. Faca Y.')
        """
        texto = texto.strip()
        if not texto:
            return [Fragmento(0, texto, tipo="texto")]
        
        # PASSO 1: Quebrar por '?' (preservando o '?' em cada parte)
        partes = texto.split('?')
        perguntas_brutas = []
        for i, parte in enumerate(partes):
            p = parte.strip()
            if p:
                perguntas_brutas.append(p + ('?' if i < len(partes) - 1 else ''))
        
        # PASSO 2: Dentro de cada parte sem '?', tentar quebrar por '. '
        # (ex: "Explique SHC. Compare com SPA." vira 2 fragmentos)
        fragmentos_finais = []
        for parte in perguntas_brutas:
            # Se a parte tem um ponto final seguido de palavra maiuscula, pode ser 2 instrucoes
            sub_partes = re.split(r'\.\s+(?=[A-Z\u00C0-\u00FF])', parte)
            if len(sub_partes) > 1 and all(len(s.split()) >= 2 for s in sub_partes):
                # Cada sub-parte e uma instrucao individual
                for sp in sub_partes:
                    sp = sp.strip()
                    if sp:
                        fragmentos_finais.append(sp)
            else:
                fragmentos_finais.append(parte)
        
        # Se todas as partes tem tamanho viavel de fragmento
        todas_validas = all(2 <= len(p.split()) <= 25 for p in fragmentos_finais)
        
        fragmentos = []
        if todas_validas and len(fragmentos_finais) >= 2:
            for idx, p in enumerate(fragmentos_finais):
                tipo = "pergunta" if '?' in p else "texto"
                fragmentos.append(Fragmento(idx, p, tipo=tipo))
        else:
            # Fallback: quebra por linhas
            linhas = texto.split('\n')
            idx = 0
            atual = []
            for linha in linhas:
                linha = linha.strip()
                if not linha:
                    continue
                atual.append(linha)
                if '?' in linha and len(atual) <= 3:
                    conteudo = ' '.join(atual)
                    fragmentos.append(Fragmento(idx, conteudo, tipo="pergunta"))
                    idx += 1
                    atual = []
                elif len(' '.join(atual)) > self.ctx_max:
                    conteudo = ' '.join(atual)
                    fragmentos.append(Fragmento(idx, conteudo, tipo="texto"))
                    idx += 1
                    atual = []
            
            if atual:
                fragmentos.append(Fragmento(idx, ' '.join(atual), tipo="pergunta"))
        
        return fragmentos if fragmentos else [Fragmento(0, texto, tipo="texto")]
    
    def _fragmentar_texto(self, texto: str) -> List[Fragmento]:
        """Divide texto longo em fragmentos por paragrafo.
        Se um paragrafo exceder o limite, quebra por sentencas ou caracteres."""
        paragrafos = [p.strip() for p in texto.split('\n\n') if p.strip()]
        if not paragrafos:
            # Sem paragrafos: quebra por sentencas ou fatias
            return self._fragmentar_sentencas(texto)
        
        fragmentos = []
        idx = 0
        bloco = []
        bloco_chars = 0
        limite = self.ctx_max * 2
        
        for p in paragrafos:
            if len(p) > limite:
                # Paragrafo unico enorme: fragmenta por sentencas
                if bloco:
                    fragmentos.append(Fragmento(idx, '\n\n'.join(bloco), tipo="texto"))
                    idx += 1
                    bloco = []; bloco_chars = 0
                sub_frags = self._fragmentar_sentencas(p)
                for sf in sub_frags:
                    sf.idx = idx
                    fragmentos.append(sf)
                    idx += 1
            elif bloco_chars + len(p) > limite and bloco:
                fragmentos.append(Fragmento(idx, '\n\n'.join(bloco), tipo="texto"))
                idx += 1
                bloco = []
                bloco_chars = 0
                bloco.append(p)
                bloco_chars += len(p)
            else:
                bloco.append(p)
                bloco_chars += len(p)
        
        if bloco:
            fragmentos.append(Fragmento(idx, '\n\n'.join(bloco), tipo="texto"))
        
        return fragmentos
    
    def _fragmentar_sentencas(self, texto: str) -> List[Fragmento]:
        """Quebra texto por sentencas, depois agrupa ate ctx_max.
        Se nao achar delimitadores logicos, quebra por caracteres."""
        limite = self.ctx_max * 2
        
        # Tenta dividir por . ! ? seguido de espaco/nova linha
        sentencas = re.split(r'(?<=[.!?])\s+', texto)
        sentencas = [s.strip() for s in sentencas if s.strip()]
        
        # Se nao achou delimitadores, ou se a primeira sentenca ja estoura o limite
        if not sentencas or len(sentencas[0]) > limite:
            # Fallback: quebra por caracteres
            sentencas = [texto[i:i+limite] for i in range(0, len(texto), limite)]
        
        fragmentos = []
        bloco = []; bloco_chars = 0
        for s in sentencas:
            if len(s) > limite:
                # Sentenca muito longa mesmo apos fallback: quebra fatia
                if bloco:
                    fragmentos.append(Fragmento(len(fragmentos), ' '.join(bloco), tipo="texto"))
                    bloco = []; bloco_chars = 0
                for i in range(0, len(s), limite):
                    fragmentos.append(Fragmento(len(fragmentos), s[i:i+limite], tipo="texto"))
            elif bloco_chars + len(s) > limite and bloco:
                fragmentos.append(Fragmento(len(fragmentos), ' '.join(bloco), tipo="texto"))
                bloco = []; bloco_chars = 0
                bloco.append(s)
                bloco_chars += len(s)
            else:
                bloco.append(s)
                bloco_chars += len(s)
        if bloco:
            fragmentos.append(Fragmento(len(fragmentos), ' '.join(bloco), tipo="texto"))
        
        return fragmentos if fragmentos else [Fragmento(0, texto[:limite], tipo="texto")]
    
    def _fragmentar_arquivos(self, entrada: str) -> List[Fragmento]:
        """Entrada referencia arquivos. Le e fragmenta cada um."""
        # Se entrada e uma string, procura por nomes de arquivo
        if isinstance(entrada, str):
            arquivos = re.findall(r'[\w\-\/]+\.(?:py|lua|xml|json|txt|md|cpp|h|ts|js)', entrada)
        elif isinstance(entrada, list):
            arquivos = entrada
        else:
            arquivos = [entrada]
        
        fragmentos = []
        for idx, nome in enumerate(arquivos[:10]):  # Max 10 arquivos
            # Tentar resolver caminho
            path = nome
            if not os.path.exists(path):
                # Tentar no sandbox
                path_sandbox = os.path.join(os.path.dirname(__file__), '..', '..',
                                            'sandbox', nome)
                if os.path.exists(path_sandbox):
                    path = path_sandbox
            
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read(4000)  # Limite de 4K por arquivo
                    ext = os.path.splitext(nome)[1]
                    tipo = "codigo" if ext in ('.py', '.lua', '.cpp', '.h', '.ts', '.js') else "texto"
                    fragmentos.append(Fragmento(idx, conteudo, tipo=tipo, origem=nome))
                except Exception as e:
                    print(f"[Fix] ERRO: {e}")
            else:
                fragmentos.append(Fragmento(idx, nome, tipo="texto", origem=nome))
        
        return fragmentos if fragmentos else [Fragmento(0, entrada, tipo="texto")]
    
    def _fragmentar_comandos(self, texto: str) -> List[Fragmento]:
        """Divide em comandos individuais."""
        linhas = texto.strip().split('\n')
        fragmentos = []
        for idx, linha in enumerate(linhas):
            linha = linha.strip()
            if linha:
                fragmentos.append(Fragmento(idx, linha, tipo="comando"))
        return fragmentos if fragmentos else [Fragmento(0, texto, tipo="comando")]
    
    def _fragmentar_lista(self, dados: list) -> List[Fragmento]:
        """Fragmenta lista JSON."""
        fragmentos = []
        for idx, item in enumerate(dados):
            conteudo = json.dumps(item, ensure_ascii=False)
            if len(conteudo) > self.ctx_max * 2:
                # Item muito grande, fragmenta como texto
                fragmentos.extend(self._fragmentar_texto(conteudo))
            else:
                fragmentos.append(Fragmento(idx, conteudo, tipo="json"))
        return fragmentos
    
    def _fragmentar_dict(self, dados: dict) -> List[Fragmento]:
        """Fragmenta dicionario em pares chave:valor."""
        return self._fragmentar_texto(
            "\n".join(f"{k}: {v}" for k, v in dados.items())
        )


# ============================================================
# 2. PROCESSADOR DE FRAGMENTOS
# ============================================================

class ProcessadorFragmentos:
    """
    Processa CADA fragmento independentemente usando CrewPipeline.
    (V12 check → ContextCrew → fn_compactar)
    """
    
    def __init__(self, kg, ia, ctx_crew=None, verbose=True):
        self.kg = kg
        self.ia = ia
        self.ctx_crew = ctx_crew
        self.verbose = verbose
        self._crew_pipeline = None
    
    def processar(self, fragmento: Fragmento) -> Fragmento:
        """Processa um fragmento e armazena resultado."""
        t0 = time.time()
        
        # Tenta CrewPipeline primeiro
        resultado = self._crew(fragmento.conteudo)
        
        if resultado:
            fragmento.resultado = resultado
            fragmento.origem_resposta = "crew"
        elif self.ia:
            # Fallback: IA direta
            r = self.ia.gerar(
                f"Responda de forma clara e objetiva: {fragmento.conteudo[:500]}",
                temp=0.3
            )
            if r and len(r) > 20:
                fragmento.resultado = r
                fragmento.origem_resposta = "ia"
            else:
                fragmento.resultado = fragmento.conteudo[:200]
                fragmento.origem_resposta = "none"
        else:
            fragmento.resultado = fragmento.conteudo[:200]
            fragmento.origem_resposta = "none"
        
        fragmento.tempo = time.time() - t0
        
        if self.verbose:
            print(f'    [Frag {fragmento.idx}] {fragmento.origem_resposta} '
                  f'({fragmento.tempo:.1f}s): {str(fragmento.resultado)[:80]}...')
        
        return fragmento
    
    def _crew(self, texto: str) -> Optional[str]:
        """Usa CrewPipeline para processar o texto."""
        if not self._crew_pipeline:
            try:
                from crew_pattern import CrewPipeline
                self._crew_pipeline = CrewPipeline(
                    self.kg, self.ia, self.ctx_crew, verbose=False
                )
            except Exception as e:
                print(f"[Fix] ERRO: {e}")
        
        return self._crew_pipeline.processar(texto)
    
    def processar_lote(self, fragmentos: List[Fragmento]) -> List[Fragmento]:
        """Processa todos os fragmentos em lote."""
        for frag in fragmentos:
            self.processar(frag)
        return fragmentos


# ============================================================
# 3. MONTADOR (SCRIPT DE MONTAGEM)
# ============================================================

class Montador:
    """
    Monta resposta final a partir dos fragmentos processados.
    V12 PURO: Python estrutura, 0 IA.
    
    Estrategias de montagem:
      - concat: junta resultados em ordem (para textos/perguntas)
      - estrutura: cria estrutura com headers (para comandos)
      - tabela: monta tabela comparativa (para analises)
      - relatorio: sumario estruturado
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
    
    def montar(self, fragmentos: List[Fragmento],
               estrategia: str = "auto") -> str:
        """Monta resposta final."""
        if not fragmentos:
            return ""
        
        if estrategia == "auto":
            estrategia = self._detectar_estrategia(fragmentos)
        
        if self.verbose:
            print(f'  [Montador] Estrategia: {estrategia} '
                  f'({len(fragmentos)} fragmentos)')
        
        if estrategia == "concat":
            return self._montar_concat(fragmentos)
        elif estrategia == "estrutura":
            return self._montar_estrutura(fragmentos)
        elif estrategia == "tabela":
            return self._montar_tabela(fragmentos)
        elif estrategia == "relatorio":
            return self._montar_relatorio(fragmentos)
        elif estrategia == "sumario":
            return self._montar_sumario(fragmentos)
        else:
            return self._montar_concat(fragmentos)
    
    def _detectar_estrategia(self, fragmentos: List[Fragmento]) -> str:
        """Detecta melhor estrategia baseado nos fragmentos."""
        # Contar tipos
        tipos = {}
        for f in fragmentos:
            tipos[f.tipo] = tipos.get(f.tipo, 0) + 1
        
        # Multiplos arquivos/codigo → tabela comparativa
        if tipos.get('codigo', 0) >= 2 or tipos.get('json', 0) >= 2:
            return "tabela"
        
        # Comandos → estrutura com headers
        if tipos.get('comando', 0) >= 2:
            return "estrutura"
        
        # Textos longos → sumario
        if tipos.get('texto', 0) >= 3:
            return "sumario"
        
        # Multiplos resultados → estrutura
        if len(fragmentos) >= 3:
            return "estrutura"
        
        # Padrao: concat
        return "concat"
    
    def _montar_concat(self, fragmentos: List[Fragmento]) -> str:
        """Concatena resultados em ordem."""
        partes = []
        for i, f in enumerate(fragmentos):
            if f.resultado:
                if len(fragmentos) > 1:
                    partes.append(f"=== Fragmento {i+1} ===")
                partes.append(str(f.resultado).strip())
        return '\n\n'.join(partes)
    
    def _montar_estrutura(self, fragmentos: List[Fragmento]) -> str:
        """Monta estrutura com headers descritivos."""
        partes = []
        for i, f in enumerate(fragmentos):
            cabecalho = f.origem or f"Ponto {i+1}"
            if f.tipo:
                cabecalho = f"{cabecalho} ({f.tipo})"
            partes.append(f"## {cabecalho}")
            partes.append(str(f.resultado or "[sem resultado]").strip())
        return '\n\n'.join(partes)
    
    def _montar_tabela(self, fragmentos: List[Fragmento]) -> str:
        """Monta tabela comparativa."""
        linhas = ["| # | Item | Resultado | Origem | Tempo |",
                   "|---|------|-----------|--------|-------|"]
        for i, f in enumerate(fragmentos):
            nome = f.origem or f"Item {i+1}"
            resultado = str(f.resultado or "-")[:60].replace('\n', ' ')
            linhas.append(f"| {i+1} | {nome} | {resultado} | "
                         f"{f.origem_resposta or '-'} | {f.tempo:.1f}s |")
        
        tabela = '\n'.join(linhas)
        
        # Adicionar sumario
        total_ok = sum(1 for f in fragmentos if f.resultado)
        total_tempo = sum(f.tempo for f in fragmentos)
        sumario = (f"\n**Resumo:** {total_ok}/{len(fragmentos)} processados "
                  f"em {total_tempo:.1f}s")
        
        return tabela + sumario
    
    def _montar_relatorio(self, fragmentos: List[Fragmento]) -> str:
        """Monta relatorio com metadados."""
        partes = []
        
        # Cabecalho
        partes.append("# Relatorio de Processamento")
        partes.append(f"Fragmentos: {len(fragmentos)}")
        
        # Resultados
        for i, f in enumerate(fragmentos):
            if f.resultado:
                titulo = f.origem or f"Item {i+1}"
                partes.append(f"\n## {i+1}. {titulo}")
                partes.append(str(f.resultado).strip())
                if f.tempo > 1:
                    partes.append(f"*(processado em {f.tempo:.1f}s)*")
        
        # Rodape
        total = sum(f.tempo for f in fragmentos)
        partes.append(f"\n---\nTempo total: {total:.1f}s")
        
        return '\n'.join(partes)
    
    def _montar_sumario(self, fragmentos: List[Fragmento]) -> str:
        """Sumario conciso."""
        partes = []
        
        # Pontos principais
        for i, f in enumerate(fragmentos):
            if f.resultado:
                resumo = str(f.resultado)[:200].strip()
                partes.append(f"- {resumo}")
        
        return '\n'.join(partes)


# ============================================================
# 4. PIPELINE PRINCIPAL
# ============================================================

class InputPipeline:
    """
    Pipeline de entrada infinita.
    
    Uso:
        pipe = InputPipeline(kg, ia)
        resposta = pipe.executar("O que e MCR? Explique SHC. Como compilar OTClient?")
        # Fragmenta em 3 perguntas, processa cada uma, monta resultado final
    """
    
    def __init__(self, kg=None, ia=None, ctx_crew=None, verbose=True):
        self.kg = kg
        self.ia = ia
        self.ctx_crew = ctx_crew
        self.verbose = verbose
        
        self.fragmentador = FragmentadorEntrada()
        self.processador = ProcessadorFragmentos(kg, ia, ctx_crew, verbose)
        self.montador = Montador(verbose)
        
        self.stats = {
            "execucoes": 0,
            "total_fragmentos": 0,
            "tempo_total": 0.0,
            "fragmentos_crew": 0,
            "fragmentos_ia": 0,
            "estrategias_usadas": {}
        }
    
    def executar(self, entrada: Union[str, list, dict],
                 estrategia: str = "auto",
                 formato: str = "auto") -> str:
        """Pipeline completa: fragmentar → processar → montar."""
        t0 = time.time()
        self.stats["execucoes"] += 1
        
        if self.verbose:
            entrada_str = str(entrada)[:100]
            print(f'\n[InputPipeline] "{entrada_str}..."')
        
        # 1. FRAGMENTAR
        fragmentos = self.fragmentador.fragmentar(entrada, formato)
        self.stats["total_fragmentos"] += len(fragmentos)
        
        if self.verbose:
            print(f'  [Fragmentador] {len(fragmentos)} fragmentos')
            for f in fragmentos:
                print(f'    Frag {f.idx}: tipo={f.tipo} origem={f.origem or "-"} '
                      f'({len(f.conteudo)} chars)')
        
        # 2. PROCESSAR CADA FRAGMENTO
        if len(fragmentos) == 1:
            # Fragmento unico: processamento direto
            self.processador.processar(fragmentos[0])
        else:
            # Multiplos fragmentos: processa cada um
            self.processador.processar_lote(fragmentos)
        
        # Atualizar stats
        for f in fragmentos:
            if f.origem_resposta == "crew":
                self.stats["fragmentos_crew"] += 1
            elif f.origem_resposta == "ia":
                self.stats["fragmentos_ia"] += 1
        
        # 3. MONTAR RESPOSTA FINAL
        resposta = self.montador.montar(fragmentos, estrategia)
        self.stats["estrategias_usadas"][
            self.montador._detectar_estrategia(fragmentos)
        ] = self.stats["estrategias_usadas"].get(
            self.montador._detectar_estrategia(fragmentos), 0) + 1
        
        # Log
        dt = time.time() - t0
        self.stats["tempo_total"] += dt
        
        if self.verbose:
            print(f'  [InputPipeline] Concluido em {dt:.1f}s')
        
        return resposta
    
    def get_stats(self) -> Dict:
        s = dict(self.stats)
        if s["execucoes"] > 0:
            s["media_fragmentos"] = round(
                s["total_fragmentos"] / s["execucoes"], 1)
            s["tempo_medio"] = round(
                s["tempo_total"] / s["execucoes"], 1)
        return s


# ============================================================
# MAIN — Teste
# ============================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  INPUT PIPELINE — Teste Isolado")
    print("=" * 55)
    
    # Teste 1: Fragmentacao de multiplas perguntas
    pipe = InputPipeline(verbose=True)
    
    entrada_teste = """O que e MCR?
O que e SHC?
Como compilar o OTClient?
Qual a diferenca entre Canary e TFS?"""
    
    print("\n--- Teste 1: Fragmentar multiplas perguntas ---")
    frags = pipe.fragmentador.fragmentar(entrada_teste)
    print(f"  Fragmentos: {len(frags)}")
    for f in frags:
        print(f"    [{f.tipo}] {f.conteudo[:80]}...")
    
    # Teste 2: Fragmentacao de texto longo
    texto_longo = " ".join(["palavra"] * 2000)
    print(f"\n--- Teste 2: Fragmentar texto longo ({len(texto_longo)} chars) ---")
    frags = pipe.fragmentador.fragmentar(texto_longo)
    print(f"  Fragmentos: {len(frags)}")
    
    # Teste 3: Fragmentar arquivos
    print(f"\n--- Teste 3: Fragmentar referencia a arquivos ---")
    # Simular entrada com nomes de arquivo
    entrada_arq = "analise os arquivos crew_pattern.py e context_crew.py"
    # Sem os arquivos reais, testa o padrao de deteccao
    frags = pipe.fragmentador.fragmentar(entrada_arq)
    print(f"  Formato detectado: {pipe.fragmentador._detectar_formato(entrada_arq)}")
    print(f"  Fragmentos: {len(frags)}")
    for f in frags:
        print(f"    [{f.tipo}] {f.conteudo[:60]}...")
    
    # Teste 4: Montador com estrategias
    print(f"\n--- Teste 4: Montador com estrategias ---")
    frags_teste = [
        Fragmento(0, "Resposta sobre MCR", tipo="texto"),
        Fragmento(1, "Resposta sobre SHC", tipo="texto"),
        Fragmento(2, "Resposta sobre OTClient", tipo="texto"),
    ]
    for f in frags_teste:
        f.resultado = f"Resultado do fragmento {f.idx}: {f.conteudo}"
        f.origem_resposta = "crew"
        f.tempo = 1.5
    
    montador = Montador(verbose=True)
    print("\nEstrategia 'estrutura':")
    print(montador.montar(frags_teste, "estrutura"))
    
    print("\nEstrategia 'tabela':")
    print(montador.montar(frags_teste, "tabela"))
    
    print("\n[OK] InputPipeline tests basicos concluidos")
