"""
    Melhora habilidades SHC de dominios de arma:
    Adiciona sinergias, estados, condicoes e melhora postura/niveis
    Uso: python melhorar_habilidades_shc.py
"""
import os, re

BASE = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'

# Config de melhoria por dominio
MELHORIAS = {
    "arcos": {
        "sinergias": [
            (23, "Fogo", "Flecha Incendiaria: dano de fogo adicional", 1, "COMBAT_FIREDAMAGE", 0.3),
            (24, "Gelo", "Flecha Congelante: lentidao adicional", 3, None, 0),
            (26, "Energia", "Flecha Eletrica: dano em cadeia", 5, "COMBAT_ENERGYDAMAGE", 0.25),
        ],
        "estados_ids": {3, 6, 10},
        "condicoes_ids": {5, 8},
    },
    "lutador": {
        "sinergias": [
            (14, "ArtesMarciais", "Golpes Marciais: dano de impacto extra", 1, None, 0.2),
            (132, "ArmasDePunho", "Soco Potente: chance de atordoar", 3, None, 0),
            (1, "Combate", "Furia do Combate: dano progressivo", 5, None, 0.15),
        ],
        "estados_ids": {2, 6, 10},
        "condicoes_ids": {4, 7, 9},
    },
    "armas_punho": {
        "sinergias": [
            (130, "Lutador", "Punhos do Lutador: multi-hit extra", 1, None, 0),
            (14, "ArtesMarciais", "Agilidade Marcial: velocidade de ataque", 3, None, 0),
            (26, "Energia", "Punhos Eletricos: dano de energia", 5, "COMBAT_ENERGYDAMAGE", 0.3),
        ],
        "estados_ids": {3, 7, 10},
        "condicoes_ids": {6, 9},
    },
    "bastoes_arcanos": {
        "sinergias": [
            (23, "Fogo", "Bastao de Fogo: dano de fogo", 1, "COMBAT_FIREDAMAGE", 0.35),
            (24, "Gelo", "Bastao de Gelo: dano de gelo com lentidao", 3, "COMBAT_ICEDAMAGE", 0.3),
            (26, "Energia", "Bastao de Energia: dano em area", 5, "COMBAT_ENERGYDAMAGE", 0.25),
            (200, "SagradoMorte", "Poder Sagrado: dano extra vs mortos-vivos", 7, "COMBAT_HOLYDAMAGE", 0.4),
        ],
        "estados_ids": {3, 8, 10},
        "condicoes_ids": {5, 9},
    },
    "clavas_leves": {
        "sinergias": [
            (113, "ClavasPesadas", "Impacto Pesado: dano de impacto extra", 1, None, 0.2),
            (25, "Terra", "Golpe Terrestre: dano de terra adicional", 3, "COMBAT_EARTHDAMAGE", 0.3),
        ],
        "estados_ids": {4, 8, 10},
        "condicoes_ids": {6},
    },
    "clavas_pesadas": {
        "sinergias": [
            (112, "ClavasLeves", "Agilidade da Clava: velocidade+", 1, None, 0),
            (25, "Terra", "Impacto Sismico: area de efeito maior", 3, None, 0),
        ],
        "estados_ids": {3, 7, 10},
        "condicoes_ids": {5, 9},
    },
    "espadas_pesadas": {
        "sinergias": [
            (100, "EspadasLeves", "Corte Rapido: velocidade de ataque", 1, None, 0),
            (23, "Fogo", "Laminas Incendiarias: dano de fogo", 3, "COMBAT_FIREDAMAGE", 0.3),
            (200, "SagradoMorte", "Laminas Sagradas: dano sagrado", 5, "COMBAT_HOLYDAMAGE", 0.25),
        ],
        "estados_ids": {3, 6, 10},
        "condicoes_ids": {5, 8},
    },
    "machados_pesados": {
        "sinergias": [
            (110, "MachadosLeves", "Machado Rapido: velocidade de ataque", 1, None, 0),
            (25, "Terra", "Machado da Terra: dano de terra", 3, "COMBAT_EARTHDAMAGE", 0.3),
        ],
        "estados_ids": {4, 7, 10},
        "condicoes_ids": {5, 9},
    },
    "sobrevivencia": {
        "sinergias": [
            (24, "Gelo", "Sobrevivencia Glacial: resistencia ao frio", 3, None, 0),
            (25, "Terra", "Rastreamento Terrestre: dano de veneno", 5, "COMBAT_EARTHDAMAGE", 0.25),
            (120, "Arcos", "Pontaria Selvagem: precisao aumentada", 1, None, 0),
        ],
        "estados_ids": {3, 6, 10},
        "condicoes_ids": {5, 8},
    },
}

