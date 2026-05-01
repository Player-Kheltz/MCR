#!/usr/bin/env python3
import re
import sys
import json

# Dicionário estático MCR (termos que a API pode traduzir mal)
DICIONARIO_MCR = {
    "health": "vida",
    "maxhealth": "vida máxima",
    "mana": "mana",
    "maxmana": "mana máxima",
    "soul": "alma",
    "level": "nível",
    "experience": "experiência",
    "capacity": "capacidade",
    "speed": "velocidade",
    "attack": "ataque",
    "defense": "defesa",
    "armor": "armadura",
    "shield": "escudo",
    "weapon": "arma",
    "distance": "distância",
    "logout": "sair",
    "login": "entrar",
    "create account": "criar conta",
    "manage account": "gerenciar conta",
    "delete account": "apagar conta",
    "password": "senha",
    "new password": "nova senha",
    "confirm password": "confirmar senha",
    "name": "nome",
    "character": "personagem",
    "select character": "selecionar personagem",
    "create character": "criar personagem",
    "delete character": "apagar personagem",
    "enter game": "entrar no jogo",
    "accept": "aceitar",
    "decline": "recusar",
    "yes": "sim",
    "no": "não",
    "back": "voltar",
    "next": "próximo",
    "confirm": "confirmar",
    "cancel": "cancelar",
    "buy": "comprar",
    "sell": "vender",
    "trade": "trocar",
    "look": "olhar",
    "use": "usar",
    "walk": "andar",
    "follow": "seguir",
    "stop": "parar",
    "close": "fechar",
    "open": "abrir",
    "save": "salvar",
    "load": "carregar",
    "options": "opções",
    "settings": "configurações",
    "help": "ajuda",
    "quest": "missão",
    "mission": "missão",
    "reward": "recompensa",
    "collect": "coletar",
    "deliver": "entregar",
    "completed": "concluída",
    "in progress": "em andamento",
    "started": "iniciada",
    "failed": "falhou",
    "success": "sucesso",
    "error": "erro",
    "warning": "aviso",
    "server": "servidor",
    "world": "mundo",
    "channel": "canal",
    "chat": "chat",
    "message": "mensagem",
    "broadcast": "transmissão",
    "online": "online",
    "offline": "offline",
    "premium": "premium",
    "free": "grátis",
    "account": "conta",
    "player": "jogador",
    "npcs": "NPCs",
    "monsters": "monstros",
    "creatures": "criaturas",
    "items": "itens",
    "gold": "ouro",
    "platinum": "platina",
    "crystal": "cristal",
    "diamond": "diamante",
    "helmet": "capacete",
    "legs": "calças",
    "boots": "botas",
    "ring": "anel",
    "amulet": "amuleto",
    "container": "recipiente",
    "key": "chave",
    "spell": "magia",
    "rune": "runa",
    "potion": "poção",
    "food": "comida",
    "depot": "depósito",
    "inbox": "caixa de entrada",
    "store": "loja",
    "bank": "banco",
    "balance": "saldo",
    "deposit": "depositar",
    "withdraw": "sacar",
    "transfer": "transferir",
    "vocation": "vocação",
    "none": "nenhum",
    "knight": "cavaleiro",
    "paladin": "paladino",
    "sorcerer": "feiticeiro",
    "druid": "druida",
    "elder": "ancião",
    "master": "mestre",
    "royal": "real",
    "promotion": "promoção",
    "skill": "habilidade",
    "fist": "punho",
    "club": "clava",
    "sword": "espada",
    "axe": "machado",
    "shielding": "defesa",
    "fishing": "pesca",
    "critical": "crítico",
    "blessing": "bênção",
    "stamina": "energia",
    "prey": "presa",
    "hunt": "caçada",
    "task": "tarefa",
    "achievement": "conquista",
    "title": "título",
    "outfit": "visual",
    "mount": "montaria",
    "addon": "complemento",
    "house": "casa",
    "guild": "guilda",
    "party": "grupo",
    "friend": "amigo",
    "enemy": "inimigo",
    "tutorial": "tutorial",
    "note": "nota",
    "book": "livro",
    "document": "documento",
    "letter": "carta",
    "invitation": "convite",
    "report": "denunciar",
    "rule": "regra",
    "violation": "violação",
    "ban": "banir",
    "mute": "silenciar",
    "kick": "expulsar",
    "you are dead": "você está morto",
    "you have been defeated": "você foi derrotado",
    "you advanced": "você avançou",
    "you received": "você recebeu",
    "you see": "você vê",
    "you found": "você encontrou",
    "you gained": "você ganhou",
    "you have lost": "você perdeu",
    "you cannot": "você não pode",
    "you need": "você precisa",
    "you already": "você já",
    "not enough": "insuficiente",
    "welcome": "bem-vindo",
    "goodbye": "adeus",
    "congratulations": "parabéns",
    "sorry": "desculpe",
    "please": "por favor",
    "thank you": "obrigado",
    "you are": "você é",
    "invalid": "inválido",
    "expired": "expirado",
    "suspended": "suspenso",
    "disconnected": "desconectado",
    "timeout": "tempo esgotado",
    "connection lost": "conexão perdida",
    "forbidden": "proibido",
    "permission denied": "permissão negada",
    "inventory full": "inventário cheio",
    "too heavy": "muito pesado",
    "target not reachable": "alvo inacessível",
    "there is no way": "não há caminho",
    "you are exhausted": "você está exausto",
    "cannot use that object": "não pode usar este objeto",
    "cannot move this object": "não pode mover este objeto",
    "first go upstairs": "primeiro suba as escadas",
    "first go downstairs": "primeiro desça as escadas",
    "you see a": "você vê um",
    "you see an": "você vê uma",
    "it weighs": "pesa",
    "position": "posição",
    "north": "norte",
    "south": "sul",
    "east": "leste",
    "west": "oeste",
    "hello": "olá",
    "bye": "tchau",
    "farewell": "adeus",
    "greetings": "saudações",
}

