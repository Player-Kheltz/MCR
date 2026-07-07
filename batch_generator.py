#!/usr/bin/env python3
"""Batch Generator — Fabrica de Conteudo Autonoma para MCR-DevIA.
Le um JSON de entradas, processa cada uma via processar(), gera relatorio.
"""
import sys, os, json, time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Importa o processar do mcr_devia
# (precisa importar o modulo para que os globais sejam inicializados)
from mcr_devia import processar


def carregar_entradas(caminho_json):
    with open(caminho_json, 'r', encoding='utf-8') as f:
        return json.load(f)


def executar_lote(entradas):
    """Executa lote de requisicoes e retorna relatorio."""
    t0 = time.time()
    resultados = []
    total_arquivos = 0
    total_erros = 0
    
    for i, item in enumerate(entradas):
        classe = item.get('classe', 'desconhecido')
        prompt = item.get('prompt', '')
        
        if not prompt:
            print('\n[Batch] Entrada %d: prompt vazio, ignorando' % i)
            continue
        
        print('\n' + '='*60)
        print('[Batch %d/%d] %s' % (i+1, len(entradas), classe))
        print('  Prompt: %s...' % prompt[:80])
        print('='*60)
        
        t_item = time.time()
        try:
            resp = processar(prompt)
        except Exception as e:
            print('  ERRO na execucao: %s' % e)
            resultados.append({'indice': i, 'classe': classe, 'erro': str(e), 'tempo': time.time()-t_item})
            total_erros += 1
            continue
        
        tempo_item = time.time() - t_item
        
        # Conta arquivos gerados
        resposta = resp.get('resposta', '')
        classe_resp = resp.get('classe', '')
        sintaxe_valida = resp.get('sintaxe_valida', None)
        tentativas = resp.get('tentativas_sintaxe', 0)
        
        # Verifica se tem arquivos salvos (pelo pos_processamento)
        # O processar retorna a resposta mas os arquivos sao salvos pelo pipeline
        # Verificamos na pasta generated/ ou quarantine/
        arquivos_gerados = []
        arqs = []
        for diretorio in ['generated', 'quarantine']:
            caminho_dir = os.path.join(BASE, '..', 'Projeto MCR', 'scripts', diretorio)
            if os.path.isdir(caminho_dir):
                for f in os.listdir(caminho_dir):
                    fp = os.path.join(caminho_dir, f)
                    if os.path.isfile(fp) and f.endswith('.lua'):
                        # So conta arquivos criados durante esta execucao
                        criado_em = os.path.getctime(fp)
                        if criado_em >= t0:
                            arqs.append(fp)
                            if diretorio == 'quarantine':
                                total_erros += 1
                            else:
                                total_arquivos += 1
        
        resultado_item = {
            'indice': i,
            'classe': classe_resp,
            'tempo': round(tempo_item, 2),
            'sintaxe_valida': sintaxe_valida,
            'tentativas': tentativas,
            'arquivos': [os.path.basename(a) for a in arqs],
            'erro': None,
        }
        resultados.append(resultado_item)
        
        print('  Classe: %s | Tempo: %.1fs | Valido: %s | Tentativas: %d' % (
            classe_resp, tempo_item, sintaxe_valida, tentativas))
        if arqs:
            print('  Arquivos: %s' % [os.path.basename(a) for a in arqs])
    
    # Relatorio final
    t1 = time.time()
    print('\n' + '='*60)
    print('  RELATORIO FINAL DO BATCH')
    print('='*60)
    print('  Total de entradas: %d' % len(entradas))
    print('  Arquivos gerados: %d' % total_arquivos)
    print('  Arquivos em quarentena: %d' % total_erros)
    print('  Tempo total: %.1fs' % (t1-t0))
    if total_arquivos > 0:
        print('  Velocidade: %.1f arquivos/min' % (total_arquivos/(t1-t0)*60))
    print('='*60)
    
    return {
        'total_entradas': len(entradas),
        'arquivos_gerados': total_arquivos,
        'arquivos_quarentena': total_erros,
        'tempo_total': round(t1-t0, 1),
        'resultados': resultados,
    }


if __name__ == '__main__':
    json_path = sys.argv[1] if len(sys.argv) > 1 else 'batch_input.json'
    if not os.path.isabs(json_path):
        json_path = os.path.join(BASE, json_path)
    
    if not os.path.exists(json_path):
        print('Arquivo nao encontrado: %s' % json_path)
        print('Uso: python batch_generator.py [caminho_para_input.json]')
        sys.exit(1)
    
    entradas = carregar_entradas(json_path)
    print('Batch Generator — Fabrica de Conteudo MCR-DevIA')
    print('Carregadas %d entradas de: %s' % (len(entradas), json_path))
    
    relatorio = executar_lote(entradas)
    
    # Salva relatorio
    relatorio_path = os.path.join(BASE, 'batch_relatorio.json')
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    print('\nRelatorio salvo em: %s' % relatorio_path)
