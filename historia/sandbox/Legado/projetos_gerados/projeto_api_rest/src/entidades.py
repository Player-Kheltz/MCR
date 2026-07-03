from pydantic import BaseModel

class Jogador(BaseModel):
    id: int
    nome: str
    nivel: int = 1
    pontos: int = 0

    class Config:
        orm_mode = True

class Inimigo(BaseModel):
    id: int
    tipo: str
    vida: int
    dano: int

    class Config:
        orm_mode = True

class Item(BaseModel):
    id: int
    nome: str
    tipo: str
    valor: int

    class Config:
        orm_mode = True