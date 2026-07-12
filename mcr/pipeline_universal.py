#!/usr/bin/env python3
"""
mcr.pipeline_universal — Pipeline de 6 estágios para QUALQUER domínio.

╔══════════════════════════════════════════════════════════╗
║   FILOSOFIA MCR — LER ANTES DE MODIFICAR                ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   1. TUDO é transição entre dois estados consecutivos   ║
║   2. ENTROPIA descobre estrutura vs ruído               ║
║   3. MESMO motor, N domínios — só tokenizador muda      ║
║   4. Template + gaps (fixo + variável)                  ║
║   5. Fecha o loop: gerar → validar → aprender           ║
║   6. MCR descobre seus próprios níveis                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
import sys, os, math, random, json, time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from collections import Counter

sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\MCR\prototypes\mcr-universal')

# ─── MCR Core ──────────────────────────────────────────────
from devia.kernel.mcr_kernel.engine import MCR
from devia.kernel.mcr_kernel.decisor import (
    MCRThreshold, MCRDecisor, MCRPesoNota, MCREntropia
)
from devia.kernel.mcr_kernel.signature import MCRSignature, MCRFingerprint
from devia.kernel.mcr_kernel.meta import MCRMetaNivel
from devia.kernel.mcr_kernel.evolution import MCRAutoMelhoria

from mcr_universal.core.signature import MCRSignatureExpansiva
from mcr.template_entropico import extrair_template_entropico, gerar_do_template, resumir_template


# ─── Diretorio de output ───────────────────────────────────

_OUTPUT_DIR = Path(r'E:\MCR\poc_output\pipeline_universal')
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ─── Pipeline Universal ────────────────────────────────────


class PipelineUniversal:
    """Pipeline de 6 estágios para QUALQUER domínio.

    Uso:
        pipe = PipelineUniversal()
        pipe.registrar('sprite', tokenizer=..., validator=..., builder=...)
        resultado = pipe.executar(dados, 'sprite')
    """

    def __init__(self):
        # Motor MCR universal
        self.mcr = MCR('pipeline_universal')

        # Thresholds adaptativos (auto-descoberta)
        self.th_limiar_template = MCRThreshold('pp_limiar_template')
        self.th_temp_geracao = MCRThreshold('pp_temp_geracao')
        self.th_temp_filler = MCRThreshold('pp_temp_filler')
        self.th_aceitacao = MCRThreshold('pp_aceitacao')

        # Decisor (aprende fluxo)
        self.decisor = MCRDecisor('pp_decisor')

        # PesoNota (nota composta)
        self.peso_nota = MCRPesoNota('pp_peso_nota')

        # Entropia (detecta loops)
        self.entropia = MCREntropia('pp_entropia')

        # Auto-melhoria
        self.auto_melhoria = None

        # Dominios registrados
        self.dominios: Dict[str, dict] = {}

        # Contexto (sequencias aprendidas)
        self._contexto: Dict[str, List] = {}

        # Semente fixa
        random.seed(42)

    # ─── Registro de domínios ─────────────────────────────

    def registrar(self, nome: str, config: dict):
        """Registra um domínio no pipeline.

        Config:
            tokenizer: Callable[[Any], List[str]] — dados → sequência de tokens
            validator: Callable[[Any], dict] — saída → {'score': float}
            builder: Callable[[Any, str], None] — saída + path → salva
            descricao: str (opcional)
            template_engine: Callable (opcional, default=extrair_template_entropico)
            filler: Callable (opcional, default=gerar_do_template)
            filler_deterministico: Callable (opcional)
        """
        self.dominios[nome] = {
            'tokenizer': config.get('tokenizer', lambda d: [str(d)]),
            'validator': config.get('validator', lambda s: {'score': 0.0}),
            'builder': config.get('builder', lambda s, p: None),
            'template_engine': config.get('template_engine', extrair_template_entropico),
            'filler': config.get('filler', gerar_do_template),
            'filler_deterministico': config.get('filler_deterministico'),
            'descricao': config.get('descricao', nome),
            'loader': config.get('loader'),
        }
        self._contexto[nome] = []

        # Alimentar decisor
        self.decisor.aprender(f'registrar_{nome}', nome, True)

        return self

    # ─── Pipeline de 6 estágios ───────────────────────────

    def executar(
        self,
        dados: Any,
        dominio: str = 'texto',
        n_gerar: int = 5,
        salvar: bool = True,
        verbose: bool = False,
    ) -> Dict:
        """Executa pipeline completo para um domínio.

        Args:
            dados: dados de entrada (ou nome da categoria/caminho)
            dominio: domínio registrado
            n_gerar: quantas saídas gerar
            salvar: salvar resultados
            verbose: log detalhado

        Returns:
            dict com status, score, arquivos, descobertas
        """
        if dominio not in self.dominios:
            return {'status': 'erro', 'erro': f'Dominio {dominio} nao registrado'}

        cfg = self.dominios[dominio]
        t0 = time.time()
        descobertas = {}

        if verbose:
            print(f'\n[PipelineUniversal] Executando dominio={dominio}')

        # ─── Estágio 1: LOAD ───────────────────────────────
        if verbose:
            print(f'  [1/6] Load...')

        raw_data = dados
        if cfg.get('loader'):
            try:
                raw_data = cfg['loader'](dados)
            except Exception as e:
                if verbose:
                    print(f'  [1/6] Loader fallback: {e}')

        # ─── Estágio 2: TOKENIZE ───────────────────────────
        if verbose:
            print(f'  [2/6] Tokenize...')

        tokenizer = cfg['tokenizer']
        todas_sequencias = []
        if isinstance(raw_data, list):
            todas_sequencias = [tokenizer(item) for item in raw_data]
            self.mcr.aprender_batch(todas_sequencias)
        else:
            seq = tokenizer(raw_data)
            todas_sequencias = [seq]
            self.mcr.aprender_batch([seq])

        if not todas_sequencias:
            todas_sequencias = [['F']]

        # Alimentar contexto
        self._contexto[dominio].extend(todas_sequencias)
        if len(self._contexto[dominio]) > 50:
            self._contexto[dominio] = self._contexto[dominio][-50:]

        # MCRMetaNivel: descobrir niveis automaticamente
        try:
            meta_nivel = MCRMetaNivel()
            for s in todas_sequencias[:3]:
                meta_nivel.alimentar((' '.join(s)).encode('utf-8'))
            diagnostico_niveis = meta_nivel.diagnosticar()
            if verbose:
                print(f'  [2/6] MetaNiveis: {diagnostico_niveis}')
            descobertas['meta_niveis'] = diagnostico_niveis
        except Exception as e:
            if verbose:
                print(f'  [2/6] MetaNivel fallback: {e}')
            descobertas['meta_niveis'] = {'erro': str(e)}

        # Fingerprint para entropia
        for s in todas_sequencias[:3]:
            fp_str = '|'.join(s[:10])
            self.entropia.alimentar(str(hash(fp_str)))

        total_tokens = sum(len(s) for s in todas_sequencias)
        unicos = len(set(t for s in todas_sequencias for t in s))

        if verbose:
            print(f'  [2/6] {len(todas_sequencias)} sequencias, '
                  f'{total_tokens} tokens, {unicos} unicos')

        descobertas['estagio2'] = {
            'n_sequencias': len(todas_sequencias),
            'n_tokens': total_tokens,
            'unicos': unicos,
        }

        # ─── Estágio 3: TEMPLATE (extrair estrutura) ──────
        if verbose:
            print(f'  [3/6] Template...')

        limiar = self.th_limiar_template.obter(f'limiar_{dominio}', 0.5)

        if len(todas_sequencias) >= 2:
            try:
                # Padding: todas as sequencias com mesmo comprimento
                max_len = max(len(s) for s in todas_sequencias) if todas_sequencias else 1
                seqs_padded = [s + ['F'] * (max_len - len(s)) for s in todas_sequencias]
                template = cfg['template_engine'](seqs_padded, limiar)
                resumo = resumir_template(template)
                if verbose:
                    print(f'  [3/6] {resumo}')
                descobertas['estagio3'] = {
                    'tipo': 'entropico',
                    'limiar': limiar,
                    'resumo': resumo,
                }
            except Exception as e:
                template = None
                if verbose:
                    print(f'  [3/6] Template fallback: {e}')
                descobertas['estagio3'] = {'tipo': 'fallback', 'erro': str(e)}
        else:
            template = None
            descobertas['estagio3'] = {'tipo': 'unica_sequencia'}

        # ─── Estágio 4: FILL (gerar) ───────────────────────
        if verbose:
            print(f'  [4/6] Fill...')

        temp = self.th_temp_geracao.obter(f'temp_{dominio}', 0.8)
        saidas = []

        for i in range(n_gerar):
            if template:
                # Verificar se template tem estrutura fixa
                if isinstance(template, dict):
                    n_fixos = sum(1 for p in template.values() 
                                  if isinstance(p, tuple) and p[0] == 'fixo')
                elif isinstance(template, list):
                    n_fixos = sum(1 for p in template 
                                  if isinstance(p, tuple) and p[0] == 'fixo')
                else:
                    n_fixos = 0
                
                if n_fixos > 0:
                    # Template com estrutura: gerar do template
                    nova_seq = cfg['filler'](template, temp)
                else:
                    # Template sem estrutura: gerar do MCR treinado
                    if todas_sequencias and todas_sequencias[0]:
                        semente = todas_sequencias[0][0]
                        max_len = max(len(s) for s in todas_sequencias) if todas_sequencias else 10
                        nova_seq = self.mcr.gerar(semente, max_len - 1)
                    else:
                        nova_seq = []
            elif todas_sequencias:
                semente = todas_sequencias[0][0] if todas_sequencias[0] else 'F'
                max_len = max(len(s) for s in todas_sequencias) if todas_sequencias else 10
                nova_seq = self.mcr.gerar(semente, max_len - 1)
            else:
                nova_seq = []

            saidas.append(nova_seq)

            # Alimentar entropia com cada saída
            fp_saida = '|'.join(nova_seq[:10]) if nova_seq else 'vazio'
            self.entropia.alimentar(str(hash(fp_saida)))

        if verbose:
            print(f'  [4/6] Geradas {len(saidas)} saidas, temp={temp:.2f}')

        descobertas['estagio4'] = {
            'n_geradas': len(saidas),
            'temperatura': temp,
            'usou_template': template is not None,
        }

        # ─── Estágio 5: VALIDATE ───────────────────────────
        if verbose:
            print(f'  [5/6] Validate...')

        validator = cfg['validator']
        scores = []
        for saida in saidas:
            try:
                resultado = validator(saida)
                scores.append(resultado.get('score', 0.0))
            except Exception as e:
                scores.append(0.0)

        score_medio = sum(scores) / len(scores) if scores else 0.0

        # Detectar loop
        em_loop = self.entropia.esta_em_loop()

        # PesoNota
        nota = self.peso_nota.calcular(
            byte_s=score_medio,
            palavra_s=1.0 - abs(sum(scores) - len(scores) * 0.5) / max(len(scores), 1) if scores else 0,
            token_s=1.0 if not em_loop else 0.3,
        )

        if verbose:
            print(f'  [5/6] Score medio={score_medio:.3f} notal={nota:.3f} loop={em_loop}')

        descobertas['estagio5'] = {
            'score_medio': round(score_medio, 4),
            'scores': [round(s, 4) for s in scores],
            'nota_mcr': round(nota, 4),
            'em_loop': em_loop,
        }

        # ─── Estágio 6: LEARN (aprender + persistir) ──────
        if verbose:
            print(f'  [6/6] Learn...')

        arquivos = []
        if salvar:
            builder = cfg['builder']
            ext = '.txt'
            if dominio == 'sprite':
                ext = '.png'
            elif dominio == 'audio':
                ext = '.wav'
            elif dominio == 'codigo':
                ext = '.lua'

            for i, saida in enumerate(saidas):
                path = str(_OUTPUT_DIR / f'{dominio}_{int(t0)}_{i}{ext}')
                try:
                    builder(saida, path)
                    arquivos.append(path)
                except Exception as e:
                    if verbose:
                        print(f'  [6/6] Builder fallback: {e}')

        # Alimentar auto-melhoria
        try:
            if self.auto_melhoria is None:
                self.auto_melhoria = MCRAutoMelhoria()
            self.auto_melhoria.ciclo()
        except Exception:
            pass

        # Aprender no decisor
        status = 'aceito' if nota > self.th_aceitacao.obter(f'aceite_{dominio}', 0.3) else 'rejeitado'
        self.decisor.aprender(f'resultado_{dominio}', status, nota > 0.5)

        if verbose:
            print(f'  [6/6] Status={status} arquivos={len(arquivos)}')
            print(f'  [PipelineUniversal] Concluido em {time.time()-t0:.2f}s')

        # Salvar relatório de descobertas
        relatorio = {
            'dominio': dominio,
            'status': status,
            'score': round(score_medio, 4),
            'nota': round(nota, 4),
            'em_loop': em_loop,
            'arquivos': arquivos,
            'descobertas': descobertas,
            'tempo': round(time.time() - t0, 2),
            'thresholds': {
                'limiar_template': limiar,
                'temp_geracao': temp,
                'aceitacao': self.th_aceitacao.obter(f'aceite_{dominio}', 0.3),
            },
        }

        if salvar:
            rel_path = str(_OUTPUT_DIR / f'relatorio_{dominio}_{int(t0)}.json')
            with open(rel_path, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            relatorio['relatorio_path'] = rel_path

        return relatorio

    # ─── Utilitários ──────────────────────────────────────

    def stats(self) -> Dict:
        return {
            'dominios': list(self.dominios.keys()),
            'contexto': {d: len(s) for d, s in self._contexto.items()},
            'entropia_loop': self.entropia.esta_em_loop(),
            'thresholds': {
                'limiar_template': self.th_limiar_template.calcular(1.0),
                'temp_geracao': self.th_temp_geracao.calcular(1.0),
            },
            'mcr': self.mcr.stats(),
        }


# ─── Função principal para CLI ─────────────────────────────


def main():
    """CLI: python -m mcr.pipeline_universal --dominio texto --dados 'hello world'"""
    import argparse
    parser = argparse.ArgumentParser(description='PipelineUniversal MCR')
    parser.add_argument('--dominio', default='texto', help='Dominio a executar')
    parser.add_argument('--dados', default='o rato roeu a roupa', help='Dados de entrada')
    parser.add_argument('--n', type=int, default=3, help='Numero de saidas')
    parser.add_argument('--verbose', action='store_true', help='Log detalhado')

    args = parser.parse_args()

    pipe = PipelineUniversal()

    # Registrar dominios padrao
    try:
        from mcr.dominios.texto import DOMINIO as dom_texto
        pipe.registrar('texto', dom_texto)
    except ImportError:
        pass

    resultado = pipe.executar(args.dados, args.dominio, args.n, verbose=args.verbose)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
