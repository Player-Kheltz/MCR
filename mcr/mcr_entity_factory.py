"""mcr.mcr_entity_factory — Fabrica de entidades.
Decide metodo de criacao baseado na spec (Tier 1/2/3).
Executa a criacao, valida e registra no world_state."""
import time
import os
from typing import Dict, Optional
from mcr.golden_templates import is_template_role, gerar_npc_canary, gerar_monstro_parametrizado
from mcr.golden_templates import salvar_npc_parametrizado, salvar_monstro_parametrizado
from mcr.mcr_world_state import registrar_entidade


def create_entity(spec: dict, world_state: dict) -> dict:
    """Cria uma entidade a partir de sua especificacao.
    
    Decisao de metodo:
        NPC Tier 1: golden template (role generico, sem quest)
        NPC Tier 2: codificar via pipeline (role especifico)
        NPC Tier 3: codificar + expandir_npc (com quest)
        Monster: golden template ou codificar
        Quest: expandir_npc no giver
    
    Args:
        spec: dict com type, name, role, etc. (vindo de idea_to_entity_spec)
        world_state: estado acumulado (para registrar)
    
    Returns:
        dict com sucesso, entidade, arquivo, tier, erros
    """
    tipo = spec.get('type', '')
    nome = spec.get('name', '') or spec.get('title', '')
    role = spec.get('role', '')

    if not nome:
        return {'sucesso': False, 'erro': 'Entidade sem nome', 'spec': spec}

    # ─── NPC ──────────────────────────────────────────────
    if tipo == 'npc':
        tem_quest_associada = bool(spec.get('quest'))
        
        if is_template_role(role) and not tem_quest_associada:
            return _criar_npc_template(spec)
        else:
            return _criar_npc_codificado(spec, tem_quest_associada)

    # ─── MONSTER ──────────────────────────────────────────
    elif tipo == 'monster':
        return _criar_monstro(spec)

    # ─── QUEST ────────────────────────────────────────────
    elif tipo == 'quest':
        return _criar_quest(spec)

    else:
        return {'sucesso': False, 'erro': 'Tipo desconhecido: %s' % tipo, 'spec': spec}


def _criar_npc_template(spec: dict) -> dict:
    """Tier 1: golden template, zero LLM."""
    import re as _re
    nome = spec.get('name', 'NPC')
    role = spec.get('role', '')
    shop_items = spec.get('shop_items', [])

    params = {
        'name': nome,
        'health': 100,
        'looktype': 128,
        'greeting': 'Ola, seja bem-vindo!',
        'job_desc': 'Sou %s e trabalho por aqui.' % role if role else 'Trabalho por aqui.',
        'shop_items': shop_items,
    }
    
    # Gera o codigo para validacao antes de salvar
    from mcr.mcr_world_builder import _validar_sintaxe, _validar_semantica
    codigo = gerar_npc_canary(params)
    valido, erro_sint = _validar_sintaxe(codigo)
    apis = _validar_semantica(codigo, 'npc')
    
    if valido and not apis:
        resultado_msg = salvar_npc_parametrizado(params)
        # Extrai caminho do arquivo da mensagem
        caminho_arquivo = str(resultado_msg).split('salvo em: ')[-1].strip() if 'salvo em:' in str(resultado_msg) else ''
        
        # Computa nome do arquivo sanitizado
        nome_arquivo_sanitizado = _re.sub(r'[^a-z0-9_]', '', nome.lower().replace(' ', '_')) + '.lua'
        caminho_completo = r'E:\MCR\server\data-otservbr-global\npc\%s' % nome_arquivo_sanitizado
        
        tamanho_arquivo = os.path.getsize(caminho_completo) if os.path.exists(caminho_completo) else 0
        
        # Registra no world_state
        registrar_entidade('npc', nome, {
            'file': caminho_completo,
            'role': role,
            'tier': 'template',
        })
        
        return {
            'sucesso': True,
            'entidade': nome,
            'tipo': 'npc',
            'tier': 'template',
            'arquivo': caminho_completo,
            'tamanho': tamanho_arquivo,
        }
    else:
        return {'sucesso': False, 'erro': 'Template invalido: sintaxe=%s apis=%s' % (
            erro_sint if not valido else 'OK',
            ', '.join(apis[:3]) if apis else 'OK'),
                'spec': spec}


