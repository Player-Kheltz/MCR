// Definindo o NPC Guia
class NPCGuide {
    constructor(name, location) {
        this.name = name;
        this.location = location;
    }

    // Método para interagir com o jogador
    interact(player) {
        console.log(`${this.name}: Olá, ${player}! Bem-vindo(a) a Eridanus. Estou aqui para ajudar.`);
        this.showLocationInfo();
    }

    // Método para mostrar informações sobre a localização atual do NPC
    showLocationInfo() {
        console.log(`${this.name}: Você está em ${this.location}. Esta é uma área de pesquisa científica importante.`);
    }
}

// Criando um novo NPC Guia em Eridanus
const eridanusGuide = new NPCGuide('Dr. Zara', 'Eridanus Research Station');

// Simulando interação com o jogador
eridanusGuide.interact('Jogador');