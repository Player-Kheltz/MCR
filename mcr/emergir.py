"""mcr.emergir — Motor de Criatividade (FASE 6).
Orquestra o ciclo: GERAR IDEIA -> ESCREVER CODIGO -> VALIDAR -> PROMOVER."""
import json
import os
import random
import time
from pathlib import Path
from typing import Dict, Optional, List
from collections import defaultdict

from mcr.config_llm import MODELO

from mcr.paths import (
    KG_DIR, SANDBOX_CRIATIVO_DIR, IDEAS_DIR, GOLDEN_EXAMPLES_DIR,
    DEVIA_KERNEL_DIR,
)
from mcr.encoding import write_file, read_file
from mcr.sanity_validator import SanityValidator


class Emergir:
    """Motor de Criatividade: gera ideias, escreve codigo, valida e promove."""

    def __init__(self, llm_func=None):
        self.llm_func = llm_func
        self.validator = SanityValidator()
        self._carregar_conceitos()
        SANDBOX_CRIATIVO_DIR.mkdir(parents=True, exist_ok=True)
        IDEAS_DIR.mkdir(parents=True, exist_ok=True)

    def _carregar_conceitos(self):
        """Carrega conceitos do KG para geracao de ideias."""
        self.conceitos = defaultdict(list)  # tipo -> [padroes]
        self.todos_api_calls = set()

        for fpath in sorted(KG_DIR.glob('patterns_*.json')):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                items = dados.get('padroes', dados if isinstance(dados, list) else [])
                for p in items:
                    tipo = p.get('tipo', 'generic')
                    self.conceitos[tipo].append(p)
                    for api in p.get('api_calls', []):
                        self.todos_api_calls.add(api.split('(')[0].strip().lower())
            except Exception:
                pass

        print(f'[Emergir] {sum(len(v) for v in self.conceitos.values())} conceitos em '
              f'{len(self.conceitos)} categorias')

    # ─── Estagio 1: Geracao da Ideia ───────────────────────────

    def gerar_ideia(self) -> Dict:
        """Gera uma ideia "E se...?" conectando dois conceitos distantes no KG.
        
        Returns:
            dict com 'ideia', 'conceito_a', 'conceito_b', 'descricao'
        """
        if len(self.conceitos) < 2:
            return self._ideia_fallback()

        # Pega dois tipos diferentes aleatoriamente
        tipos = list(self.conceitos.keys())
        tipo_a, tipo_b = random.sample(tipos, 2)

        # Pega um padrao de cada tipo
        padrao_a = random.choice(self.conceitos[tipo_a])
        padrao_b = random.choice(self.conceitos[tipo_b])

        # Extrai informacoes
        nome_a = Path(padrao_a.get('arquivo', '')).stem
        nome_b = Path(padrao_b.get('arquivo', '')).stem
        apis_a = padrao_a.get('api_calls', [])[:3]
        apis_b = padrao_b.get('api_calls', [])[:3]

        # Gera a ideia
        templates = [
            f"E se um {tipo_a} pudesse se transformar em um {tipo_b} quando ativado? "
            f"Usando {apis_a[0] if apis_a else 'trigger'} no primeiro e "
            f"{apis_b[0] if apis_b else 'callback'} no segundo.",

            f"E se um {tipo_a} como '{nome_a}' pudesse invocar um {tipo_b} como "
            f"'{nome_b}' quando um jogador interagisse com ele?",

            f"E se combinassemos as APIs de {tipo_a} ({apis_a[0] if apis_a else '?'}) "
            f"com as de {tipo_b} ({apis_b[0] if apis_b else '?'}) para criar "
            f"um comportamento hibrido nunca antes visto no servidor?",
        ]

        ideia = random.choice(templates)
        descricao = f"Conectar conceitos de '{tipo_a}' e '{tipo_b}' "

        return {
            'ideia': ideia,
            'conceito_a': {'tipo': tipo_a, 'nome': nome_a, 'apis': apis_a},
            'conceito_b': {'tipo': tipo_b, 'nome': nome_b, 'apis': apis_b},
            'descricao': descricao,
        }

    @staticmethod
    def _ideia_fallback() -> Dict:
        """Ideia generica quando o KG tem poucos conceitos."""
        return {
            'ideia': 'E se um NPC pudesse invocar monstros quando um jogador se aproximasse?',
            'conceito_a': {'tipo': 'npc', 'nome': 'guarda', 'apis': ['Game.createNpcType']},
            'conceito_b': {'tipo': 'monster', 'nome': 'goblin', 'apis': ['Game.createMonsterType']},
            'descricao': 'Cenario generico: NPC guarda que spawna monstros',
        }

    # ─── Estagio 2-3: Executar Ideia ──────────────────────────

    def executar_ideia(self, ideia: Dict, prompt_extra: str = '') -> Dict:
        """Executa o ciclo completo: LLM -> salvar -> validar -> promover.
        
        Args:
            ideia: dict retornado por gerar_ideia()
            prompt_extra: instrucoes extras para o LLM
        
        Returns:
            dict com resultado do ciclo
        """
        if not self.llm_func:
            return {'sucesso': False, 'erro': 'LLM nao disponivel', 'estagio': 'pre_llm'}

        # --- Estagio 2: LLM escreve codigo ---
        prompt = self._montar_prompt(ideia, prompt_extra)
        print(f'[Emergir] LLM gerando codigo para: {ideia["ideia"][:80]}...')

        t0 = time.time()
        try:
            codigo = self.llm_func(prompt, modelo=MODELO)
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'estagio': 'llm'}
        t1 = time.time()

        if not codigo or len(codigo) < 30:
            return {'sucesso': False, 'erro': 'Codigo gerado vazio', 'estagio': 'llm'}

        # Extrai bloco ```lua se presente
        if '```lua' in codigo:
            codigo = codigo.split('```lua')[1].split('```')[0]
        elif '```' in codigo:
            codigo = codigo.split('```')[1].split('```')[0]

        # --- Estagio 3: Salva no sandbox ---
        timestamp = int(time.time())
        nome_arquivo = f'ideia_{timestamp}.lua'
        caminho_sandbox = SANDBOX_CRIATIVO_DIR / nome_arquivo
        write_file(caminho_sandbox, codigo.strip(), language='lua')
        print(f'[Emergir] Codigo salvo em: {caminho_sandbox}')

        # --- Estagio 4: SanityValidator ---
        resultado_validacao = self.validator.validar_script(caminho_sandbox)
        print(f'[Emergir] Validacao: valido={resultado_validacao["valido"]}, '
              f'conhecidas={len(resultado_validacao["apis_conhecidas"])}, '
              f'desconhecidas={len(resultado_validacao["apis_desconhecidas"])}')

        if not resultado_validacao['valido']:
            # Rejeitado: registra e retorna
            resultado = {
                'sucesso': False,
                'erro': f'APIs desconhecidas: {resultado_validacao["apis_desconhecidas"][:5]}',
                'estagio': 'sanity_validator',
                'ideia': ideia,
                'arquivo': str(caminho_sandbox),
                'validacao': resultado_validacao,
                'tempo_llm': round(t1 - t0, 1),
            }
            # Registra no KG para aprendizado
            self._registrar_falha(resultado_validacao['apis_desconhecidas'], ideia)
            return resultado

        # --- Estagio 5: Promocao ---
        caminho_ideas = IDEAS_DIR / nome_arquivo
        # Adiciona cabecalho com a ideia
        cabecalho = f"-- IDEA: {ideia['ideia']}\n-- Conceitos: {ideia['conceito_a']['tipo']} + {ideia['conceito_b']['tipo']}\n-- Gerado por: MCR-DevIA Emergir\n\n"
        codigo_final = cabecalho + codigo.strip()
        write_file(caminho_ideas, codigo_final, language='lua')

        # Remove do sandbox (promovido)
        try:
            os.remove(caminho_sandbox)
        except Exception:
            pass

        print(f'[Emergir] IDEA PROMOVIDA: {caminho_ideas}')

        return {
            'sucesso': True,
            'ideia': ideia,
            'arquivo': str(caminho_ideas),
            'validacao': resultado_validacao,
            'tempo_llm': round(t1 - t0, 1),
        }

    def _montar_prompt(self, ideia: Dict, prompt_extra: str = '') -> str:
        """Monta o prompt para o LLM gerar o codigo da ideia."""
        golden = ""
        try:
            examples = list(GOLDEN_EXAMPLES_DIR.glob('*.lua'))
            if examples:
                ex = random.choice(examples)
                golden = read_file(ex)[:500]
        except Exception:
            pass

        prompt = (
            f"### IDEA CRIATIVA\n{ideia['ideia']}\n\n"
            f"Conceito A: {ideia['conceito_a']['tipo']} ({', '.join(ideia['conceito_a']['apis'][:3])})\n"
            f"Conceito B: {ideia['conceito_b']['tipo']} ({', '.join(ideia['conceito_b']['apis'][:3])})\n\n"
            f"### TAREFA\n"
            f"Escreva um script Lua para o servidor Canary que implemente esta ideia.\n"
            f"Use APENAS as APIs do Canary que voce conhece.\n"
            f"NAO invente funcoes. NAO use classes como Quest().\n"
            f"Use Action() para itens interativos, Game.createMonsterType() para monstros, "
            f"Game.createNpcType() para NPCs.\n\n"
        )
        if golden:
            prompt += f"### EXEMPLO DE API VALIDA\n{golden[:300]}\n...\n\n"
        if prompt_extra:
            prompt += f"### INSTRUCOES EXTRAS\n{prompt_extra}\n\n"
        prompt += "### CODIGO LUA (responda apenas com o codigo):"
        return prompt

    def _registrar_falha(self, apis_desconhecidas: List[str], ideia: Dict):
        """Registra uma falha de validacao no KG."""
        try:
            falhas_path = KG_DIR / 'emergir_falhas.json'
            falhas = []
            if falhas_path.exists():
                with open(falhas_path, 'r', encoding='utf-8') as f:
                    falhas = json.load(f)
            falhas.append({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'ideia': ideia['ideia'],
                'apis_desconhecidas': apis_desconhecidas,
            })
            with open(falhas_path, 'w', encoding='utf-8') as f:
                json.dump(falhas, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ─── Utilitarios ───────────────────────────────────────────

    def gerar_ideias_tematicas(self, conceitos: list, n: int = 10) -> list:
        """Gera ideias 'E se' combinando conceitos fornecidos.
        
        Args:
            conceitos: lista de strings (ex: ["comerciante", "armadilha", ...])
            n: numero maximo de ideias a retornar
        
        Returns:
            lista de dicts com 'ideia' (string) e 'conceito_a', 'conceito_b'
        """
        import random
        
        if len(conceitos) < 2:
            return [{'ideia': 'E se algo especial acontecesse neste mundo?',
                     'conceito_a': conceitos[0] if conceitos else 'mundo',
                     'conceito_b': 'destino'}]
        
        # Gera todas as combinacoes 2-a-2
        combinacoes = []
        for i in range(len(conceitos)):
            for j in range(i + 1, len(conceitos)):
                combinacoes.append((conceitos[i], conceitos[j]))
        
        random.shuffle(combinacoes)
        
        templates_ideia = [
            "E se um {a} pudesse se transformar em um {b} quando algo extraordinario acontecesse?",
            "E se um {a} e um {b} estivessem secretamente aliados em uma trama sombria?",
            "E se o maior {a} da cidade fosse, na verdade, um {b} disfarcado?",
            "E se um antigo {b} fosse descoberto dentro de um {a} abandonado?",
            "E se um {a} local precisasse da ajuda de um {b} para resolver uma crise iminente?",
            "E se um {a} e um {b} disputassem o controle da mesma regiao?",
            "E se um humilde {a} encontrasse um {b} magico que mudaria sua vida para sempre?",
            "E se um bando de {a} estivesse roubando {b} para financiar uma revolucao?",
            "E se um {a} fosse amaldicoado a se tornar um {b} toda noite?",
            "E se o comeco de um {a} dependesse da destruicao de um {b} ancestral?",
        ]
        
        ideias = []
        vistos = set()
        
        for a, b in combinacoes:
            if len(ideias) >= n * 3:  # Gera mais que o necessario para filtrar
                break
            template = random.choice(templates_ideia)
            # Alterna ordem para variedade
            if random.random() < 0.5:
                a, b = b, a
            ideia_texto = template.format(a=a, b=b)
            
            # Filtro de similaridade (Jaccard)
            palavras = set(ideia_texto.lower().split())
            similar = False
            for existente in vistos:
                pal_existente = set(existente.lower().split())
                inter = palavras & pal_existente
                uniao = palavras | pal_existente
                if len(inter) / len(uniao) > 0.6:
                    similar = True
                    break
            
            if not similar:
                vistos.add(ideia_texto)
                ideias.append({
                    'ideia': ideia_texto,
                    'conceito_a': a,
                    'conceito_b': b,
                })
        
        # Se ainda faltam ideias, complementa com variacoes LLM
        if len(ideias) < n:
            for a in conceitos:
                if len(ideias) >= n:
                    break
                ideias.append({
                    'ideia': "E se um %s misterioso aparecesse na cidade trazendo segredos do passado?" % a,
                    'conceito_a': a,
                    'conceito_b': 'misterio',
                })
        
        print('[Emergir] %d ideias geradas de %d combinacoes' % (
            min(len(ideias), n), len(combinacoes)))
        return ideias[:n]

    def estatisticas(self) -> Dict:
        """Retorna estatisticas do motor criativo."""
        sandbox_count = len(list(SANDBOX_CRIATIVO_DIR.glob('*.lua'))) if SANDBOX_CRIATIVO_DIR.exists() else 0
        ideas_count = len(list(IDEAS_DIR.glob('*.lua'))) if IDEAS_DIR.exists() else 0
        return {
            'conceitos': sum(len(v) for v in self.conceitos.values()),
            'categorias': len(self.conceitos),
            'sandbox_pendentes': sandbox_count,
            'ideias_promovidas': ideas_count,
            'apis_conhecidas': len(self.todos_api_calls),
        }


if __name__ == '__main__':
    """Modo standalone: gera uma ideia e mostra sem executar."""
    print('=' * 55)
    print('  EMERGIR — Motor de Criatividade')
    print('=' * 55)

    emergir = Emergir()
    stats = emergir.estatisticas()
    print(f'  Conceitos: {stats["conceitos"]} em {stats["categorias"]} categorias')
    print(f'  APIs conhecidas: {stats["apis_conhecidas"]}')

    print(f'\n--- Ideia Gerada ---')
    ideia = emergir.gerar_ideia()
    print(f'  {ideia["ideia"]}')
    print(f'  Conceito A: {ideia["conceito_a"]["nome"]} ({ideia["conceito_a"]["tipo"]})')
    print(f'  Conceito B: {ideia["conceito_b"]["nome"]} ({ideia["conceito_b"]["tipo"]})')
    print(f'\nPara executar esta ideia, forneca uma funcao LLM ao Emergir.executar_ideia()')
