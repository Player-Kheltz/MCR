#!/usr/bin/env python3
"""PROTÓTIPO: PatternEngine Omnidirecional — validação standalone.

Ciclo: analisa → executa → re-analisa → re-executa → até entropia < 0.3
Depois: converte n-gramas em esqueleto → preenche blanks → valida

NÃO MODIFICA NADA NO MCR. Só importa módulos existentes.
Arquivos criados vão para sandbox/test_output/
"""
import sys, os, json, math, re, time as _time

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))

from modulos.pattern_engine import PatternEngine
from modulos.tool_orchestrator import ToolOrchestrator
from modulos.intention_engine import IntentionEngine
from modulos.kg import KnowledgeGraph

# ============================================================
# BLANK FILLER OFFLINE (sem LLM) — extrai esqueleto de n-gramas
# ============================================================
class EsqueletoBuilder:
    """Converte n-gramas do PatternEngine em esqueleto com @BLANK_N.
    
    SEM LLM — determinístico, baseado puramente nos tokens do código real.
    """
    
    # Padrões de linguagem: sequência de tokens → template
    _PADROES_LINGUAGEM = {
        # Lua
        ('AST', 'KW', 'AST'): [
            'local @BLANK_NOME = @BLANK_TIPO:@BLANK_METODO("@BLANK_PARAM")'
        ],
        ('AST', 'AST', 'KW'): [
            '@BLANK_NOME:@BLANK_METODO("@BLANK_PARAM")'
        ],
        ('AST', 'AST', 'AST'): [
            '@BLANK_NOME:@BLANK_METODO(function(@BLANK_PARAMS)',
            '    @BLANK_CORPO',
            'end)'
        ],
        # Texto padrão
        ('ACAO', 'PAL_MEDIA', 'PAL_LONGA'): [
            '@BLANK_ACAO @BLANK_OBJETO @BLANK_DETALHE'
        ],
        ('FIM_FRASE', 'PAL_MEDIA', 'PAL_MEDIA'): [
            '@BLANK_FRASE.'
        ],
    }
    
    def __init__(self):
        self._prox_blank = 1
    
    def construir(self, tokens, padroes, linguagem='lua'):
        """Constrói esqueleto a partir de tokens reais.
        
        Args:
            tokens: resultado de pe.tokenizar(codigo, 'codigo')
            padroes: resultado de pe.extrair_padroes(tokens)
            linguagem: 'lua' | 'texto'
        
        Returns:
            (esqueleto: str, blanks: list) — esqueleto com @BLANK_N e lista de blanks
        """
        self._prox_blank = 1
        n_gramas = padroes.get('n_gramas', {})
        markov = padroes.get('markov', {})
        
        if linguagem == 'lua':
            return self._construir_lua(tokens, n_gramas, markov)
        else:
            return self._construir_texto(tokens, n_gramas, markov)
    
    def _construir_lua(self, tokens, n_gramas, markov):
        """Constrói esqueleto Lua dos tokens."""
        linhas = []
        blanks = []
        i = 0
        
        # Extrai tipos de token para formar trigramas
        tipos = [t[0] for t in tokens] if tokens else []
        
        while i < len(tipos):
            # Tenta match de trigrama (3 tokens consecutivos)
            trigrama = tuple(tipos[i:i+3])
            if len(trigrama) == 3 and trigrama in self._PADROES_LINGUAGEM:
                templates = self._PADROES_LINGUAGEM[trigrama]
                for tmpl in templates:
                    linha, novos_blanks = self._preencher_template(tmpl)
                    linhas.append(linha)
                    blanks.extend(novos_blanks)
                i += 3
                continue
            
            # Tenta bigrama
            bigrama = tuple(tipos[i:i+2])
            if len(bigrama) == 2 and bigrama in self._PADROES_LINGUAGEM:
                templates = self._PADROES_LINGUAGEM[bigrama]
                for tmpl in templates:
                    linha, novos_blanks = self._preencher_template(tmpl)
                    linhas.append(linha)
                    blanks.extend(novos_blanks)
                i += 2
                continue
            
            # Token único — usa o valor real se disponível
            if i < len(tokens):
                tipo, valor = tokens[i]
                if tipo in ('AST', 'KW'):
                    linhas.append(f"-- {tipo}: {valor}")
                elif tipo == 'INDENT':
                    pass  # ignoramos indentação no esqueleto
                elif tipo == 'FUNC_SIZE':
                    linhas.append(f"-- [funcao: {valor} linhas]")
                else:
                    linhas.append(f"-- {tipo}")
            i += 1
        
        esqueleto = '\n'.join(linhas)
        return esqueleto, blanks
    
    def _construir_texto(self, tokens, n_gramas, markov):
        """Constrói esqueleto de texto dos tokens."""
        linhas = []
        blanks = []
        
        # Extrai tipos
        tipos = [t[0] for t in tokens] if tokens else []
        
        for tipo in tipos:
            if tipo == 'FIM_FRASE':
                linhas.append('@BLANK_FRASE.')
                blanks.append('@BLANK_FRASE')
            elif tipo == 'ACAO':
                linhas.append('@BLANK_ACAO')
                blanks.append('@BLANK_ACAO')
            elif tipo.startswith('PAL_'):
                if linhas and not linhas[-1].startswith('@BLANK'):
                    linhas.append('@BLANK_OBJETO')
                    blanks.append('@BLANK_OBJETO')
                elif not linhas:
                    linhas.append('@BLANK_OBJETO')
                    blanks.append('@BLANK_OBJETO')
            elif tipo == 'PAUSA':
                pass  # ignoramos pausas no esqueleto
        
        esqueleto = ' '.join(linhas)
        return esqueleto, list(set(blanks))
    
    def _preencher_template(self, template):
        """Preenche um template com @BLANK_N únicos."""
        blanks_encontrados = re.findall(r'@BLANK_\w+', template)
        novos_blanks = []
        
        for blank_original in blanks_encontrados:
            # Gera ID único
            novo_blank = f'@BLANK_{self._prox_blank}'
            self._prox_blank += 1
            template = template.replace(blank_original, novo_blank, 1)
            novos_blanks.append(novo_blank)
        
        return template, novos_blanks

    def _extrair_ctx_original(self, tokens, blank_tipo):
        """Extrai contexto de um token específico para ajudar no preenchimento."""
        for tipo, valor in (tokens or []):
            if tipo == blank_tipo and isinstance(valor, str) and len(valor) > 2:
                return valor
        return f"({blank_tipo})"


