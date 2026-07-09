"""mcr.mcr_world_seed — Semente do Mundo (World Seed Lite).
Gera uma semente minimalista a partir de um tema usando LLM Mistral.
Serve de ancora tematica para o pipeline iterativo de expansao."""
import json
import time
import urllib.request
from typing import Dict, List, Optional
from mcr.mcr_world_state import salvar_foundation

OLLAMA_CHAT = "http://localhost:11434/api/generate"
MODELO = "mistral:7b"


def generate_world_seed_lite(tema: str) -> dict:
    """Gera semente minimalista do mundo a partir de um tema.
    
    Chama Mistral com prompt estruturado para retornar:
        world_name, main_conflict, concepts (lista de 5-10 strings)
    
    Args:
        tema: descricao do mundo (ex: "Feira dos Mercadores de Eldoria")
    
    Returns:
        dict com world_name, main_conflict, concepts
    
    Raises:
        ValueError se falhar apos 2 tentativas
    """
    prompt = (
        "Gere uma semente de mundo de RPG no formato JSON abaixo.\n"
        "Retorne APENAS o JSON valido, sem comentarios, sem ```.\n\n"
        "{\n"
        '  "world_name": "Nome do mundo",\n'
        '  "main_conflict": "Conflito central em 1 frase",\n'
        '  "concepts": ["conceito1", "conceito2", ...]\n'
        "}\n\n"
        "Regras:\n"
        "- concepts deve ter 5 a 10 strings curtas (1-3 palavras cada) "
        "que representam papeis, lugares, temas, objetos ou faccoes "
        "presentes neste mundo.\n"
        "- Os conceitos devem ser DIVERSOS e concretos. "
        "Ex: comerciante, armadilha, floresta, moeda rara, guilda, "
        "contrabando, leilao, ferreiro, pocoes, mascara.\n"
        "- Nao use conceitos genericos como 'aventura' ou 'magia'.\n\n"
        "TEMA: %s\n\n" % tema
        + "JSON:"
    )

    for tentativa in range(2):
        print('[WorldSeed] Gerando semente (tentativa %d)...' % (tentativa + 1))
        try:
            payload = json.dumps({
                "model": MODELO, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.7, "max_tokens": 600}
            }).encode()
            req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            texto = resp.get('response', '').strip()
        except Exception as e:
            print('[WorldSeed] Erro LLM: %s' % e)
            continue

        # Extrai JSON
        if '```json' in texto:
            texto = texto.split('```json')[1].split('```')[0].strip()
        elif '```' in texto:
            texto = texto.split('```')[1].split('```')[0].strip()

        try:
            seed = json.loads(texto)
        except json.JSONDecodeError:
            print('[WorldSeed] JSON invalido. Retentando...')
            prompt += "\n\nERRO: JSON invalido. Use virgulas, aspas e colchetes corretos.\n"
            continue

        # Valida
        if not isinstance(seed.get('concepts'), list) or len(seed['concepts']) < 3:
            print('[WorldSeed] concepts < 3. Retentando...')
            prompt += "\n\nERRO: concepts deve ter pelo menos 5 itens.\n"
            continue

        seed.setdefault('world_name', 'Mundo sem nome')
        seed.setdefault('main_conflict', 'Conflito desconhecido')
        seed['theme'] = tema

        # Salva no world_state
        try:
            salvar_foundation({'world_seed_lite': seed})
        except Exception:
            pass

        print('[WorldSeed] Semente gerada: %s (%d conceitos)' % (
            seed['world_name'], len(seed['concepts'])))
        return seed

    raise ValueError("Falha ao gerar semente apos 2 tentativas")


if __name__ == '__main__':
    s = generate_world_seed_lite("Feira dos Mercadores")
    print(json.dumps(s, indent=2, ensure_ascii=False))
