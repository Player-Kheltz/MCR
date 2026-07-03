#!/usr/bin/env python3
"""PROTÓTIPO: AprendizDePadroes lê fontes REAIS e extrai padrões.

NÃO MODIFICA NADA NO MCR. Só importa módulos existentes.
Valida que o sistema consegue aprender padrões de múltiplas fontes.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from modulos.pattern_engine import PatternEngine
from modulos.aprendiz_de_padroes import AprendizDePadroes


def executar():
    print("=" * 80)
    print("  APRENDIZ DE PADRÕES — PROTÓTIPO")
    print("  Lendo fontes REAIS do MCR-DevIA e extraindo padrões")
    print("=" * 80)
    
    pe = PatternEngine()
    aprendiz = AprendizDePadroes(pe=pe)
    
    # Estuda cada fonte individualmente
    fontes = ['kg', 'conselho', 'episodios', 'metricas', 'testes', 'conversa']
    
    total_geral = 0
    
    for fonte in fontes:
        print(f"\n{'─'*80}")
        print(f"  [FONTE] {fonte.upper()}")
        print(f"{'─'*80}")
        
        padroes = aprendiz.estudar_fonte(fonte)
        total_geral += len(padroes)
        
        if not padroes:
            print(f"  → Nenhum padrão encontrado (fonte vazia ou sem dados)")
            continue
        
        print(f"  → {len(padroes)} padrões encontrados")
        
        # Mostra top 3
        top = sorted(padroes, key=lambda x: -x.get('conf', 0))[:3]
        for p in top:
            conf = p.get('conf', 0)
            tipo = p.get('tipo', '?')
            
            if tipo == 'coocorrencia':
                termos = p.get('termos', [])
                freq = p.get('freq', 0)
                sugestao = p.get('sugestao_ie', {}).get('tipo', 'DOM_GENERICO')
                print(f"    [{conf:.2f}] {sugestao}: '{termos[0]}' (freq={freq})")
            
            elif tipo == 'ngrama_tipo':
                ng = p.get('n_grama', ())
                freq = p.get('freq', 0)
                print(f"    [{conf:.2f}] n-grama: {ng} (freq={freq})")
            
            elif tipo == 'raciocinio':
                membro = p.get('membro', '?')
                score = p.get('score_medio', 0)
                ocorr = p.get('ocorrencias', 0)
                print(f"    [{conf:.2f}] {membro}: score={score:.2f} ({ocorr} ocorrências)")
            
            elif tipo == 'risco':
                termo = p.get('termos', [])
                taxa = p.get('taxa_risco', 0)
                print(f"    [{conf:.2f}] RISCO: '{termo}' (taxa={taxa:.2%})")
            
            elif tipo == 'rota_preferida':
                tmpl = p.get('template_mais_usado', '?')
                uso = p.get('uso_total', 0)
                print(f"    [{conf:.2f}] Rota preferida: '{tmpl}' ({uso} usos)")
            
            elif tipo == 'tempo_medio':
                tm = p.get('tempo_medio', 0)
                n = p.get('ocorrencias', 0)
                print(f"    [{conf:.2f}] Tempo médio: {tm}s ({n} execuções)")
            
            elif tipo == 'teste_falha':
                teste = p.get('teste', '?')
                falhos = p.get('criterios_falhos', [])
                print(f"    [{conf:.2f}] Teste '{teste}': falhou em {falhos}")
            
            elif tipo == 'pergunta_teste':
                ng = p.get('n_grama', ())
                tam = p.get('tamanho', 0)
                print(f"    [{conf:.2f}] Padrão de pergunta teste: {ng} ({tam} chars)")
            
            elif tipo == 'topico':
                n = p.get('ocorrencias', 0)
                exemplos = p.get('exemplos', [])[:2]
                print(f"    [{conf:.2f}] Tópico: {n} mensagens similares")
                for ex in exemplos:
                    print(f"      → {ex[:80]}")
            
            else:
                print(f"    [{conf:.2f}] {tipo}: {str(p)[:100]}")
    
    # Relatório final
    print(f"\n\n{'='*80}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*80}")
    print(f"\n  Total de fontes: {len(fontes)}")
    print(f"  Total de padrões encontrados: {total_geral}")
    
    # Por fonte
    print(f"\n  --- Por fonte ---")
    for fonte in fontes:
        qtd = len([p for p in aprendiz._padroes_encontrados if p.get('fonte') == fonte])
        conf_media = sum(p.get('conf', 0) for p in aprendiz._padroes_encontrados 
                        if p.get('fonte') == fonte) / max(qtd, 1)
        print(f"    {fonte}: {qtd} padrões (conf média: {conf_media:.2f})")
    
    # Tipos de padrão
    tipos = {}
    for p in aprendiz._padroes_encontrados:
        t = p.get('tipo', '?')
        if t not in tipos:
            tipos[t] = 0
        tipos[t] += 1
    
    print(f"\n  --- Por tipo ---")
    for t, n in sorted(tipos.items(), key=lambda x: -x[1]):
        print(f"    {t}: {n}")
    
    print(f"\n{'='*80}")
    print(f"  SIMULAÇÃO: IE carregaria os padrões em runtime")
    print(f"{'='*80}")
    
    # Simula quais padrões seriam carregados pela IE
    lexico_novos = []
    markov_novos = []
    riscos_novos = []
    
    for p in aprendiz._padroes_encontrados:
        if p.get('conf', 0) >= 0.7:
            if 'sugestao_ie' in p:
                lexico_novos.append(p['sugestao_ie'].get('tipo', '?'))
            if 'markov' in p:
                markov_novos.append(p.get('n_grama', str(p['markov'])[:30]))
            if p.get('tipo') == 'risco':
                riscos_novos.append(p.get('termos', ['?']))
    
    print(f"\n  IE receberia:")
    print(f"    {len(lexico_novos)} novos tipos de token (ex: {lexico_novos[:5]})")
    print(f"    {len(markov_novos)} novas Markov chains")
    print(f"    {len(riscos_novos)} alertas de risco")
    print(f"\n  Impacto esperado: melhora na detecção de intenção")
    print(f"  e redução de falsos positivos em padrões de risco.")
    print(f"{'='*80}")
    
    return aprendiz


if __name__ == '__main__':
    aprendiz = executar()