# ============================================================
# MOTOR OMNIDIRECIONAL
# ============================================================
class PatternOmni:
    """Ciclo PatternEngine Omnidirecional.
    
    Analisa → Executa ferramenta → Re-analisa → ...
    Até entropia < 0.3 ou MAX_CICLOS.
    """
    
    MAX_CICLOS = 8
    ENTROPIA_LIMIAR = 0.35  # abaixo disso = padrão estabilizado
    
    def __init__(self):
        self.pe = PatternEngine()
        self.tools = ToolOrchestrator()
        self.kg = KnowledgeGraph()
        self.ie = IntentionEngine(pe=self.pe)
        self.esqueleto_builder = EsqueletoBuilder()
        
        self.contexto = []
        self.historico_ciclos = []
        self.ferramentas_executadas = []
        self.chamadas_llm = 0  # simuladas (contadas, não executadas)
    
    def processar(self, texto):
        """Processa uma entrada e retorna resultado completo."""
        print(f"\n{'='*70}")
        print(f"  PATTERN OMNIDIRECIONAL — PROTÓTIPO")
        print(f"{'='*70}")
        print(f"\n  Entrada: {texto}")
        
        self.contexto = [f"[INPUT] {texto}"]
        self.historico_ciclos = []
        self.ferramentas_executadas = []
        self.chamadas_llm = 0
        
        # Passo 0: IntentionEngine detecta intenção
        intencoes = self.ie.detectar(texto)
        if intencoes:
            cat, params, conf = intencoes[0]
            print(f"  Intenção: {cat} (conf={conf:.2f}) params={params}")
        else:
            cat, params = "GERAL", {}
            print(f"  Intenção: GERAL (não detectada)")
        
        # ============================================================
        # CICLO OMNIDIRECIONAL
        # ============================================================
        for ciclo in range(1, self.MAX_CICLOS + 1):
            ctx_str = '\n'.join(self.contexto[-5:])  # últimos 5 blocos
            
            # 1. PatternEngine analisa contexto ATUAL
            tokens = self.pe.tokenizar(ctx_str, 'texto')
            padroes = self.pe.extrair_padroes(tokens)
            entropia = padroes.get('entropia', 1.0)
            n_gramas = padroes.get('n_gramas', {})
            markov = padroes.get('markov', {})
            
            # 2. Gera fingerprint + eixo
            fp = self.pe.fingerprint(tokens)
            eixo = self.pe.eixo_nirvana_caos(tokens)
            
            # 3. Checa se entropia estabilizou
            direcao = "⬇️" if (len(self.historico_ciclos) > 0 and 
                               entropia < self.historico_ciclos[-1].get('entropia', 1.0)) else "⬆️"
            
            print(f"\n{'─'*70}")
            print(f"  CICLO {ciclo}/{self.MAX_CICLOS} | entropia: {entropia:.3f} {direcao} | eixo: {eixo:.3f}")
            print(f"{'─'*70}")
            
            if ciclo == 1 and n_gramas:
                top_ngramas = list(n_gramas.items())[:5]
                for ngrama, freq in top_ngramas:
                    print(f"    n-grama: {ngrama} (freq={freq})")
            
            # Registra ciclo
            self.historico_ciclos.append({
                'ciclo': ciclo,
                'entropia': entropia,
                'eixo': eixo,
                'n_gramas': list(n_gramas.keys())[:3] if n_gramas else [],
                'markov': {k: list(v.keys())[:2] for k, v in markov.items()} if markov else {},
            })
            
            # 4. Entropia baixa + eixo alto = PADRÃO ESTABILIZADO
            if entropia < self.ENTROPIA_LIMIAR and eixo > 0.5:
                print(f"\n  ✅ PADRÃO ESTABILIZADO em {ciclo} ciclo(s)!")
                print(f"     Entropia {entropia:.3f} < {self.ENTROPIA_LIMIAR} | Eixo {eixo:.3f} > 0.5")
                break
            
            # 5. Markov sugere PRÓXIMA AÇÃO
            acao = self._markov_para_acao(markov, tokens, cat, params)
            
            if not acao:
                print(f"     Markov: sem sugestão clara — usando fallback")
                acao = self._fallback_acao(cat, params, ciclo)
            
            # 6. Executa ação
            resultado = self._executar_acao(acao)
            
            if resultado:
                self.contexto.append(f"[RESULTADO DE {acao['ferramenta']}]\n{resultado}")
                self.ferramentas_executadas.append(acao)
                print(f"\n     → Executou: {acao['ferramenta']}({acao.get('params', {})})")
                print(f"     → Resultado: {len(resultado.split(chr(10)))} linhas, {len(resultado)} chars")
            else:
                print(f"\n     → {acao['ferramenta']}: sem resultados (vazio)")
        
        # ============================================================
        # PÓS-CICLO: Constrói saída
        # ============================================================
        print(f"\n{'='*70}")
        print(f"  CONSTRUINDO SAÍDA")
        print(f"{'='*70}")
        
        resultado_final = self._construir_saida(texto, cat, params)
        
        print(f"\n{'='*70}")
        print(f"  RESUMO")
        print(f"{'='*70}")
        print(f"  Ciclos: {len(self.historico_ciclos)}")
        print(f"  Ferramentas executadas: {len(self.ferramentas_executadas)}")
        for f in self.ferramentas_executadas:
            print(f"    - {f['ferramenta']}({f.get('params', {})})")
        print(f"  Chamadas LLM (simuladas): {self.chamadas_llm}")
        print(f"  Entropia final: {self.historico_ciclos[-1].get('entropia', 1.0):.3f}")
        print(f"  Eixo final: {self.historico_ciclos[-1].get('eixo', 0):.3f}")
        print(f"  Saída gerada: {len(resultado_final)} chars")
        
        return resultado_final
    
    def _markov_para_acao(self, markov, tokens, cat, params):
        """Markov chain sugere a PRÓXIMA ação baseada nos tokens atuais."""
        if not tokens:
            return None
        
        # Tenta encontrar o último tipo de token com transições
        tipos = [t[0] for t in tokens] if tokens else []
        if not tipos:
            return None
        
        ultimo_tipo = tipos[-1] if tipos else 'ACAO'
        
        # Markov chain: dado o último tipo, qual o próximo?
        if ultimo_tipo in markov:
            transicoes = markov[ultimo_tipo]
            if transicoes:
                # Pega a transição mais provável
                melhor_prox = max(transicoes, key=transicoes.get)
                
                # Mapa: token → ferramenta
                if melhor_prox in ('ACAO', 'PAL_LONGA'):
                    if cat == 'CREATE':
                        return {'ferramenta': 'buscar_estrategico', 
                                'params': {'termo': params.get('tipo', params.get('termo', '')) or 'NPC'}}
                    elif cat == 'EXPLAIN':
                        return {'ferramenta': 'buscar_kg',
                                'params': {'termo': params.get('termo', '') or 'SPA'}}
                    else:
                        return {'ferramenta': 'buscar_estrategico',
                                'params': {'termo': params.get('termo', '') or 'MCR'}}
                
                elif melhor_prox == 'PAL_MEDIA':
                    return {'ferramenta': 'ler_arquivo',
                            'params': {'path': self._encontrar_arquivo_lido()}}
        
        # Se tem ACAO nos tokens, busca dados
        if 'ACAO' in tipos:
            if cat in ('CREATE', 'SEARCH'):
                return {'ferramenta': 'buscar_estrategico',
                        'params': {'termo': params.get('tipo', params.get('termo', '')) or 'NPC'}}
            else:
                return {'ferramenta': 'buscar_kg',
                        'params': {'termo': params.get('termo', '') or 'MCR'}}
        
        return None
    
    def _fallback_acao(self, cat, params, ciclo):
        """Ação de fallback se Markov não sugerir nada."""
        acoes = [
            {'ferramenta': 'buscar_estrategico', 'params': {'termo': 'NPC'}},
            {'ferramenta': 'buscar_estrategico', 'params': {'termo': 'SPA'}},
            {'ferramenta': 'buscar_kg', 'params': {'termo': 'MCR'}},
            {'ferramenta': 'ler_arquivo', 'params': {'path': 'docs/MCR_IDENTITY.md'}},
        ]
        idx = min(ciclo - 1, len(acoes) - 1)
        return acoes[idx]
    
    def _executar_acao(self, acao):
        """Executa uma ação e retorna resultado."""
        if not acao:
            return ""
        
        ferramenta = acao.get('ferramenta', '')
        params = acao.get('params', {})
        
        try:
            if ferramenta == 'buscar_estrategico':
                termo = params.get('termo', '')
                if self.tools and hasattr(self.tools, 'executar'):
                    r = self.tools.executar('buscar_estrategico', {'termo': termo})
                    if r and r.get('sucesso'):
                        txt = str(r.get('resultado', ''))
                        if txt and 'Nenhum' not in txt and len(txt) > 30:
                            return txt[:2000]
                return ""
            
            elif ferramenta == 'buscar_kg':
                termo = params.get('termo', '')
                if self.kg and hasattr(self.kg, 'buscar'):
                    lessons = self.kg.buscar(termo, max_r=3)
                    if lessons:
                        partes = []
                        for l in lessons[:3]:
                            sol = l.get('solucao', '').strip()
                            if sol:
                                partes.append(f"- {sol[:200]}")
                        return '\n'.join(partes)
                return ""
            
            elif ferramenta == 'ler_arquivo':
                path = params.get('path', '')
                if not path:
                    return ""
                path_abs = os.path.join(BASE, path) if not os.path.isabs(path) else path
                if os.path.exists(path_abs):
                    with open(path_abs, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read()
                    return f"({len(conteudo)} chars, {len(conteudo.splitlines())} linhas):\n{conteudo[:2000]}"
                return f"(Arquivo nao encontrado: {path})"
            
        except Exception as e:
            return f"(Erro: {e})"
        
        return ""
    
    def _encontrar_arquivo_lido(self):
        """Encontra o primeiro path de arquivo no contexto."""
        for bloco in self.contexto:
            if '[RESULTADO DE buscar_estrategico' in bloco:
                # Tenta extrair path do resultado
                linhas = bloco.split('\n')
                for linha in linhas[:10]:
                    m = re.search(r'([\w/]+\.\w+)', linha)
                    if m:
                        return m.group(1)
        return 'docs/MCR_IDENTITY.md'
    
    def _construir_saida(self, texto, cat, params):
        """Constrói saída final baseada nos dados coletados.
        
        SEM LLM — usa PatternEngine para extrair estrutura + dados coletados.
        """
        saida = []
        saida.append(f"# Resultado: {cat}")
        saida.append(f"")
        saida.append(f"Baseado em {len(self.ferramentas_executadas)} ferramentas executadas:")
        
        for f in self.ferramentas_executadas:
            saida.append(f"- {f['ferramenta']}({f.get('params', {})})")
        
        saida.append(f"")
        
        # Tenta extrair/esqueleto se temos dados de código
        dados_codigo = None
        for bloco in self.contexto:
            if 'RESULTADO DE ler_arquivo' in bloco and '.lua' in bloco:
                # Extrai o código do resultado
                linhas = bloco.split('\n')
                # Pula o cabeçalho, pega o código
                codigo_linhas = [l for l in linhas[1:] if not l.startswith('(') or 'chars' not in l]
                dados_codigo = '\n'.join(codigo_linhas)
                break
        
        if dados_codigo and len(dados_codigo) > 50:
            # PatternEngine analisa o código real
            try:
                tokens_codigo = self.pe.tokenizar(dados_codigo, 'codigo')
                padroes_codigo = self.pe.extrair_padroes(tokens_codigo)
                
                esqueleto, blanks = self.esqueleto_builder.construir(
                    tokens_codigo, padroes_codigo, 'lua'
                )
                
                saida.append("## Esqueleto extraído do código real:")
                saida.append("")
                saida.append("```lua")
                saida.append(esqueleto)
                saida.append("```")
                saida.append("")
                saida.append(f"Blanks a preencher: {len(blanks)}")
                for b in blanks:
                    saida.append(f"- {b}")
                
                # Simula LLM para blanks criativos
                blanks_criativos = [b for b in blanks if 'NOME' in b or 'TITULO' in b or 'FRASE' in b]
                blanks_dados = [b for b in blanks if b not in blanks_criativos]
                
                if blanks_criativos:
                    self.chamadas_llm += len(blanks_criativos)
                    saida.append(f"")
                    saida.append(f"## Preenchimento (simulado):")
                    saida.append(f"")
                    saida.append(f"LLM usado para {len(blanks_criativos)} blanks criativos:")
                    for b in blanks_criativos:
                        saida.append(f"- {b} = [LLM geraria nome/diálogo]")
                    saida.append(f"")
                    saida.append(f"Ferramentas para {len(blanks_dados)} blanks de dados:")
                    for b in blanks_dados:
                        saida.append(f"- {b} = [buscar_estrategico/ler_arquivo preencheria]")
            except Exception as e:
                saida.append(f"(Erro ao gerar esqueleto: {e})")
        
        # Se for EXPLAIN, mostra dados do KG
        if cat == 'EXPLAIN':
            saida.append(f"")
            saida.append("## Dados do Knowledge Graph:")
            for bloco in self.contexto:
                if '[RESULTADO DE buscar_kg' in bloco:
                    saida.append(bloco)
        
        # Se for SEARCH, mostra resultados da busca
        if cat == 'SEARCH':
            saida.append(f"")
            saida.append("## Resultados da busca:")
            for bloco in self.contexto:
                if '[RESULTADO DE buscar_estrategico' in bloco:
                    saida.append(bloco)
        
        return '\n'.join(saida)


# ============================================================
# TESTES
# ============================================================
def testar(entrada):
    """Executa protótipo para uma entrada."""
    print(f"\n\n{'#'*70}")
    print(f"# TESTE: {entrada[:60]}")
    print(f"{'#'*70}")
    
    t0 = _time.time()
    
    omni = PatternOmni()
    resultado = omni.processar(entrada)
    
    tempo = round(_time.time() - t0, 1)
    
    # Salva resultado
    nome_arquivo = re.sub(r'[^a-zA-Z0-9]', '_', entrada[:30]).lower()
    out_path = os.path.join(BASE, 'sandbox', 'test_output', f'omni_{nome_arquivo}.txt')
    
    # Garante diretório
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"Entrada: {entrada}\n")
        f.write(f"Tempo: {tempo}s\n")
        f.write(f"Ciclos: {omni.historico_ciclos}\n")
        f.write(f"Ferramentas: {omni.ferramentas_executadas}\n")
        f.write(f"LLM: {omni.chamadas_llm} chamadas\n")
        f.write(f"{'='*70}\n")
        f.write(resultado)
    
    print(f"\nResultado salvo: sandbox/test_output/omni_{nome_arquivo}.txt")
    print(f"Tempo: {tempo}s | LLM: {omni.chamadas_llm} chamadas")
    
    return omni


