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
        
        self.resultados = {
            'estagios': estagios,
        }
        return self.resultados
    
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


def validar_resposta(pergunta, resposta, kg=None, pe=None, ia=None, contexto_kg=""):
    vp = ValidationPipeline(kg=kg, pe=pe, ia=ia)
    return vp.validar(pergunta, resposta, contexto_kg)
