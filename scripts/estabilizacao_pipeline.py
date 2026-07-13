#!/usr/bin/env python3
"""estabilizacao_pipeline.py — Monitora o pipeline integrado.

Executa baterias de perguntas, registra metricas de:
- Cache hit/miss (L1, L2, L3)
- LLM simples chamadas
- Ensemble chamadas
- CoVe falhas
- Tempo medio de resposta

Uso:
    python estabilizacao_pipeline.py              # 1 ciclo
    python estabilizacao_pipeline.py --watch      # loop a cada 60s
    python estabilizacao_pipeline.py --watch --intervalo 30
"""
import sys, os, json, time, argparse, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'devia', 'kernel'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, List


# Bateria de perguntas de teste
PERGUNTAS = [
    # Cache (repetidas, devem ser resolvidas sem LLM)
    "Explique o que e SPA",
    "O que significa SPA",
    "Como funciona o sistema de progressao",
    "O que sao estados compostos",
    "crie um npc ferreiro",
    "ola tudo bem",
    "bom dia",
    "criar npc vendedor",
    "O que e cadeia de markov",
    "Explique o conceito de jaccard",
    
    # LLM Simples (perguntas que exigem geracao)
    "Explique como o MCR usa entropia de shannon para detectar alucinacoes",
    "Como o cache hierarquico decide entre L1, L2 e L3?",
    "Qual a diferenca entre cadeia de markov de primeira ordem e estados compostos?",
    "Como funciona o ensemble de modelos no MCR-DevIA?",
    
    # Complexas / Criacao
    "crie uma quest de coleta de 10 pocoes de cura",
    "implemente um sistema de loot simples em lua",
]
# Repete as primeiras 5 para simular cache
for _ in range(3):
    PERGUNTAS.extend(PERGUNTAS[:5])


class MonitorPipeline:
    """Monitora o pipeline e acumula metricas."""

    def __init__(self):
        self._metricas = {
            'total': 0, 'cache_hit': 0, 'llm_simples': 0, 'ensemble': 0,
            'cove_falhas': 0, 'tempo_total': 0.0,
            'tempos': [], 'rotas': {},
        }

    def executar(self, perguntas: List[str]) -> Dict:
        """Executa pipeline para cada pergunta e acumula metricas."""
        from mcr.pipeline_completo import PipelineCompleto
        pipe = PipelineCompleto()

        for i, pergunta in enumerate(perguntas):
            t0 = time.time()
            try:
                resultado = pipe.processar(pergunta)
                tempo = time.time() - t0
                rota = resultado.get('rota', 'unknown')
                
                self._metricas['total'] += 1
                self._metricas['tempo_total'] += tempo
                self._metricas['tempos'].append(tempo)
                self._metricas['rotas'][rota] = self._metricas['rotas'].get(rota, 0) + 1
                
                if rota == 'cache':
                    self._metricas['cache_hit'] += 1
                elif rota == 'llm_simples':
                    self._metricas['llm_simples'] += 1
                elif rota == 'ensemble':
                    self._metricas['ensemble'] += 1
                
                verificacao = resultado.get('verificacao', {})
                if not verificacao.get('valida', True):
                    self._metricas['cove_falhas'] += 1
                
                print(f'  [{i+1}/{len(perguntas)}] {rota:12s} {tempo:.1f}s {pergunta[:50]}')
                
            except Exception as e:
                print(f'  [{i+1}/{len(perguntas)}] ERRO: {e}')
        
        return self._metricas

    def relatorio(self) -> str:
        """Gera relatorio formatado das metricas."""
        m = self._metricas
        total = max(m['total'], 1)
        tempo_medio = m['tempo_total'] / total
        
        linhas = [
            "=" * 55,
            "  RELATORIO DE ESTABILIZACAO DO PIPELINE",
            "=" * 55,
            "",
            f"  Total de perguntas:      {m['total']}",
            f"  Cache hit (L1+L2+L3):    {m['cache_hit']} ({m['cache_hit']/total*100:.0f}%)",
            f"  LLM simples:             {m['llm_simples']} ({m['llm_simples']/total*100:.0f}%)",
            f"  Ensemble 7B:             {m['ensemble']} ({m['ensemble']/total*100:.0f}%)",
            f"  CoVe falhas:             {m['cove_falhas']}",
            f"  Tempo medio:             {tempo_medio:.2f}s",
            "",
            "  Rotas:",
        ]
        for rota, count in sorted(m['rotas'].items(), key=lambda x: -x[1]):
            linhas.append(f"    {rota:15s}: {count}")
        
        if m['tempos']:
            linhas.append("")
            linhas.append(f"  Tempo min: {min(m['tempos']):.3f}s")
            linhas.append(f"  Tempo max: {max(m['tempos']):.3f}s")
            linhas.append(f"  Tempo mediano: {sorted(m['tempos'])[len(m['tempos'])//2]:.3f}s")
        
        return '\n'.join(linhas)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true', help='Loop periodico')
    parser.add_argument('--intervalo', type=int, default=60, help='Intervalo entre ciclos (s)')
    args = parser.parse_args()

    monitor = MonitorPipeline()

    if args.watch:
        ciclo = 0
        print(f'[Monitor] Iniciando estabilizacao (intervalo={args.intervalo}s)')
        print(f'[Monitor] {len(PERGUNTAS)} perguntas por ciclo')
        print()
        try:
            while True:
                print(f'=== Ciclo {ciclo} - {time.strftime("%H:%M:%S")} ===')
                monitor.executar(PERGUNTAS)
                rel = monitor.relatorio()
                print('\n' + rel + '\n')
                ciclo += 1
                time.sleep(args.intervalo)
        except KeyboardInterrupt:
            print('\n[Monitor] Parando...')
            print(monitor.relatorio())
    else:
        print(f'Executando {len(PERGUNTAS)} perguntas...')
        print()
        monitor.executar(PERGUNTAS)
        print()
        print(monitor.relatorio())


if __name__ == '__main__':
    main()
