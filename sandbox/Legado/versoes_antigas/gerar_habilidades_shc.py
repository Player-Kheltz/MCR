"""
    Gerador de Habilidades SHC para dominios de arma
    Gera 20 habilidades por dominio com: sinergias, estados, condicoes, postura, niveis
    Uso: python gerar_habilidades_shc.py
"""
import os
import sys

BASE = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'

# Template de dominio arma
DOMINIOS = {
    "arcos": {
        id = 120, nome = "ARCOS", perfil = "Especialidade (Precisao 13 -> Combate 1)",
        traco = "Mira Infalivel — Nv5: alcance+1 | Nv10: critico+5% | Nv15: perfuracao | Nv20: olho de aguia",
        cor = "COR.DOM_COMBATE_PRECISAO",
        elemento = "COMBAT_PHYSICALDAMAGE",
        ids = (12001, 12020),
        estilo = "distancia",
        sinergias = {
            {dom = 23, nome = "Fogo", desc = "Flecha Incendiaria" },
            {dom = 24, nome = "Gelo", desc = "Flecha Congelante" },
            {dom = 26, nome = "Energia", desc = "Flecha Eletrica" },
            {dom = 25, nome = "Terra", desc = "Flecha Venenosa" },
        }
    },
    "lutador": {
        id = 130, nome = "LUTADOR", perfil = "Especialidade (Artes Marciais 14 -> Combate 1)",
        traco = "Punhos de Aco — Nv5: dano+10% | Nv10: combo+1 | Nv15: quebra-ossos | Nv20: mestre do combate",
        cor = "COR.DOM_COMBATE_IMPACTO",
        elemento = "COMBAT_PHYSICALDAMAGE",
        ids = (13001, 13020),
        estilo = "corpoacorpo",
        sinergias = {
            {dom = 14, nome = "ArtesMarciais", desc = "Artes Marciais" },
            {dom = 132, nome = "ArmasDePunho", desc = "Armas de Punho" },
            {dom = 1, nome = "Combate", desc = "Combate" },
            {dom = 4, nome = "Natureza", desc = "Natureza" },
        }
    },
    "armas_punho": {
        id = 132, nome = "ARMAS_DE_PUNHO", perfil = "Especialidade (Artes Marciais 14 -> Combate 1)",
        traco = "Soco Rapido — Nv5: velocidade+5% | Nv10: multi-hit+1 | Nv15: precisao | Nv20: mestre dos punhos",
        cor = "COR.DOM_COMBATE_IMPACTO",
        elemento = "COMBAT_PHYSICALDAMAGE",
        ids = (13201, 13220),
        estilo = "corpoacorpo",
        sinergias = {
            {dom = 130, nome = "Lutador", desc = "Lutador" },
            {dom = 14, nome = "ArtesMarciais", desc = "Artes Marciais" },
            {dom = 26, nome = "Energia", desc = "Energia" },
        }
    },
    "bastoes_arcanos": {
        id = 133, nome = "BASTOES_ARCANOS", perfil = "Especialidade (Artes Marciais 14 -> Combate 1)",
        traco = "Sabedoria Arcana — Nv5: mana+5% | Nv10: cooldown-10% | Nv15: duplo | Nv20: mestre arcano",
        cor = "COR.DOM_MAGIA_ARCANA",
        elemento = "COMBAT_ENERGYDAMAGE",
        ids = (13301, 13320),
        estilo = "magia",
        sinergias = {
            {dom = 23, nome = "Fogo", desc = "Fogo" },
            {dom = 24, nome = "Gelo", desc = "Gelo" },
            {dom = 26, nome = "Energia", desc = "Energia" },
            {dom = 25, nome = "Terra", desc = "Terra" },
            {dom = 200, nome = "SagradoMorte", desc = "Sagrado e Morte" },
        }
    },
    "clavas_leves": {
        id = 112, nome = "CLAVAS_LEVES", perfil = "Especialidade (Clavas 12 -> Combate 1)",
        traco = "Golpe Rapido — Nv5: velocidade+5% | Nv10: atordoamento+5% | Nv15: duplo | Nv20: mestre das clavas",
        cor = "COR.DOM_CLAVAS",
        elemento = "COMBAT_PHYSICALDAMAGE",
        ids = (11201, 11220),
        estilo = "corpoacorpo",
        sinergias = {
            {dom = 113, nome = "ClavasPesadas", desc = "Clavas Pesadas" },
            {dom = 1, nome = "Combate", desc = "Combate" },
            {dom = 25, nome = "Terra", desc = "Terra" },
        }
    },
    "clavas_pesadas": {
        id = 113, nome = "CLAVAS_PESADAS", perfil = "Especialidade (Clavas 12 -> Combate 1)",
        traco = "Impacto Brutal — Nv5: dano+10% | Nv10: knockback+1 | Nv15: area+1 | Nv20: mestre do impacto",
        cor = "COR.DOM_CLAVAS",
        elemento = "COMBAT_PHYSICALDAMAGE",
        ids = (11301, 11320),
        estilo = "corpoacorpo",
        sinergias = {
            {dom = 112, nome = "ClavasLeves", desc = "Clavas Leves" },
            {dom = 25, nome = "Terra", desc = "Terra" },
            {dom = 1, nome = "Combate", desc = "Combate" },
        }
    },
    "espadas_pesadas": {
        id = 101, nome = "ESPADAS_PESADAS", perfil = "Especialidade (Laminas 10 -> Combate 1)",
        traco = "Golpe Poderoso — Nv5: dano+10% | Nv10: sangramento+5% | Nv15: area+1 | Nv20: mestre das laminas",
        cor = "COR.DOM_COMBATE_LAMINAS",
        elemento = "COMBAT_PHYSICALDAMAGE",
        ids = (10101, 10120),
        estilo = "corpoacorpo",
        sinergias = {
            {dom = 100, nome = "EspadasLeves", desc = "Espadas Leves" },
            {dom = 23, nome = "Fogo", desc = "Fogo" },
            {dom = 200, nome = "SagradoMorte", desc = "Sagrado e Morte" },
        }
    },
    "machados_pesados": {
        id = 111, nome = "MACHADOS_PESADOS", perfil = "Especialidade (Machados 11 -> Combate 1)",
        traco = "Furia do Machado — Nv5: dano+10% | Nv10: armadura-5% | Nv15: area+1 | Nv20: mestre dos machados",
        cor = "COR.DOM_COMBATE_LAMINAS",
        elemento = "COMBAT_PHYSICALDAMAGE",
        ids = (11101, 11120),
        estilo = "corpoacorpo",
        sinergias = {
            {dom = 110, nome = "MachadosLeves", desc = "Machados Leves" },
            {dom = 25, nome = "Terra", desc = "Terra" },
            {dom = 1, nome = "Combate", desc = "Combate" },
        }
    },
    "sobrevivencia": {
        id = 400, nome = "SOBREVIVENCIA", perfil = "Especialidade (Natureza 4)",
        traco = "Sobrevivente — Nv5: regen+1% | Nv10: velocidade+5% | Nv15: faro | Nv20: mestre da selva",
        cor = "COR.DOM_NATUREZA",
        elemento = "COMBAT_PHYSICALDAMAGE",
        ids = (40001, 40020),
        estilo = "distancia",
        sinergias = {
            {dom = 24, nome = "Gelo", desc = "Gelo" },
            {dom = 25, nome = "Terra", desc = "Terra" },
            {dom = 120, nome = "Arcos", desc = "Arcos" },
        }
    },
}

