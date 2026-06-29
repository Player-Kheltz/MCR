// entidades.js
class Entidade {
    constructor(id, tipo) {
        this.id = id;
        this.tipo = tipo;
        this.posicao = { x: 0, y: 0 };
        this.status = 'ativo';
    }
    mover(x, y) {
        this.posicao.x += x;
        this.posicao.y += y;
        console.log(`Entidade ${this.id} movida para (${this.posicao.x}, ${this.posicao.y})`);
    }
    atacar(outraEntidade) {
        if (outraEntidade.status === 'ativo') {
            outraEntidade.status = 'inativo';
            console.log(`Entidade ${this.id} atacou e derrotou a entidade ${outraEntidade.id}`);
        } else {
            console.log(`A entidade ${outraEntidade.id} já está inativa.`);
        }
    }
    curar() {
        if (this.status === 'inativo') {
            this.status = 'ativo';
            console.log(`Entidade ${this.id} foi curada e agora está ativa.`);
        } else {
            console.log(`A entidade ${this.id} já está ativa.`);
        }
    }
    getStatus() {
        return this.status;
    }
    getPosicao() {
        return this.posicao;
    }
}
class Jogador extends Entidade {
    constructor(id, nome) {
        super(id, 'jogador');
        this.nome = nome;
        this.pontos = 0;
    }
    adicionarPontos(pontos) {
        this.pontos += pontos;
        console.log(`Jogador ${this.nome} ganhou ${pontos} pontos. Total: ${this.pontos}`);
    }
}
class Monstro extends Entidade {
    constructor(id, nivel) {
        super(id, 'monstro');
        this.nivel = nivel;
    }
    subirNivel() {
        this.nivel += 1;
        console.log(`Monstro ${this.id} subiu de nível para ${this.nivel}`);
    }
}
module.exports = { Entidade, Jogador, Monstro };
Este módulo define três classes principais:
1. `Entidade`: Uma classe base que representa uma entidade genérica no jogo, com métodos para mover, atacar e curar.
2. `Jogador`: Uma classe que estende `Entidade` e adiciona propriedades específicas de jogadores, como nome e pontos.
3. `Monstro`: Uma classe que também estende `Entidade` e adiciona uma propriedade de nível.
Você pode usar este módulo em seu projeto React para criar e manipular entidades no jogo. Certifique-se de importar e usar essas classes conforme necessário em seus componentes do React e lógica de backend com Socket.IO.