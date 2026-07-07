"""Comando: gerar_componentes - Pre-gera componentes usando Orquestrador Universal.
Cria personagens, locais, artefatos e salva no KG."""
import os, json, re
from modulos.util import fast as _fast

def register():
    return {
        "name": "gerar_componentes",
        "desc": "Pre-gera componentes para historias (personagens, locais, artefatos) via Orquestrador Universal",
        "handler": execute,
        "args": [{"name": "tema", "type": "str", "required": True}],
        "categoria": "criatividade",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args or not kg:
        print('[Componentes] Uso: gerar_componentes <tema>')
        return True
    
    tema = ' '.join(args)
    print(f'[Componentes] Gerando componentes para: {tema}')
    
    # 1. Verifica se ja existem componentes no KG
    existentes = kg.buscar(tema, max_r=5)
    componentes_existentes = [l for l in existentes if l.get('ctx') == 'componente_historia']
    
    if componentes_existentes:
        print(f'  {len(componentes_existentes)} componentes ja existentes no KG')
        for c in componentes_existentes:
            print(f'    - {c.get("erro","")}: {c.get("solucao","")}')
        print('  Reutilizando componentes existentes.')
        return True
    
    # Funcao auxiliar para gerar via orquestrador ou fallback
    def _gerar_tipo(tipo_template, label):
        if ia and hasattr(ia, 'orquestrar'):
            r = ia.orquestrar(tipo_template, {"tema": tema}, consulta=f"{tema} {label}", temp=0.3)
            if r:
                return r
        # Fallback: fast direto
        prompts_fallback = {
            "componentes_personagens": (
                f"Crie 3 personagens para uma historia sobre {tema} em Tibia. "
                f"Cada um com: nome proprio, funcao, personalidade. "
                f"Formato: Nome: [nome] | Funcao: [funcao] | Personalidade: [personalidade]"
            ),
            "componentes_locais": (
                f"Crie 2 locais para uma historia sobre {tema} em Tibia. "
                f"Cada um com: nome do local, descricao, significado. "
                f"Formato: Local: [nome] | Descricao: [descricao]"
            ),
            "componentes_artefatos": (
                f"Crie 2 artefatos ou eventos importantes para uma historia sobre {tema} em Tibia. "
                f"Cada um com: nome, descricao, poder/significado. "
                f"Formato: Artefato: [nome] | Descricao: [descricao]"
            ),
        }
        prompt = prompts_fallback.get(tipo_template, prompts_fallback["componentes_personagens"])
        return _fast(prompt, 0.3, "leve") or ""
    
    # 2. Personagens
    print('  Gerando personagens...')
    personagens = _gerar_tipo("componentes_personagens", "personagens")
    if personagens:
        kg.aprender(erro=f"Personagens para: {tema}", causa=f"Pre-gerado por orquestrador",
                    solucao=personagens, ctx="componente_historia")
        print(f'    Personagens salvos no KG')
    
    # 3. Locais
    print('  Gerando locais...')
    locais = _gerar_tipo("componentes_locais", "locais")
    if locais:
        kg.aprender(erro=f"Locais para: {tema}", causa=f"Pre-gerado por orquestrador",
                    solucao=locais, ctx="componente_historia")
        print(f'    Locais salvos no KG')
    
    # 4. Artefatos/eventos
    print('  Gerando artefatos...')
    artefatos = _gerar_tipo("componentes_artefatos", "artefatos")
    if artefatos:
        kg.aprender(erro=f"Artefatos para: {tema}", causa=f"Pre-gerado por orquestrador",
                    solucao=artefatos, ctx="componente_historia")
        print(f'    Artefatos salvos no KG')
    
    print(f'[Componentes] Geracao concluida.')
    return True
