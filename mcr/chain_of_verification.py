#!/usr/bin/env python3
"""chain_of_verification.py — Verifica respostas do LLM contra o KG.

Gera perguntas de verificacao a partir da resposta,
consulta o KG (via Metacognicao ou busca direta),
e se alguma verificacao falhar, sinaliza para re-geracao.

Uso:
    verificador = ChainOfVerification()
    resultado = verificador.verificar("Resposta gerada pelo LLM")
    if not resultado['valida']:
        print("Alucinacao detectada:", resultado['falhas'])
"""
import re, json
from typing import Dict, List


class ChainOfVerification:
    """Verifica resposta do LLM contra o Knowledge Graph."""

    def __init__(self):
        self._stats = {'total': 0, 'ok': 0, 'falhas': 0}

    def verificar(self, pergunta: str, resposta: str) -> Dict:
        """Verifica resposta contra o KG.

        Args:
            pergunta: pergunta original do usuario
            resposta: resposta gerada pelo LLM

        Returns:
            dict com valida, falhas, confianca_media, perguntas_geradas
        """
        self._stats['total'] += 1

        # 1. Extrai termos e frases verificaveis da resposta
        termos = self._extrair_termos(resposta)
        perguntas = self._gerar_perguntas(pergunta, resposta, termos)

        # 2. Verifica cada pergunta contra o KG
        falhas = []
        confiancas = []

        for pq in perguntas:
            resultado = self._consultar_kg(pq['termo'], pq['pergunta'])
            confiancas.append(resultado['confianca'])
            if not resultado['valido']:
                falhas.append({
                    'termo': pq['termo'],
                    'contexto': pq['contexto'],
                    'confianca': resultado['confianca'],
                    'msg': resultado['msg'],
                })

        confianca_media = sum(confiancas) / max(len(confiancas), 1)
        valida = len(falhas) == 0

        if not valida:
            self._stats['falhas'] += 1
        else:
            self._stats['ok'] += 1

        return {
            'valida': valida,
            'falhas': falhas,
            'n_falhas': len(falhas),
            'confianca_media': round(confianca_media, 3),
            'perguntas_geradas': len(perguntas),
            'termos_extraidos': termos,
        }

    def _extrair_termos(self, texto: str) -> List[str]:
        """Extrai termos verificaveis (entidades, conceitos) do texto."""
        palavras = re.findall(r'\b[A-Z][a-zA-ZÀ-ÿ]{2,}\b', texto)
        return list(set(palavras))[:10]  # max 10 termos

    def _gerar_perguntas(self, pergunta: str, resposta: str, termos: List[str]) -> List[Dict]:
        """Gera perguntas de verificacao baseadas na resposta."""
        perguntas = []

        # Pergunta sobre o tema central (similaridade com a pergunta)
        perguntas.append({
            'termo': pergunta[:50],
            'pergunta': pergunta,
            'contexto': 'tema central',
        })

        # Perguntas sobre entidades com letra maiuscula
        for termo in termos[:5]:
            perguntas.append({
                'termo': termo,
                'pergunta': f"O que e {termo}?",
                'contexto': f'entidade {termo}',
            })

        # Extras: frases longas que parecem afirmacoes
        frases = re.split(r'[.!?]+', resposta)
        for frase in frases:
            frase = frase.strip()
            if 20 < len(frase) < 100:
                # Verifica se a frase contem uma afirmacao verificavel
                palavras_frase = re.findall(r'\b[a-zA-ZÀ-ÿ_0-9]{2,}\b', frase)
                if len(palavras_frase) >= 3:
                    perguntas.append({
                        'termo': ' '.join(palavras_frase[:5]),
                        'pergunta': frase[:100],
                        'contexto': 'afirmacao',
                    })

        return perguntas[:8]  # max 8 perguntas

    def verificar_coerencia_estrutural(self, texto: str) -> Dict:
        """Verifica coerencia estrutural do texto gerado.

        - Se termina com pontuacao adequada (. ! ?)
        - Se ha frases truncadas no final
        - Se a entropia media do texto esta dentro do esperado

        Returns:
            dict com valido, erros, sugestao
        """
        if not texto:
            return {'valido': False, 'erros': ['texto vazio'], 'sugestao': 'regenerar'}

        erros = []

        # 1. Verifica finalizacao
        texto_limpo = texto.strip()
        if texto_limpo and texto_limpo[-1] not in ('.', '!', '?'):
            erros.append('texto nao termina com pontuacao adequada')

        # 2. Verifica frases truncadas (ultima frase sem verbo ou muito curta)
        frases = re.split(r'[.!?]', texto_limpo)
        if frases:
            ultima = frases[-1].strip()
            if 3 < len(ultima) < 15:
                erros.append('ultima frase parece truncada')

        # 3. Verifica entropia local (picos anomalos indicam perda de coerencia)
        entropias = []
        for frase in frases:
            if len(frase) > 10:
                try:
                    from mcr.ensemble_7b import _entropia
                    entropias.append(_entropia(frase))
                except Exception:
                    entropias.append(0.0)

        if entropias:
            h_media = sum(entropias) / len(entropias)
            picos = [h for h in entropias if h > h_media * 1.5]
            if len(picos) > len(entropias) // 3:
                erros.append(f'{len(picos)}/{len(entropias)} frases com entropia anomala')

        # 4. Verifica campos obrigatorios (se parece um formulario)
        campos_esperados = ['NOME:', 'HISTORIA:', 'FALA_']
        for campo in campos_esperados:
            if campo in texto.upper():
                break
        else:
            # So reporta se faltam campos quando o texto parece estruturado
            if 'NOME:' in texto.upper() or 'HISTORIA:' in texto.upper():
                erros.append('campos obrigatorios ausentes no formato esperado')

        return {
            'valido': len(erros) == 0,
            'erros': erros,
            'n_erros': len(erros),
            'sugestao': 'regenerar com temperatura mais baixa' if erros else 'ok',
        }

    def _consultar_kg(self, termo: str, pergunta_verif: str) -> Dict:
        """Consulta o KG para verificar um termo.

        Usa Metacognicao se disponivel, ou busca simples por similaridade.
        """
        # Tenta Metacognicao primeiro
        try:
            from mcr.metacognicao import Metacognicao
            meta = Metacognicao()
            score, justificativa = meta.calcular_confianca(termo)
            return {
                'valido': score >= 0.3,
                'confianca': score,
                'msg': f"confianca KG: {score:.2f} ({justificativa})",
            }
        except Exception:
            pass

        # Fallback: busca no cache/similaridade
        try:
            from devia.kernel.mcr_kernel.signature import raw_token_set
            from mcr.cache_hierarquico import CacheHierarquico
            cache = CacheHierarquico()
            resp = cache.buscar(pergunta_verif)
            if resp:
                tokens_resp = raw_token_set(resp)
                tokens_termo = raw_token_set(termo)
                if tokens_resp and tokens_termo:
                    inter = tokens_resp & tokens_termo
                    uniao = tokens_resp | tokens_termo
                    sim = len(inter) / len(uniao) if uniao else 0
                    return {
                        'valido': sim >= 0.15,
                        'confianca': sim,
                        'msg': f"similaridade: {sim:.2f}",
                    }
        except Exception:
            pass

        return {
            'valido': True,  # sem KG, assume valido
            'confianca': 0.5,
            'msg': 'KG indisponivel, assumindo valido',
        }

    def corrigir(self, pergunta: str, resposta: str, contexto_extra: str = '') -> str:
        """Tenta corrigir resposta com base em falhas de verificacao.

        Retorna a resposta original se nao houver falhas,
        ou uma versao corrigida com contexto adicional.
        """
        resultado = self.verificar(pergunta, resposta)

        if resultado['valida']:
            return resposta  # ja esta valida

        # Se falhou, adiciona contexto corretivo
        falhas_str = '; '.join([f.get('msg', '') for f in resultado['falhas']])
        prompt_correcao = (
            f"Resposta original:\n{resposta}\n\n"
            f"Problemas detectados:\n{falhas_str}\n\n"
            f"{contexto_extra}"
            f"Corrija a resposta acima com base nas informacoes fornecidas. "
            f"Seja conciso e factual."
        )

        try:
            import urllib.request, json
            payload = json.dumps({
                "model": "qwen2.5-coder:7b-32k",
                "prompt": prompt_correcao,
                "stream": False,
                "options": {"num_predict": 1024, "temperature": 0.2}
            }).encode()
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                return result.get("response", resposta)
        except Exception:
            return resposta  # fallback: resposta original

    def estatisticas(self) -> Dict:
        return self._stats
