#!/usr/bin/env python3
"""
MCR-DevIA — AUTO-CONSCIENCIA (Meta-camada)
============================================
Nao resolve problemas. So OBSERVA e AVISA.
Como um co-piloto que diz: "Ei, voce ja tentou isso 3x e falhou."

Monitora:
  - Reparo que nunca funciona (mesmo erro >2x)
  - IA que nao responde (>2x)
  - Loop infinito de tentativas
  - Quando esta "patinando"

Uso: python mcr_autoconsciencia.py (roda e da o toque)
     python mcr_autoconsciencia.py --daemon (vigia continuamente)
"""

import sys, os, json, datetime

BASE = r'E:\Projeto MCR\sandbox'
AUTO_LOG = os.path.join(BASE, '.mcr_auto_log.json')
KG_PATH = os.path.join(BASE, '.mcr_devia', 'knowledge.json')


class AutoConsciencia:
    """
    Observa o comportamento do MCR-DevIA e aponta padroes.
    Nao age. So da o toque no ombro.
    """
    
    def __init__(self):
        self.toques = []  # toques que deu
    
    def observar(self):
        """Observa o estado atual do MCR-DevIA e da toques."""
        print('\n[META-CONSCIENCIA] Observando MCR-DevIA...')
        
        # 1. Verifica log de auto-reparo
        self._verificar_reparos()
        
        # 2. Verifica mesmo erro especifico >2x
        self._verificar_mesmo_erro()
        
        # 3. Verifica IA falhando >2x
        self._verificar_ia_falhando()
        
        # 4. Verifica KG
        self._verificar_kg()
        
        # 5. Verifica idade do conhecimento
        self._verificar_conhecimento()
        
        # Relatorio
        if self.toques:
            print(f'\n  Toques dados: {len(self.toques)}')
            for t in self.toques:
                print(f'    [TOQUE] {t["mensagem"]}')
        else:
            print(f'\n  Sem toques no momento.')
    
    def _verificar_reparos(self):
        """Verifica se ha reparos repetidos sem sucesso."""
        if not os.path.exists(AUTO_LOG): return
        
        with open(AUTO_LOG, 'r') as f:
            log = json.load(f)
        
        reparos = log.get('reparos', [])
        if not reparos:
            return
        
        # Reparos que FALHARAM (se tiver o campo resultado)
        falhas = [r for r in reparos if r.get('resultado') == 'falha']
        if len(falhas) >= 2:
            self.toques.append({
                'nivel': 'atencao',
                'mensagem': f'Atencao: {len(falhas)} reparos falharam consecutivamente. '
                           f'O ultimo foi em {falhas[-1].get("tipo","?")}. '
                           f'Motivo: {falhas[-1].get("motivo","desconhecido")}. '
                           f'Talvez o arquivo alvo tenha mudado de formato.',
                'sugestao': 'Tente verificar o formato atual do arquivo antes de tentar o reparo.',
            })
        
        # Reparos sem resultado (nem sucesso nem falha) = pode ter sido ignorado
        ignorados = len(reparos) - len([r for r in reparos if 'resultado' in r])
        if ignorados >= 3:
            self.toques.append({
                'nivel': 'atencao',
                'mensagem': f'{ignorados} reparos sem registro de resultado. '
                           f'Pode ser que a IA nao esteja respondendo ou o reparo esteja sendo pulado.',
                'sugestao': 'Verifique se a IA local esta respondendo. Se nao, talvez seja um timeout.',
            })

    def _verificar_mesmo_erro(self):
        """Detecta se o MESMO erro especifico aparece >2x nos reparos."""
        if not os.path.exists(AUTO_LOG): return
        try:
            with open(AUTO_LOG, 'r') as f:
                log = json.load(f)
            reparos = log.get('reparos', [])
            if not reparos:
                return
            # Agrupa por motivo/tipo
            motivos = {}
            for r in reparos:
                chave = r.get('motivo', r.get('tipo', 'desconhecido'))
                motivos[chave] = motivos.get(chave, 0) + 1
            for motivo, count in motivos.items():
                if count > 2 and motivo != 'desconhecido':
                    self.toques.append({
                        'nivel': 'atencao',
                        'mensagem': f'Mesmo erro {count}x: "{motivo}". '
                                   f'O reparador esta patinando neste problema.',
                        'sugestao': 'Analise manualmente o arquivo alvo. Pode ser um bug estrutural.',
                    })
                    break
        except Exception:
            pass

    def _verificar_ia_falhando(self):
        """Detecta se a IA nao responde >2x consecutivamente."""
        if not os.path.exists(AUTO_LOG): return
        try:
            with open(AUTO_LOG, 'r') as f:
                log = json.load(f)
            reparos = log.get('reparos', [])
            if not reparos:
                return
            # Conta falhas consecutivas NO FINAL da lista
            falhas_consecutivas = 0
            for r in reversed(reparos):
                if r.get('resultado') == 'falha' or not r.get('resultado'):
                    falhas_consecutivas += 1
                else:
                    break
            if falhas_consecutivas > 2:
                self.toques.append({
                    'nivel': 'critico',
                    'mensagem': f'IA falhando {falhas_consecutivas}x consecutivas. '
                               f'O ultimo reparo foi em {reparos[-1].get("tipo","?")}. '
                               f'A IA pode estar fora do ar ou com timeout.',
                    'sugestao': 'Verifique se o servidor Ollama esta rodando. '
                               'Se estiver, tente reiniciar o kernel.',
                })
        except Exception:
            pass
    
    def _verificar_kg(self):
        """Verifica se o KG tem licoes repetidas."""
        if not os.path.exists(KG_PATH): return
        
        try:
            with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                kg = json.load(f)
        except Exception as e:
            print(f"[Fix] ERRO: {e}")
        
        licoes = kg.get('licoes', [])
        
        # Busca licoes com o mesmo erro
        erros = [l.get('erro', '') for l in licoes]
        repetidos = {}
        for e in erros:
            repetidos[e] = repetidos.get(e, 0) + 1
        
        for erro, count in repetidos.items():
            if count >= 2 and len(erro) > 10:
                self.toques.append({
                    'nivel': 'info',
                    'mensagem': f'Licao repetida {count}x: "{erro}..."',
                    'sugestao': 'Considere unificar licoes duplicadas no Knowledge Graph.',
                })
                break  # So um aviso por vez
    
    def _verificar_conhecimento(self):
        """Verifica se o conhecimento foi atualizado recentemente."""
        if not os.path.exists(KG_PATH): return
        
        try:
            with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                kg = json.load(f)
        except Exception as e:
            print(f"[Fix] ERRO: {e}")
        
        n_licoes = len(kg.get('licoes', []))
        versao = kg.get('versoes', 0)
        
        print(f'  KG: {n_licoes} licoes, V{versao}')


if __name__ == '__main__':
    ac = AutoConsciencia()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        import time
        print('[META-CONSCIENCIA] Modo vigia (Ctrl+C para parar)')
        try:
            while True:
                ac.observar()
                time.sleep(30)
        except KeyboardInterrupt:
            print('\n  Parou.')
    else:
        ac.observar()
