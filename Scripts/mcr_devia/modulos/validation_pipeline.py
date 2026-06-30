"""Validation Pipeline — Relator de FATOS. Sem thresholds, sem notas.
Cada estagio APENAS relata o que encontrou. Sem APROVADO/REPROVADO.
Quem decide e quem le o relatorio.

Estagios:
  V1: PatternChecker — similaridade entre resposta e KG
  V2: FactChecker — termos confirmados vs nao encontrados
  V3: CodeChecker — verifica arquivos citados
  V4: ConselhoChecker — IA avalia coerencia
  V5: AlucinacaoChecker — verifica termos proibidos
  V6: TruncationChecker — detecta resposta cortada
  V7: Especificidade — diagnostico de especificidade MCR
"""
import os, re, sys, json

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

_NOMES_ESTAGIOS = {
    'v1': 'PatternChecker',
    'v2': 'FactChecker',
    'v3': 'CodeChecker',
    'v4': 'ConselhoChecker',
    'v5': 'AlucinacaoChecker',
    'v6': 'TruncationChecker',
    'v7': 'Especificidade',
    'v8': 'Completude',
    'v9': 'SemanticChecker',
}


class ValidationPipeline:
    """7 estagios que APENAS relatam fatos. Sem thresholds, sem notas."""
    
    def __init__(self, kg=None, pe=None, ia=None):
        self.kg = kg
        self.pe = pe
        self.ia = ia
        self.resultados = {}
    
    def validar(self, pergunta, resposta, contexto_kg=""):
        """Executa todos os 7 estagios. Retorna relatorio de fatos."""
        self.resultados = {}
        estagios = []
        
        if not resposta or len(resposta) < 5:
            return {'estagios': [{'nome': 'PreCheck', 'status': 'INFO', 'detalhes': 'Resposta muito curta'}], 'total_falhas': 0}
        
        estagios.append(self._v1_pattern_checker(pergunta, resposta))
        estagios.append(self._v2_fact_checker(resposta, contexto_kg))
        estagios.append(self._v3_code_checker(resposta))
        estagios.append(self._v4_conselho_checker(pergunta, resposta))
        estagios.append(self._v5_alucinacao_checker(resposta))
        estagios.append(self._v6_truncation_checker(resposta))
        estagios.append(self._v7_especificidade(pergunta, resposta, contexto_kg))
        estagios.append(self._v8_completude(pergunta, resposta))
        estagios.append(self._v9_semantic_checker(pergunta, resposta))
        
        self.resultados = {
            'estagios': estagios,
            'nota_geral': self._calcular_nota(estagios),
        }
        return self.resultados
    
    def _calcular_nota(self, estagios):
        """Calcula nota geral 0-10 baseada nos estagios.
        
        Cada estagio contribui com uma pontuacao baseada em heuristicas:
        - V1: similaridade com KG (0-2 pontos)
        - V2: termos confirmados (0-2 pontos)
        - V3: arquivos citados (0-1 ponto)
        - V4: coerencia (0-1 ponto)
        - V5: alucinacoes (0-1 ponto)
        - V6: completude textual (0-1 ponto)
        - V7: especificidade MCR (0-1 ponto)
        - V8: decisao de completude (0-1 ponto)
        """
        nota = 5.0  # nota base neutra
        
        for e in estagios:
            nome = e.get('nome', '')
            detalhes = e.get('detalhes', '')
            
            if nome == 'PatternChecker':
                # Extrai similaridade
                import re as _re
                m = _re.search(r'[\d.]+', detalhes)
                if m:
                    sim = float(m.group())
                    nota += sim * 2  # 0 a 2 pontos
                    if sim > 0.8:
                        nota += 0.5
            
            elif nome == 'FactChecker':
                m = _re.search(r'(\d+)\s*termos', detalhes)
                if m:
                    n_termos = int(m.group(1))
                    nota += min(n_termos / 5, 2)  # 0 a 2 pontos
            
            elif nome == 'CodeChecker':
                if 'confirmados' in detalhes:
                    nota += 1  # 1 ponto se tem arquivos confirmados
            
            elif nome == 'ConselhoChecker':
                if 'aprovado' in detalhes.upper() or ('coerente' in detalhes.lower() and 'não' not in detalhes.lower() and 'nao' not in detalhes.lower()):
                    nota += 1
            
            elif nome == 'AlucinacaoChecker':
                if 'nenhum' in detalhes.lower():
                    nota += 1  # sem alucinacoes = +1
            
            elif nome == 'TruncationChecker':
                if 'completa' in detalhes.lower():
                    nota += 1
            
            elif nome == 'Especificidade':
                m = _re.search(r'(\d+)\s*arquivos', detalhes)
                if m:
                    nota += 0.5
                if 'arquivos:linhas' in detalhes:
                    nota += 0.5
            
            elif nome == 'Completude':
                decisao = e.get('decisao', '')
                if decisao == 'COMPLETO':
                    nota += 1
                elif decisao == 'CONTINUAR':
                    nota -= 0.5
            
            elif nome == 'SemanticChecker':
                # V9: penaliza se resposta nao cobre os termos da pergunta
                taxa = e.get('taxa_cobertura', 0.0)
                nota += min(taxa * 2.5, 2.5)  # 0 a 2.5 pontos (peso maior)
                if taxa < 0.3:
                    nota -= 1.5  # penalidade severa para respostas fora do contexto
                elif taxa < 0.5:
                    nota -= 0.5
        
        return round(max(0, min(10, nota)), 1)
    
    def _v1_pattern_checker(self, pergunta, resposta):
        """V1 - PatternChecker: similaridade entre resposta e KG. Apenas relata."""
        nome = _NOMES_ESTAGIOS['v1']
        if not self.kg or not self.pe:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'KG ou PE nao disponiveis'}
        
        try:
            lessons = self.kg.buscar_expandido(pergunta, max_r=5)
            if not lessons:
                return {'nome': nome, 'status': 'INFO', 'detalhes': 'Nenhuma lesson no KG para comparar'}
            
            tokens_resp = self.pe.tokenizar(resposta, 'texto')
            fp_resp = self.pe.fingerprint(tokens_resp)
            
            similaridades = []
            for l in lessons:
                texto_lesson = l.get('solucao', '') + ' ' + l.get('erro', '')
                tokens_lesson = self.pe.tokenizar(texto_lesson, 'texto')
                fp_lesson = self.pe.fingerprint(tokens_lesson)
                sim = self.pe.similaridade(fp_resp, fp_lesson)
                similaridades.append(sim)
            
            sim_media = sum(similaridades) / len(similaridades) if similaridades else 0
            return {'nome': nome, 'status': 'INFO', 'detalhes': f'Similaridade media com KG: {sim_media:.2f}'}
        except Exception as e:
            return {'nome': nome, 'status': 'INFO', 'detalhes': f'Erro: {e}'}
    
    def _v2_fact_checker(self, resposta, contexto_kg):
        """V2 - FactChecker: lista termos encontrados e nao encontrados no KG. Apenas relata."""
        nome = _NOMES_ESTAGIOS['v2']
        if not self.kg:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'KG nao disponivel'}
        
        try:
            termos = set(re.findall(r'[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,}){0,3}', resposta))
            if not termos:
                return {'nome': nome, 'status': 'INFO', 'detalhes': 'Nenhum termo para verificar'}
            
            encontrados = []
            nao_encontrados = []
            for termo in list(termos):
                if self.kg.buscar(termo, max_r=1):
                    encontrados.append(termo)
                elif hasattr(self.kg, 'buscar_expandido') and self.kg.buscar_expandido(termo, max_r=1):
                    encontrados.append(termo)
                else:
                    nao_encontrados.append(termo)
            
            detalhes = f'{len(encontrados)} termos confirmados no KG'
            if nao_encontrados:
                detalhes += f' | {len(nao_encontrados)} termos SEM confirmacao: {", ".join(nao_encontrados)}'
            return {'nome': nome, 'status': 'INFO', 'detalhes': detalhes}
        except Exception as e:
            return {'nome': nome, 'status': 'INFO', 'detalhes': f'Erro: {e}'}
    
    def _v3_code_checker(self, resposta):
        """V3 - CodeChecker: verifica arquivos citados. Apenas relata."""
        nome = _NOMES_ESTAGIOS['v3']
        
        refs_arquivos = re.findall(r'([a-zA-Z_][\w/]*\.(?:py|lua|cpp|h|hpp|txt|md))', resposta)
        refs_funcoes = re.findall(r'(?:metodo|funcao|função|classe)\s+([a-zA-Z_]\w*)', resposta)
        
        if not refs_arquivos and not refs_funcoes:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'Sem referencias a arquivos ou funcoes'}
        
        arquivos_ok = []
        arquivos_faltando = []
        for arq in refs_arquivos:
            caminhos = [
                os.path.join(BASE, 'Scripts', 'mcr_devia', arq),
                os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos', arq),
                os.path.join(BASE, 'Scripts', 'mcr_devia', 'comandos', arq),
            ]
            if any(os.path.exists(c) for c in caminhos):
                arquivos_ok.append(arq)
            else:
                arquivos_faltando.append(arq)
        
        detalhes = f'{len(arquivos_ok)} arquivos confirmados'
        if arquivos_faltando:
            detalhes += f' | {len(arquivos_faltando)} arquivos NAO encontrados: {", ".join(arquivos_faltando)}'
        if refs_funcoes:
            detalhes += f' | Funcoes mencionadas: {", ".join(refs_funcoes)}'
        return {'nome': nome, 'status': 'INFO', 'detalhes': detalhes}
    
    def _v4_conselho_checker(self, pergunta, resposta):
        """V4 - ConselhoChecker: IA avalia coerencia. Apenas relata."""
        nome = _NOMES_ESTAGIOS['v4']
        if not self.ia:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'IA nao disponivel'}
        
        try:
            prompt = (
                "[SISTEMA]\nAnalise a resposta abaixo. Ela e COERENTE com a pergunta?\n"
                "Tem contradicoes internas? Responda com ANALISE e VEREDITO.\n\n"
                f"[PERGUNTA]\n{pergunta}\n\n"
                f"[RESPOSTA]\n{resposta}\n\n"
                "[ANALISE]:"
            )
            veredito = self.ia.fast(prompt, 0.2, 'leve') or ''
            return {'nome': nome, 'status': 'INFO', 'detalhes': veredito.strip()}
        except Exception as e:
            return {'nome': nome, 'status': 'INFO', 'detalhes': f'Erro: {e}'}
    
    def _v5_alucinacao_checker(self, resposta):
        """V5 - AlucinacaoChecker: verifica termos suspeitos."""
        nome = _NOMES_ESTAGIOS['v5']
        return {'nome': nome, 'status': 'INFO', 'detalhes': 'Verificacao basica: sem heuristicas fixas'}
    
    def _v6_truncation_checker(self, resposta):
        """V6 - TruncationChecker: detecta se resposta parece cortada."""
        nome = _NOMES_ESTAGIOS['v6']
        problemas = []
        
        if resposta.strip().endswith('...') or resposta.strip().endswith('…'):
            problemas.append('Resposta termina com reticencias')
        
        if problemas:
            return {'nome': nome, 'status': 'INFO', 'detalhes': '; '.join(problemas)}
        return {'nome': nome, 'status': 'INFO', 'detalhes': 'Resposta parece completa'}
    
    def _v7_especificidade(self, pergunta, resposta, contexto_kg):
        """V7 - Especificidade: diagnostico de quao especifica e a resposta."""
        nome = _NOMES_ESTAGIOS['v7']
        detalhes = []
        
        refs_arquivos_linha = re.findall(r'[\w/]+\.\w+:\d+', resposta)
        refs_arquivos = re.findall(r'[\w/]+\.(?:py|lua|cpp|h|hpp)', resposta)
        refs_funcoes = re.findall(r'(?:def |funcao |função |metodo |classe )\w+', resposta)
        
        if refs_arquivos_linha:
            detalhes.append(f'{len(refs_arquivos_linha)} arquivos:linhas citados')
        if refs_arquivos:
            detalhes.append(f'{len(refs_arquivos)} arquivos citados')
        if refs_funcoes:
            detalhes.append(f'Funcoes: {", ".join(refs_funcoes)}')
        if not refs_arquivos and not refs_funcoes:
            detalhes.append('Sem referencias a codigo fonte')
        
        return {'nome': nome, 'status': 'INFO', 'detalhes': ' | '.join(detalhes)}
    
    def _v8_completude(self, pergunta, resposta):
        """V8 - Completude: resposta esta COMPLETA, precisa CONTINUAR, ou deve REFAZER?
        
        Usado no modo token-a-bloco para decidir o proximo passo.
        Retorna: COMPLETO (resposta finalizada)
                 CONTINUAR (falta conteudo)
                 REFAZER (ultimo bloco com problemas)
        """
        nome = _NOMES_ESTAGIOS.get('v8', 'Completude')
        
        if not resposta or len(resposta) < 20:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'CONTINUAR', 'decisao': 'CONTINUAR'}
        
        # Heuristica 1: termina com pontuacao final?
        if resposta.strip() and resposta.strip()[-1] not in '.!?)]}\'"':
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'CONTINUAR (sem pontuacao final)', 'decisao': 'CONTINUAR'}
        
        # Heuristica 2: tem reticencias no final (cortado)?
        if resposta.strip().endswith('...') or resposta.strip().endswith('…'):
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'CONTINUAR (reticencias)', 'decisao': 'CONTINUAR'}
        
        # Heuristica 3: parece uma frase incompleta?
        ultima_frase = resposta.strip()
        if '.' in resposta:
            ultima_frase = resposta.strip().rsplit('.', 1)[-1]
        if len(ultima_frase) < 15 and '?' not in ultima_frase:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'CONTINUAR (frase curta)', 'decisao': 'CONTINUAR'}
        
        # Se tem IA, pergunta se a pergunta foi totalmente respondida
        if self.ia:
            try:
                prompt = (
                    "[SISTEMA]\nA pergunta abaixo foi COMPLETAMENTE respondida?\n"
                    "Responda APENAS: COMPLETO, CONTINUAR ou REFAZER\n\n"
                    f"[PERGUNTA]\n{pergunta}\n\n"
                    f"[RESPOSTA ATUAL]\n{resposta}\n\n"
                    "[A resposta cobre todos os aspectos da pergunta? FALTA algo?]\n"
                    "[DECISAO]:"
                )
                decisao = self.ia.fast(prompt, 0.2, 'leve') or ''
                decisao = decisao.strip().upper()
                if 'COMPLETO' in decisao:
                    return {'nome': nome, 'status': 'INFO', 'detalhes': 'COMPLETO', 'decisao': 'COMPLETO'}
                elif 'REFAZER' in decisao:
                    return {'nome': nome, 'status': 'INFO', 'detalhes': 'REFAZER', 'decisao': 'REFAZER'}
                else:
                    return {'nome': nome, 'status': 'INFO', 'detalhes': 'CONTINUAR', 'decisao': 'CONTINUAR'}
            except Exception:
                pass
        
        # Fallback: se tem mais de 200 chars, considera completo
        if len(resposta) > 200:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'COMPLETO (fallback)', 'decisao': 'COMPLETO'}
        return {'nome': nome, 'status': 'INFO', 'detalhes': 'CONTINUAR (fallback)', 'decisao': 'CONTINUAR'}


    def _v9_semantic_checker(self, pergunta, resposta):
        """V9 - SemanticChecker: verifica se a resposta realmente RESPONDE a pergunta.
        
        Em vez de medir formato, mede se os termos-chave da pergunta
        aparecem na resposta. Se nao aparecem, a resposta e irrelevante.
        """
        nome = 'SemanticChecker'
        
        if not pergunta or not resposta:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'Sem dados',
                    'taxa_cobertura': 0.0, 'termos_pergunta': [], 'termos_resposta': []}
        
        # Extrai termos-chave da pergunta (palavras com 3+ letras, excluindo stop words)
        stop_words = {'que','para','com','uma','era','mais','como','por','seu','sua',
                      'tem','ela','ele','voce','qual','onde','quando','porque','este',
                      'essa','isto','como','sao','dos','das','nos','nas','em','no','na',
                      'de','da','do','e','o','a','os','as','um','uma','uns','umas'}
        
        palavras_pergunta = re.findall(r'[a-zA-Z]{3,}', pergunta.lower())
        palavras_resposta = re.findall(r'[a-zA-Z]{3,}', resposta.lower())
        
        termos_pergunta = [p for p in palavras_pergunta if p not in stop_words]
        termos_resposta_set = set(palavras_resposta)
        
        if not termos_pergunta:
            return {'nome': nome, 'status': 'INFO', 'detalhes': 'Pergunta sem termos para verificar',
                    'taxa_cobertura': 1.0, 'termos_pergunta': [], 'termos_resposta': []}
        
        # Termos encontrados na resposta
        encontrados = [t for t in termos_pergunta if t in termos_resposta_set]
        taxa = len(encontrados) / len(termos_pergunta) if termos_pergunta else 1.0
        
        # Detalhes
        detalhes = f'{len(encontrados)}/{len(termos_pergunta)} termos da pergunta na resposta ({taxa:.0%})'
        if taxa < 0.3:
            detalhes += ' | RESPOSTA FORA DO CONTEXTO: termos-chave da pergunta ausentes'
        elif taxa < 0.6:
            detalhes += ' | Cobertura parcial'
        else:
            detalhes += ' | Resposta contextualmente relevante'
        
        return {
            'nome': nome,
            'status': 'INFO',
            'detalhes': detalhes,
            'taxa_cobertura': taxa,
            'termos_pergunta': termos_pergunta,
            'termos_resposta': encontrados,
        }


def validar_resposta(pergunta, resposta, kg=None, pe=None, ia=None, contexto_kg=""):
    vp = ValidationPipeline(kg=kg, pe=pe, ia=ia)
    return vp.validar(pergunta, resposta, contexto_kg)