def melhorar_arquivo(filepath, config):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    linhas = content.split('\n')
    novas_linhas = []
    i = 0
    
    while i < len(linhas):
        linha = linhas[i]
        novas_linhas.append(linha)
        
        # Detecta inicio de uma habilidade: HABILIDADES[ID] = {
        m = re.match(r'HABILIDADES\[(\d+)\]\s*=\s*\{', linha)
        if m:
            hab_id = int(m.group(1))
            # Extrai os 2 ultimos digitos como indice (1-20)
            idx = hab_id % 100
            if idx == 0: idx = 100  # 40000 -> na verdade 40001-40020
            # Normaliza: 12001 -> 1, 12010 -> 10, 40020 -> 20
            hab_idx = hab_id % 100
            if hab_idx == 0: hab_idx = 100
            
            # Encontra onde a habilidade termina (fecha chave)
            brace_count = 1
            j = i + 1
            while j < len(linhas) and brace_count > 0:
                brace_count += linhas[j].count('{') - linhas[j].count('}')
                j += 1
            # j agora aponta para a linha apos o fechamento da habilidade
            
            # Insere melhorias ANTES do fechamento
            insercoes = []
            
            # 1. Sinergias
            sinergias = config.get("sinergias", [])
            for sin_dom, sin_nome, sin_desc, sin_nivel, sin_elem, sin_dano in sinergias:
                if hab_idx % sin_dom % 5 == 0 or hab_idx == sin_dom % 20:
                    insercoes.append(f'    sinergias = {{')
                    insercoes.append(f'        [{sin_dom}] = {{')
                    insercoes.append(f'            descricao = "{sin_desc}",')
                    insercoes.append(f'            nivelMin = {sin_nivel},')
                    if sin_elem:
                        insercoes.append(f'            efeitoConfig = {{')
                        insercoes.append(f'                elemento = {sin_elem},')
                        insercoes.append(f'                danoAdicional = {sin_dano},')
                        insercoes.append(f'            }},')
                    else:
                        insercoes.append(f'            efeitoConfig = {{')
                        insercoes.append(f'                dano = 1.0 + {sin_dano},')
                        insercoes.append(f'            }},')
                    insercoes.append(f'        }},')
                    insercoes.append(f'    }},')
                    break  # max 1 sinergia por habilidade
            
            # 2. Estados (vinculo/lampejo)
            if hab_idx in config.get("estados_ids", set()):
                # Encontra o dano base da habilidade
                dano_match = re.search(r'dano\s*=\s*([\d.]+)', content[i:j])
                dano_base = float(dano_match.group(1)) if dano_match else 1.0
                
                insercoes.append(f'    estados = {{')
                insercoes.append(f'        vinculo = {{')
                insercoes.append(f'            efeitoConfig = {{ dano = {round(dano_base * 1.5, 1)}, damageType = "absolute" }},')
                insercoes.append(f'        }},')
                insercoes.append(f'        lampejo = {{')
                insercoes.append(f'            efeitoConfig = {{ dano = {round(dano_base * 2.0, 1)}, custoMana = 0 }},')
                insercoes.append(f'        }},')
                insercoes.append(f'    }},')
            
            # 3. Condicoes
            if hab_idx in config.get("condicoes_ids", set()):
                if hab_idx % 3 == 0:
                    insercoes.append(f'    condicoes = {{')
                    insercoes.append(f'        vidaBaixa = {{')
                    insercoes.append(f'            efeitoConfig = {{ lifesteal = 0.3, dano = {round(dano_base * 1.4, 1)} }},')
                    insercoes.append(f'        }},')
                    insercoes.append(f'    }},')
                else:
                    insercoes.append(f'    condicoes = {{')
                    insercoes.append(f'        cercado = {{')
                    insercoes.append(f'            efeitoConfig = {{ tipo = "explosion_ring", raio = 5, dano = {round(dano_base * 1.3, 1)} }},')
                    insercoes.append(f'        }},')
                    insercoes.append(f'    }},')
            
            if insercoes:
                # Insere antes do fechamento da habilidade
                novas_linhas.extend(insercoes)
                # Pula ate o final da habilidade
                i = j - 1  # vai processar a linha de fechamento no loop
        
        i += 1
    
    return '\n'.join(novas_linhas)

def main():
    print("Melhorando habilidades SHC com sinergias, estados e condicoes...")
    print()
    
    for nome, config in MELHORIAS.items():
        filepath = os.path.join(BASE, nome + ".lua")
        if not os.path.exists(filepath):
            print(f"  [!] {nome}.lua nao encontrado")
            continue
        
        # Backup
        bak = filepath + ".bak2"
        if not os.path.exists(bak):
            with open(filepath, 'r', encoding='utf-8') as f:
                original = f.read()
            with open(bak, 'w', encoding='utf-8') as f:
                f.write(original)
        
        conteudo = melhorar_arquivo(filepath, config)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        sin_count = conteudo.count('sinergias = {')
        est_count = conteudo.count('estados = {')
        cond_count = conteudo.count('condicoes = {')
        print(f"  [OK] {nome}.lua: +{sin_count} sinergias, +{est_count} estados, +{cond_count} condicoes")
    
    print()
    print("=== MELHORIA CONCLUIDA ===")

if __name__ == "__main__":
    main()
