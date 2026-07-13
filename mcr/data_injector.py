"""
mcr.data_injector — Injeta dados reais do Canary no contexto de geracao.
Usa ItemDatabase + DeterministicFiller.
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'knowledge'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))


class DataInjector:
    def __init__(self):
        self.items = None
        self._init_items()
        self._init_filler()

    def _init_items(self):
        try:
            from item_database import ItemDatabase
            self.items = ItemDatabase()
        except Exception as e:
            print(f'[DataInjector] ItemDatabase nao carregado: {e}')

    def _init_filler(self):
        try:
            from DeterministicFiller import (
                preencher_gap, preencher_template, gaps_restantes)
            self._preencher_gap = preencher_gap
            self._preencher_template = preencher_template
            self._gaps_restantes = gaps_restantes
        except Exception as e:
            print(f'[DataInjector] DeterministicFiller nao carregado: {e}')

    def enriquecer_contexto(self, pergunta: str, classe: str) -> str:
        contexto = ''
        pl = pergunta.lower()

        # Para NPCs de comercio, sugerir itens reais
        if classe == 'criar_npc' and self.items:
            profissoes = ['ferreiro', 'alquimista', 'mercador',
                          'bibliotecario', 'guarda', 'mago',
                          'druida', 'paladino']
            for prof in profissoes:
                if prof in pl:
                    itens = self.items.sugerir_itens_para_shop(prof, 5)
                    if itens:
                        contexto += (
                            f'Itens reais do jogo para {prof}: ')
                        contexto += ', '.join([
                            f'{i["nome"]} (ID:{i["id"]})'
                            for i in itens])
                    break

        # Para habilidades, preencher cooldown e elementos
        if classe == 'criar_habilidade_spa' and hasattr(self, '_preencher_gap'):
            dominios = {'fogo': 23, 'gelo': 24, 'terra': 25,
                        'raio': 26, 'fisico': 100, 'sagrado': 200}
            efeitos = ['dano_extra', 'area_ground', 'finisher',
                       'buff_damage', 'cura']
            for nome_dom, dom_id in dominios.items():
                if nome_dom in pl:
                    cor = self._preencher_gap(
                        'cor_dominio', {'dominio_id': dom_id})
                    elem = self._preencher_gap(
                        'elemento_dano', {'dominio_id': dom_id})
                    contexto += (
                        f'Dominio {nome_dom}: cor={cor}, dano={elem}')
                    break

        return contexto
