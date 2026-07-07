"""mcr.logwatcher_bridge — Conecta o LogWatcher existente ao sistema de Anti-Patterns.
Quando um erro e detectado nos logs do Canary, classifica e registra no KG."""
import time
from pathlib import Path
from typing import Optional

from mcr.anti_pattern import classificar_erro, registrar_anti_pattern


class LogWatcherBridge:
    """Bridge entre o LogWatcher (existente) e o sistema de Anti-Patterns."""

    def __init__(self, processar_func=None):
        self.processar_func = processar_func
        self._ultimo_processamento = 0
        self._anti_patterns_registrados = 0

    def processar_erro(self, linha_erro: str, arquivo_origem: str = '') -> dict:
        """Processa uma linha de erro do LogWatcher.
        
        Fluxo:
        1. Classifica o erro (anti_pattern.classificar_erro)
        2. Registra como anti-pattern no KG
        3. Se houver processar_func (callback do DevIA), chama para diagnostico
        
        Returns:
            dict com resultado do processamento
        """
        # 1. Classifica
        erro_classificado = classificar_erro(linha_erro, arquivo_origem)
        print(f'[LogWatcherBridge] Erro classificado: {erro_classificado["categoria"]} '
              f'-> {erro_classificado["api_problematica"][:40]}')

        # 2. Registra no KG
        registrado = registrar_anti_pattern(erro_classificado)
        if registrado:
            self._anti_patterns_registrados += 1
            print(f'[LogWatcherBridge] Anti-pattern registrado no KG '
                  f'(total: {self._anti_patterns_registrados})')

        # 3. Se tiver callback, chama o DevIA para diagnostico
        if self.processar_func and erro_classificado['categoria'] != 'desconhecido':
            try:
                prompt = (
                    f"O servidor Canary reportou o seguinte erro:\n"
                    f"ERRO: {linha_erro[:200]}\n"
                    f"ARQUIVO: {arquivo_origem}\n"
                    f"CATEGORIA: {erro_classificado['categoria']}\n"
                    f"API PROBLEMATICA: {erro_classificado['api_problematica']}\n\n"
                    f"Diagnostique e corrija."
                )
                resultado = self.processar_func(prompt)
                erro_classificado['diagnostico_devia'] = str(resultado)[:200]
            except Exception as e:
                print(f'[LogWatcherBridge] Erro no diagnostico: {e}')

        return erro_classificado

    def stats(self) -> dict:
        return {
            'anti_patterns_registrados': self._anti_patterns_registrados,
        }