# Termos técnicos que nunca devem ser alterados
TERMOS_ESTATICOS = {
    "You see ": "Você vê ",
    "You are ": "Você é ",
    "Your party has ": "Sua party tem ",
    "has no vocation.": "não tem vocação.",
    "yourself": "si mesmo(a)",
    "pending invitation.": "convite pendente.",
    "pending invitations.": "convites pendentes."
}

def carregar_dicionario():
    return DICIONARIO_MCR

def aplicar_dicionario(texto, dicionario):
    # Não aplicar a strings técnicas (contêm :: ou /scripts/)
    if '::' in texto or '/scripts/' in texto:
        return texto
    for eng, ptbr in dicionario.items():
        texto = re.sub(r'\b' + re.escape(eng) + r'\b', ptbr, texto, flags=re.IGNORECASE)
    return texto

def reparar_formatacao(original, traduzido):
    # Preserva espaços originais
    espacos_inicio = original[:len(original) - len(original.lstrip(' '))]
    espacos_fim = original[len(original.rstrip(' ')):]

    texto_base = original.strip()
    resultado = traduzido.strip()

    # Impõe termos estáticos do motor
    if texto_base in TERMOS_ESTATICOS:
        resultado = TERMOS_ESTATICOS[texto_base].strip()

    return f"{espacos_inicio}{resultado}{espacos_fim}"

def main():
    if len(sys.argv) < 4:
        print("Uso: python 3_reparador.py extraido.txt traduzido.txt reparado.txt")
        return

    arq_original, arq_traduzido, arq_reparado = sys.argv[1], sys.argv[2], sys.argv[3]

    originais = {}
    with open(arq_original, 'r', encoding='utf-8') as f:
        for linha in f:
            if '=' in linha and not linha.startswith('['):
                k, v = linha.strip('\n').split('=', 1)
                originais[k] = v

    dicio = carregar_dicionario()
    linhas_finais = []

    with open(arq_traduzido, 'r', encoding='utf-8') as f:
        for linha in f:
            if '=' in linha and not linha.startswith('['):
                k, v = linha.strip('\n').split('=', 1)
                if k in originais:
                    v = reparar_formatacao(originais[k], v)
                    v = aplicar_dicionario(v, dicio)
                linhas_finais.append(f"{k}={v}\n")
            else:
                linhas_finais.append(linha)

    with open(arq_reparado, 'w', encoding='utf-8') as f:
        f.writelines(linhas_finais)

    print(f"✅ Arquivo {arq_reparado} gerado com espaços e termos corrigidos!")

if __name__ == '__main__':
    main()