if __name__ == '__main__':
    print("=" * 70)
    print("  PROTÓTIPO: PATTERN ENGINE OMNIDIRECIONAL")
    print("  Validando ciclo: analisa → executa → re-analisa → re-executa")
    print("  NÃO MODIFICA NADA NO MCR")
    print("=" * 70)
    
    entradas = [
        "Crie um NPC Ferreiro em Eridanus",
        "Explique o sistema SPA do MCR",
        "O que e Canary no contexto do MCR?",
    ]
    
    resultados = []
    for entrada in entradas:
        omni = testar(entrada)
        resultados.append({
            'entrada': entrada,
            'ciclos': len(omni.historico_ciclos),
            'ferramentas': len(omni.ferramentas_executadas),
            'llm': omni.chamadas_llm,
            'entropia_final': omni.historico_ciclos[-1].get('entropia', 1.0) if omni.historico_ciclos else 1.0,
            'eixo_final': omni.historico_ciclos[-1].get('eixo', 0) if omni.historico_ciclos else 0,
        })
    
    # Relatório final
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*70}")
    print(f"\n  {'Entrada':40s} {'Ciclos':7s} {'Ferr':5s} {'LLM':4s} {'Entropia':9s} {'Eixo':5s}")
    print(f"  {'-'*40} {'-'*7} {'-'*5} {'-'*4} {'-'*9} {'-'*5}")
    
    for r in resultados:
        print(f"  {r['entrada'][:40]:40s} {r['ciclos']:7d} {r['ferramentas']:5d} {r['llm']:4d} {r['entropia_final']:.3f}  {r['eixo_final']:.3f}")
    
    print(f"\n  {'='*70}")
    print(f"  LEGENDA:")
    print(f"  - entropia < 0.35 = padrão estabilizado (ciclo ideal)")
    print(f"  - eixo > 0.6 = padrão de qualidade")
    print(f"  - LLM = chamadas criativas necessárias (nomes, diálogos)")
    print(f"  - Ferramentas = execuções 0 IA (buscar, ler, escrever)")
    print(f"  {'='*70}")