def _criar_npc_codificado(spec: dict, tem_quest: bool = False) -> dict:
    """Tier 2/3: usa codificador do pipeline (LLM + golden examples + validacao)."""
    from mcr.mcr_world_builder import codificar, expandir_npc
    
    nome = spec.get('name', 'NPC')
    role = spec.get('role', 'figura do mundo')
    location = spec.get('location', 'regiao desconhecida')
    faction = spec.get('faction', '')
    
    papel = '%s de %s' % (role, location)
    if faction:
        papel += ' (Faccao: %s)' % faction
    
    tarefa = {
        'tipo': 'npc',
        'nome': nome,
        'papel': papel,
    }
    
    dossie = _montar_dossie(spec)
    resultado = codificar(tarefa, dossie)
    
    if not resultado.get('sucesso'):
        return {'sucesso': False, 'erro': resultado.get('erro', 'Falha na codificacao'),
                'spec': spec}
    
    # Registra no world_state
    registrar_entidade('npc', nome, {
        'file': resultado.get('arquivo', ''),
        'role': role,
        'tier': 'codificado',
        'quests': [],
    })
    
    retorno = {
        'sucesso': True,
        'entidade': nome,
        'tipo': 'npc',
        'tier': 'codificado',
        'arquivo': resultado.get('arquivo', ''),
        'tamanho': resultado.get('tamanho', 0),
        'tempo': resultado.get('tempo', 0),
    }
    
    # Tier 3: se tem quest associada, injeta via expandir_npc
    if tem_quest and spec.get('quest'):
        instrucao = (
            "Adicione a seguinte quest ao NPC '%s': %s. Objetivo: %s. Recompensa: %s." % (
                nome,
                spec['quest'].get('title', ''),
                spec['quest'].get('objective', ''),
                spec['quest'].get('reward', '')))
        resultado_q = expandir_npc(nome, instrucao)
        if resultado_q.get('sucesso'):
            retorno['tier'] = 'codificado+quest'
            retorno['quest_injetada'] = True
        else:
            retorno['quest_erro'] = resultado_q.get('erro', '')
    
    return retorno


def _criar_monstro(spec: dict) -> dict:
    """Cria monstro via golden template ou codificador."""
    nome = spec.get('name', 'Monster')
    habitat = spec.get('habitat', '')
    danger = spec.get('danger_level', 'medium')
    
    # Mapeia danger para stats
    health_map = {'low': 200, 'medium': 800, 'high': 3000}
    exp_map = {'low': 200, 'medium': 1500, 'high': 8000}
    
    params = {
        'name': nome,
        'health': health_map.get(danger, 500),
        'experience': exp_map.get(danger, 1000),
        'description': 'Um monstro encontrado em %s.' % habitat if habitat else 'Um monstro perigoso.',
        'looktype': 100,
        'race': 'blood',
    }
    
    # Tenta template primeiro
    from mcr.mcr_world_builder import _validar_sintaxe, _validar_semantica
    codigo = gerar_monstro_parametrizado(params)
    valido, _ = _validar_sintaxe(codigo)
    apis = _validar_semantica(codigo, 'monster')
    
    if valido and not apis:
        resultado = salvar_monstro_parametrizado(params)
        registrar_entidade('monster', nome, {
            'file': '',
            'habitat': habitat,
            'danger_level': danger,
        })
        return {
            'sucesso': True,
            'entidade': nome,
            'tipo': 'monster',
            'tier': 'template',
            'arquivo': resultado,
        }
    
    return {'sucesso': False, 'erro': 'Falha ao criar monstro', 'spec': spec}


def _criar_quest(spec: dict) -> dict:
    """Cria quest via expandir_npc no giver."""
    from mcr.mcr_world_builder import expandir_npc
    
    giver = spec.get('giver', '')
    title = spec.get('title', '')
    objective = spec.get('objective', '')
    reward = spec.get('reward', '')
    
    if not giver:
        return {'sucesso': False, 'erro': 'Quest sem giver', 'spec': spec}
    
    if not title:
        return {'sucesso': False, 'erro': 'Quest sem titulo', 'spec': spec}
    
    instrucao = (
        "Adicione uma quest ao NPC '%s'. "
        "Titulo: %s. Objetivo: %s. Recompensa: %s." % (
            giver, title, objective, reward))
    
    resultado = expandir_npc(giver, instrucao)
    
    if resultado.get('sucesso'):
        # Registra quest via world_event
        try:
            from mcr.mcr_world_foundation import world_event
            world_event('quest', title, new_state='active',
                        narrative="Quest '%s' disponivel com %s." % (title, giver),
                        source='entity_factory')
        except Exception:
            pass
        
        return {
            'sucesso': True,
            'entidade': title,
            'tipo': 'quest',
            'giver': giver,
            'tier': 'injection',
            'arquivo': resultado.get('arquivo', ''),
        }
    
    return {'sucesso': False, 'erro': resultado.get('erro', 'Falha ao injetar quest'),
            'spec': spec}


def _montar_dossie(spec: dict) -> str:
    """Monta dossie de contexto para o codificador a partir da spec."""
    contexto = []
    contexto.append("[CONTEXTO DA ENTIDADE]\n")
    for k, v in spec.items():
        if k not in ('type', 'quest') and v:
            contexto.append("%s: %s\n" % (k, v))
    
    # Se tem shop_items, formata
    shop = spec.get('shop_items', [])
    if shop:
        contexto.append("\nItens para vender:\n")
        for item in shop:
            contexto.append("  - %s (ID: %s)\n" % (item.get('name', '?'), item.get('clientId', '?')))
    
    contexto.append("\n[SUA TAREFA]\n")
    contexto.append("Escreva um script Lua para o servidor Canary para este NPC.\n")
    contexto.append("Use Game.createNpcType, npcConfig, keywordHandler, StdModule.\n")
    contexto.append("Nao invente APIs.\n")
    
    return ''.join(contexto)
