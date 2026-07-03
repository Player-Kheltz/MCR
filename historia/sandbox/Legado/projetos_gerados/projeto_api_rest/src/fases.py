# app/fases.py

class Fase:
    def __init__(self, numero, descricao):
        self.numero = numero
        self.descricao = descricao

def get_fases():
    return [
        Fase(1, "Início da jornada"),
        Fase(2, "Desafio na floresta"),
        Fase(3, "Batalha com o dragão"),
        Fase(4, "Encontro com a princesa"),
        Fase(5, "Final feliz")
    ]