TIPOS_EXECUCAO = {
    projectile = {"projectile", "distance"},
    melee = {"melee", "close"},
    area_target = {"area_target", "aoe"},
    cone = {"cone", "cone"},
    explosion_ring = {"explosion_ring", "ring"},
    storm = {"storm", "multi"},
    multi_hit = {"multi_hit", "combo"},
    buff = {"buff", "buff"},
    debuff = {"debuff", "debuff"},
    heal = {"heal", "heal"},
    trap = {"trap", "trap"},
    field_aura = {"field_aura", "aura"},
}

def gerar_habilidades(dominio_key, cfg):
    dom_id = cfg["id"]
    filepath = os.path.join(BASE, dominio_key + ".lua")
    
    linhas = []
    linhas.append('--[[')
    linhas.append(f'    Projeto MCR — SPA — {cfg["nome"]} ({dom_id})')
    linhas.append(f'    Perfil: {cfg["perfil"]}')
    linhas.append(f'    SHC: 5 camadas contextuais')
    linhas.append(f'    IDs: {cfg["ids"][0]}-{cfg["ids"][1]}')
    linhas.append('--]]')
    linhas.append(f'-- Traco: "{cfg["traco"]}"')
    linhas.append('')
    
    # Definir pool de tipos variados
    tipos_disponiveis = list(TIPOS_EXECUCAO.keys())
    
    # Gerar 20 habilidades
    for idx in range(1, 21):
        hab_id = cfg["ids"][0] + idx - 1
        
        # Escolher tipo baseado no idx para variar
        if idx <= 3:
            tipo_base = cfg["estilo"] == "distancia" and "projectile" or "melee"
            cat = "single"
        elif idx <= 5:
            tipo_base = "area_target"
            cat = "aoe"
        elif idx <= 7:
            tipo_base = "cone"
            cat = "aoe"
        elif idx == 8:
            tipo_base = "buff"
            cat = "buff"
        elif idx == 9:
            tipo_base = "debuff"
            cat = "debuff"
        elif idx == 10:
            tipo_base = "multi_hit"
            cat = "single"
        elif idx <= 12:
            tipo_base = "explosion_ring"
            cat = "aoe"
        elif idx <= 14:
            tipo_base = cfg["estilo"] == "distancia" and "projectile" or "melee"
            cat = "single"
        elif idx <= 16:
            tipo_base = "field_aura"
            cat = "buff"
        elif idx == 17:
            tipo_base = "trap"
            cat = "debuff"
        elif idx <= 19:
            tipo_base = "storm"
            cat = "finisher"
        else:
            tipo_base = "multi_hit"
            cat = "finisher"
        
        # Dano escalonado
        dano_base = round(0.5 + idx * 0.08, 1)
        percentual = round(0.15 + idx * 0.025, 2)
        if percentual > 0.65: percentual = 0.65
        
        # nome
        nomes_dist = ["Tiro Certeiro", "Chuva de Flechas", "Flecha Perfurante",
            "Disparo Triplo", "Flecha Elemental", "Tiro Rapido", "Flecha de Gelo",
            "Mira Precisa", "Olho de Aguia", "Tempestade de Flechas",
            "Flecha Arcana", "Disparo Certeiro", "Barragem", "Foco do Atirador",
            "Flecha Buscadora", "Alvo Marcado", "Flecha Explosiva", "Chuva Perfurante",
            "Rajada Final", "Tiro do Julgamento"]
        nomes_punho = ["Soco Rapido", "Chute Baixo", "Joelhada", "Combo de Punhos",
            "Giro de Tornado", "Punho de Ferro", "Vento Cortante", "Esquiva Felina",
            "Foco dos Punhos", "Danca dos Punhos", "Soco Trovejante", "Chute Lateral",
            "Golpe Giro", "Respiração Profunda", "Punho Sismico", "Martelo de Plastico",
            "Soco Sombrio", "Cascata de Golpes", "Golpe Decisivo", "Furia dos Punhos"]
        nomes_lutador = ["Jab", "Cruzado", "Combinacao", "Gancho", "Upper Cut",
            "Combo Rapido", "Quebra-Costas", "Foco Interior", "Furia Marcial",
            "Combo Final", "Soco no Ventre", "Cotovelada", "Chapa Giratoria",
            "Respiração do Guerreiro", "Golpe do Dragao", "Martelo de Ferro",
            "Sombra Veloz", "Sequencia Mortal", "Golpe do Destino", "Furia do Lutador"]
        nomes_clavas = ["Golpe Rapido", "Impacto Leve", "Giro Rapido", "Combo de Clavas",
            "Chuva de Golpes", "Golpe Giratorio", "Quebra-Ossos", "Postura Firme",
            "Foco da Clava", "Tempestade de Golpes", "Golpe Sombrio", "Impacto Duplo",
            "Varredura", "Concentracao", "Golpe Esmagador", "Impacto Trovejante",
            "Clava Veloz", "Sequencia Brutal", "Golpe Final", "Furia do Impacto"]
        nomes_pesadas = ["Corte Poderoso", "Impacto Brutal", "Machadada", "Golpe de Esquerda",
            "Corte Profundo", "Golpe de Direita", "Travessao", "Postura de Ferro",
            "Golpe Sombrio", "Corte Decisivo", "Furia do Machado", "Golpe Duplo",
            "Corte Giratorio", "Respiracao Profunda", "Machado Buscador",
            "Impacto Sismico", "Corte em Espiral", "Sequencia Brutal",
            "Golpe do Destino", "Furia da Laminas"]
        nomes_bastoes = ["Ataque Arcano", "Explosao Arcana", "Bastao de Raios", "Combo Arcano",
            "Onda de Poder", "Bastao Giratorio", "Toque Arcano", "Sabedoria Arcana",
            "Concentracao Arcana", "Explosao Final", "Raio Arcano", "Bastao de Gelo",
            "Onda Arcana", "Meditacao", "Bastao de Fogo", "Tempestade Arcana",
            "Campo Arcano", "Sequencia Arcana", "Golpe do Arcano", "Furia Arcana"]
        nomes_flecha = ["Tiro Certeiro", "Chuva de Flechas", "Flecha Perfurante",
            "Disparo Triplo", "Flecha Elemental", "Tiro Rapido", "Flecha de Gelo",
            "Mira Precisa", "Olho de Aguia", "Tempestade de Flechas",
            "Barragem", "Foco do Atirador", "Flecha Buscadora", "Alvo Marcado",
            "Flecha Explosiva", "Chuva Perfurante", "Rajada Final", "Tiro do Julgamento",
            "Flecha do Vento", "Ultimo Recurso"]
        
        # Mapa de nomes por dominio
        nomes_dict = {
            "arcos": nomes_flecha,
            "lutador": nomes_lutador,
            "armas_punho": nomes_punho,
            "bastoes_arcanos": nomes_bastoes,
            "clavas_leves": nomes_clavas,
            "clavas_pesadas": nomes_pesadas,
            "espadas_pesadas": nomes_pesadas,
            "machados_pesados": nomes_pesadas,
            "sobrevivencia": nomes_flecha,
        }
        nome = nomes_dict[dominio_key][idx-1]
        
        # Cooldown variavel
        cd = max(1, 14 - idx)
        
        linhas.append(f'HABILIDADES[{hab_id}] = {{')
        linhas.append(f'    nome = "{nome}",')
        linhas.append(f'    tipo = {"gatilho" if idx != 4 and idx != 8 and idx != 18 else "passiva"},')
        linhas.append(f'    dominio = {{{dom_id}}},')
        linhas.append(f'    cooldown = {cd},')
        linhas.append(f'    categoria = "{cat}",')
        
        if tipo_base in ("buff", "debuff", "heal", "field_aura", "trap"):
            linhas.append(f'    descricao = "{nome} do {cfg["nome"].lower()}.",')
        else:
            linhas.append(f'    descricao = "Ataca o alvo com {nome.lower()}."')
        
        # Efeito config
        if tipo_base == "buff":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "buff",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        elif tipo_base == "debuff":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "debuff",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        elif tipo_base == "field_aura":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "field_aura",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        elif tipo_base == "trap":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "trap",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        elif tipo_base == "storm":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "storm",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        elif tipo_base == "multi_hit":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "multi_hit",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        elif tipo_base == "cone":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "cone",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        elif tipo_base == "area_target":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "area_target",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        elif tipo_base == "explosion_ring":
            linhas.append('    efeitoConfig = {')
            linhas.append('        tipo = "explosion_ring",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        else:
            linhas.append('    efeitoConfig = {')
            linhas.append(f'        tipo = "{tipo_base}",')
            linhas.append(f'        dano = {dano_base},')
            linhas.append(f'        percentual = {percentual},')
            linhas.append(f'        elemento = {cfg["elemento"]},')
            linhas.append('    },')
        
        # Postura (variacao de dano por postura)
        linhas.append('    postura = {')
        if idx % 3 == 0:
            # Guarda-style: buff defense
            linhas.append(f'        [1] = {{ efeitoConfig = {{ dano = {round(dano_base * 0.7, 1)} }} }},')
            linhas.append(f'        [3] = {{ efeitoConfig = {{ dano = {round(dano_base * 1.3, 1)} }} }},')
        elif idx % 3 == 1:
            # Attack-style: dano extra
            linhas.append(f'        [1] = {{ efeitoConfig = {{ dano = {round(dano_base * 1.3, 1)} }} }},')
            linhas.append(f'        [3] = {{ efeitoConfig = {{ dano = {round(dano_base * 0.7, 1)} }} }},')
        else:
            linhas.append(f'        [1] = {{ efeitoConfig = {{ dano = {round(dano_base * 1.15, 1)} }} }},')
            linhas.append(f'        [3] = {{ efeitoConfig = {{ dano = {round(dano_base * 0.85, 1)} }} }},')
        linhas.append('    },')
        
        # Niveis (melhorias em marcos 5/10/15)
        if idx % 2 == 0:
            linhas.append('    niveis = {')
            linhas.append(f'        [5] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }},')
            linhas.append(f'        [10] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }},')
            linhas.append('    },')
        else:
            linhas.append('    niveis = {')
            linhas.append(f'        [5] = {{ {{ mod = "efeitoConfig", dano = "*1.1" }} }},')
            linhas.append(f'        [10] = {{ {{ mod = "efeitoConfig", raio = 1 }} }},')
            linhas.append(f'        [15] = {{ {{ mod = "efeitoConfig", critChance = 0.1 }} }},')
            linhas.append('    },')
        
        # Sinergias (cada habilidade tem 1-2)
        if idx % 4 == 0 and len(cfg["sinergias"]) >= 2:
            sin = cfg["sinergias"][0]
            linhas.append('    sinergias = {')
            linhas.append(f'        [{sin["dom"]}] = {{')
            linhas.append(f'            descricao = "{sin["desc"]}: dano elemental adicional.",')
            linhas.append(f'            nivelMin = 1,')
            linhas.append(f'            efeitoConfig = {{')
            linhas.append(f'                elemento = COMBAT_FIREDAMAGE,' if sin["dom"] == 23 else
                          f'                elemento = COMBAT_ICEDAMAGE,' if sin["dom"] == 24 else
                          f'                elemento = COMBAT_EARTHDAMAGE,' if sin["dom"] == 25 else
                          f'                elemento = COMBAT_ENERGYDAMAGE,' if sin["dom"] == 26 else
                          f'                elemento = {cfg["elemento"]},')
            linhas.append(f'                danoAdicional = {round(dano_base * 0.3, 1)},')
            linhas.append(f'            }},')
            linhas.append(f'        }},')
            linhas.append('    },')
        elif idx % 4 == 2 and len(cfg["sinergias"]) >= 3:
            sin = cfg["sinergias"][1]
            linhas.append('    sinergias = {')
            linhas.append(f'        [{sin["dom"]}] = {{')
            linhas.append(f'            descricao = "{sin["desc"]}: efeito adicional.",')
            linhas.append(f'            nivelMin = 5,')
            linhas.append(f'            efeitoConfig = {{')
            linhas.append(f'                dano = {round(dano_base * 1.2, 1)},')
            linhas.append(f'            }},')
            linhas.append(f'        }},')
            linhas.append('    },')
        
        # Estados (vinculo/lampejo para habilidades principais)
        if idx in (3, 10, 20):
            linhas.append('    estados = {')
            linhas.append('        vinculo = {')
            linhas.append(f'            efeitoConfig = {{ dano = {round(dano_base * 1.5, 1)}, damageType = "absolute" }},')
            linhas.append('        },')
            linhas.append('        lampejo = {')
            linhas.append(f'            efeitoConfig = {{ dano = {round(dano_base * 2.0, 1)}, custoMana = 0 }},')
            linhas.append('        },')
            linhas.append('    },')
        
        # Condicoes para habilidades especificas
        if idx == 5:
            linhas.append('    condicoes = {')
            linhas.append('        cercado = {')
            linhas.append(f'            efeitoConfig = {{ tipo = "explosion_ring", raio = 5, dano = {round(dano_base * 1.3, 1)} }},')
            linhas.append('        },')
            linhas.append('    },')
        elif idx == 15:
            linhas.append('    condicoes = {')
            linhas.append('        vidaBaixa = {')
            linhas.append(f'            efeitoConfig = {{ lifesteal = 0.3, dano = {round(dano_base * 1.4, 1)} }},')
            linhas.append('        },')
            linhas.append('    },')
        
        linhas.append('}')
        linhas.append('')
    
    # Print final
    linhas.append(f'print(">> SPA: habilidades/{dominio_key}.lua carregado")')
    linhas.append('')
    
    return "\n".join(linhas)

def main():
    os.makedirs(BASE, exist_ok=True)
    print(f"Gerando habilidades SHC em: {BASE}")
    print()
    
    for key, cfg in DOMINIOS.items():
        conteudo = gerar_habilidades(key, cfg)
        filepath = os.path.join(BASE, key + ".lua")
        
        # Backup do original
        if os.path.exists(filepath):
            bak = filepath + ".bak"
            if not os.path.exists(bak):
                os.rename(filepath, bak)
                print(f"  Backup: {key}.lua -> {key}.lua.bak")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        lines = conteudo.count('\n') + 1
        habs = conteudo.count('HABILIDADES[')
        print(f"  [OK] {key}.lua: {lines} linhas, {habs} habilidades")
    
    print()
    print("=== GERACAO CONCLUIDA ===")

if __name__ == "__main__":
    main()
