"""Benchmark de modelos Ollama para OpenCode + MCR.
Mede velocidade E qualidade real das respostas.
"""
import json
import time
import sys
import re
from dataclasses import dataclass, field
from typing import Optional
try:
    import requests
except ImportError:
    import urllib.request as urllib_req
    requests = None

OLLAMA_URL = "http://localhost:11434/api/generate"

MODELOS = [
    "phi4-mini:latest",
    "qwen2.5-coder:1.5b",
    "mistral:7b",
    "llama3.1:8b",
    "deepseek-r1:7b",
    "qwen2.5-coder:7b",
    "qwen3:8b",
    "qwen3.5:9b",
    "gemma4:12b",
    "qwen2.5-coder:14b",
    "deepseek-r1:14b",
]


TAREFAS = [
    {
        "nome": "gerar_npc",
        "descricao": "Geração de JSON estruturado",
        "prompt": (
            "Crie um NPC ferreiro anão para um jogo medieval. "
            "Retorne APENAS um JSON válido com: nome, idade, personalidade (3 traços), "
            "especialidades (2 itens), fala_saudacao. NADA além do JSON."
        ),
    },
    {
        "nome": "explicar_codigo",
        "descricao": "Explicação de fórmula matemática",
        "prompt": (
            "Explique o que este código calcula, de forma concisa:\n"
            "```python\n"
            "def calcular_ponte(a, b, c, d, e):\n"
            "    return (a * b + c) / (d + 1) * (e ** 0.5)\n"
            "```"
        ),
    },
    {
        "nome": "revisar_codigo",
        "descricao": "Code review com detecção de O(n²)",
        "prompt": (
            "Revise este código. Aponte problemas de performance e boas práticas:\n"
            "```python\n"
            "def processar_lista(itens):\n"
            "    resultado = []\n"
            "    for i in range(len(itens)):\n"
            "        for j in range(len(itens)):\n"
            "            if itens[i] == itens[j] and i != j:\n"
            "                resultado.append(itens[i])\n"
            "    return resultado\n"
            "```"
        ),
    },
    {
        "nome": "gerar_lua",
        "descricao": "Geração de código Lua",
        "prompt": (
            "Gere um script Lua para um NPC em Tibia que saúda jogadores "
            "e oferece itens básicos (health potion, mana potion). "
            "Use a estrutura 'Interact' e 'onUse' do TFS. "
            "Retorne APENAS o código Lua, sem explicações."
        ),
    },
    {
        "nome": "raciocinar",
        "descricao": "Raciocínio matemático",
        "prompt": (
            "Se 3 NPCs vendem 5 itens cada, e cada item custa em média 25 moedas de ouro, "
            "quantas moedas um jogador precisa para comprar 2 itens de cada NPC? "
            "Mostre o raciocínio passo a passo."
        ),
    },
]


@dataclass
class Resultado:
    modelo: str
    tarefa: str
    tempo_total: float
    tokens_gerados: int
    tokens_por_segundo: float
    sucesso: bool
    erro: Optional[str] = None
    output: str = ""
    qualidade: dict = field(default_factory=dict)
    nota: float = 0.0
    truncou: bool = False


def query_ollama(modelo: str, prompt: str, timeout: int = 300) -> dict:
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_gpu": 999,
        },
    }
    inicio = time.time()
    try:
        if requests is not None:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            data = resp.json()
        else:
            body = json.dumps(payload).encode()
            req = urllib_req.Request(
                OLLAMA_URL, data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib_req.urlopen(req, timeout=timeout) as f:
                data = json.loads(f.read())
    except Exception as e:
        return {"erro": str(e), "tempo": time.time() - inicio}

    tempo = time.time() - inicio
    if "error" in data:
        return {"erro": data["error"], "tempo": tempo}

    response = data.get("response", "")
    eval_count = data.get("eval_count", 0)
    truncated = data.get("truncated", False)

    truncou = bool(truncated)

    return {
        "response": response,
        "eval_count": eval_count,
        "eval_duration": data.get("eval_duration", 0),
        "tempo": tempo,
        "truncou": truncou,
        "done_reason": data.get("done_reason", ""),
    }


# ─── Validadores de qualidade ───────────────────────────────────

def extrair_json(texto: str) -> Optional[dict]:
    # Tenta parsear o texto inteiro
    texto = texto.strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass
    # Tenta extrair bloco ```json ... ```
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', texto, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Tenta encontrar primeiro { ... } válido
    m = re.search(r'(\{.*\})', texto, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    return None


def avaliar_gerar_npc(output: str) -> dict:
    criterios = {}
    data = extrair_json(output)
    if data is None:
        return {
            "json_valido": False,
            "nota": 0,
            "detalhes": "JSON não encontrado na resposta",
        }

    criterios["json_valido"] = True
    checks = {
        "tem_nome": ("nome" in data and isinstance(data["nome"], str) and len(data["nome"]) > 0),
        "tem_idade": ("idade" in data and isinstance(data["idade"], (int, float))),
        "tem_personalidade": ("personalidade" in data and isinstance(data["personalidade"], list) and len(data["personalidade"]) >= 3),
        "tem_especialidades": ("especialidades" in data and isinstance(data["especialidades"], list) and len(data["especialidades"]) >= 2),
        "tem_fala": ("fala_saudacao" in data or "saudacao" in data),
    }
    criterios.update(checks)
    nota = sum(1 for v in checks.values() if v) / len(checks) * 10
    return {"nota": nota, **criterios}


def avaliar_explicar_codigo(output: str) -> dict:
    output_lower = output.lower()
    pontuacao = 0
    criterios = {}

    # Entende que é uma fórmula matemática
    if any(p in output_lower for p in ["fórmula", "formula", "calcular", "calcula", "equação", "expressão"]):
        pontuacao += 2
        criterios["identificou_formula"] = True
    else:
        criterios["identificou_formula"] = False

    # Identifica que (a*b + c) é numerador
    if any(p in output_lower for p in ["numerador", "a * b", "a*b", "multiplica", "produto"]):
        pontuacao += 2
        criterios["identificou_numerador"] = True
    else:
        criterios["identificou_numerador"] = False

    # Identifica que (d+1) é denominador
    if any(p in output_lower for p in ["denominador", "divide", "divisão", "divisao"]):
        pontuacao += 2
        criterios["identificou_denominador"] = True
    else:
        criterios["identificou_denominador"] = False

    # Identifica raiz quadrada
    if any(p in output_lower for p in ["raiz", "sqrt", "quadrada", "**0.5", "elevado a 0.5", "meio"]):
        pontuacao += 2
        criterios["identificou_raiz"] = True
    else:
        criterios["identificou_raiz"] = False

    # Explicação coesa (mínimo de qualidade textual)
    if len(output.split()) >= 30:
        pontuacao += 2
        criterios["explicacao_completa"] = True
    else:
        criterios["explicacao_completa"] = False

    nota = pontuacao
    return {"nota": nota, **criterios}


def avaliar_revisar_codigo(output: str) -> dict:
    output_lower = output.lower()
    pontuacao = 0
    criterios = {}

    # Detectou O(n²)
    if any(p in output_lower for p in ["o(n²)", "o(n^2)", "quadrático", "quadratico", "nested loop", "loop aninhado", "n²", "n^2"]):
        pontuacao += 3
        criterios["detectou_quadratico"] = True
    else:
        criterios["detectou_quadratico"] = False

    # Sugeriu otimização (set/dict)
    if any(p in output_lower for p in ["set", "dict", "hash", "o(n)", "o(1)", "complexidade"]):
        pontuacao += 2
        criterios["sugeriu_otimizacao"] = True
    else:
        criterios["sugeriu_otimizacao"] = False

    # Detectou duplicatas
    if any(p in output_lower for p in ["duplicata", "duplicado", "repetido", "repetição", "repeticao", "igual"]):
        pontuacao += 2
        criterios["detectou_duplicatas"] = True
    else:
        criterios["detectou_duplicatas"] = False

    # Sugeriu melhoria concreta
    if any(p in output_lower for p in ["sugiro", "recomendo", "melhor", "refatorar", "refatoraria", "alternativa"]):
        pontuacao += 1.5
        criterios["sugeriu_melhoria"] = True
    else:
        criterios["sugeriu_melhoria"] = False

    # Mencionou boas práticas
    if any(p in output_lower for p in ["boas práticas", "boas praticas", "legibilidade", "manutenção", "manutencao", "encapsulamento"]):
        pontuacao += 1.5
        criterios["mencionou_boas_praticas"] = True
    else:
        criterios["mencionou_boas_praticas"] = False

    nota = pontuacao
    return {"nota": nota, **criterios}


def avaliar_gerar_lua(output: str) -> dict:
    output_lower = output.lower()
    pontuacao = 0
    criterios = {}

    # Tem estrutura de função
    if any(p in output_lower for p in ["function", "onUse", "onUse=", "interact"]):
        pontuacao += 2
        criterios["tem_funcao"] = True
    else:
        criterios["tem_funcao"] = False

    # Tem sintaxe Lua válida (checagem básica)
    if "end" in output_lower and ("local" in output or "function" in output_lower):
        pontuacao += 2
        criterios["sintaxe_lua"] = True
    else:
        criterios["sintaxe_lua"] = False

    # Menciona itens específicos
    if any(p in output_lower for p in ["health", "mana", "potion", "poção", "pocao", "item"]):
        pontuacao += 2
        criterios["mencionou_itens"] = True
    else:
        criterios["mencionou_itens"] = False

    # Tem interação com jogador
    if any(p in output_lower for p in ["player", "cid", "creature", "say", "send", "msg", "fala"]):
        pontuacao += 2
        criterios["interacao_jogador"] = True
    else:
        criterios["interacao_jogador"] = False

    # É código puro (não misturou explicação)
    lines = output.strip().split('\n')
    code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith(('#', '--', '//')))
    if code_lines >= 10:
        pontuacao += 2
        criterios["codigo_substancial"] = True
    else:
        criterios["codigo_substancial"] = False

    nota = pontuacao
    return {"nota": nota, **criterios}


def avaliar_raciocinar(output: str) -> dict:
    output_lower = output.lower()
    pontuacao = 0
    criterios = {}

    # Resposta numérica correta (750)
    numeros = re.findall(r'(\d+)', output)
    if "750" in numeros:
        pontuacao += 3
        criterios["resposta_correta"] = True
    else:
        criterios["resposta_correta"] = False

    # Mostrou passo a passo
    if any(p in output_lower for p in ["passo", "etapa", "primeiro", "segundo", "terceiro", "1.", "2.", "3.", "x", "÷", "/", "*", "+", "-"]):
        pontuacao += 2
        criterios["passo_a_passo"] = True
    else:
        criterios["passo_a_passo"] = False

    # Entendeu que são 3 NPCs × 5 itens × 25 moedas × 2
    if "3" in output and "5" in output and "25" in output and "2" in output:
        pontuacao += 2
        criterios["usou_numeros_corretos"] = True
    else:
        criterios["usou_numeros_corretos"] = False

    # Explicação lógica coerente (mínimo de qualidade)
    if len(output.split()) >= 40:
        pontuacao += 1.5
        criterios["explicacao_coerente"] = True
    else:
        criterios["explicacao_coerente"] = False

    # Raciocínio alternativo ou verificação
    if any(p in output_lower for p in ["verifica", "confere", "total de", "total:", "resultado final", "portanto"]):
        pontuacao += 1.5
        criterios["verificou_resultado"] = True
    else:
        criterios["verificou_resultado"] = False

    nota = pontuacao
    return {"nota": nota, **criterios}


AVALIADORES = {
    "gerar_npc": avaliar_gerar_npc,
    "explicar_codigo": avaliar_explicar_codigo,
    "revisar_codigo": avaliar_revisar_codigo,
    "gerar_lua": avaliar_gerar_lua,
    "raciocinar": avaliar_raciocinar,
}


def testar_modelo(modelo: str, tarefas: list) -> list[Resultado]:
    resultados = []
    for tarefa in tarefas:
        nome = tarefa["nome"]
        print(f"  [{modelo}] {nome}... ", end="", flush=True)
        inicio = time.time()
        try:
            resp = query_ollama(modelo, tarefa["prompt"])
            tempo_total = time.time() - inicio

            if "erro" in resp:
                print(f"FALHA: {resp['erro'][:60]}")
                resultados.append(Resultado(
                    modelo=modelo, tarefa=nome,
                    tempo_total=tempo_total, tokens_gerados=0,
                    tokens_por_segundo=0, sucesso=False, erro=resp["erro"],
                ))
                continue

            output = resp.get("response", "")
            tokens = resp.get("eval_count", 0)
            tps = tokens / tempo_total if tempo_total > 0 else 0
            truncou = resp.get("truncou", False)

            avaliador = AVALIADORES.get(nome)
            qualidade = avaliador(output) if avaliador else {"nota": 0}
            nota = qualidade.get("nota", 0)

            status = f"{tokens}tok {tps:.0f}tok/s"
            if truncou:
                status += " [TRUNCOU]"
            status += f" qual:{nota:.0f}/10"
            print(status)

            resultados.append(Resultado(
                modelo=modelo, tarefa=nome,
                tempo_total=tempo_total, tokens_gerados=tokens,
                tokens_por_segundo=tps, sucesso=True, output=output[:500],
                qualidade=qualidade, nota=nota, truncou=truncou,
            ))

        except Exception as e:
            tempo_total = time.time() - inicio
            print(f"ERRO: {e}")
            resultados.append(Resultado(
                modelo=modelo, tarefa=nome,
                tempo_total=tempo_total, tokens_gerados=0,
                tokens_por_segundo=0, sucesso=False, erro=str(e),
            ))
    return resultados


def gerar_relatorio(todos_resultados: dict[str, list[Resultado]]):
    print("\n" + "=" * 100)
    print("BENCHMARK COMPLETO - VELOCIDADE + QUALIDADE")
    print("=" * 100)

    # ─── Ranking geral (qualidade + velocidade ponderada) ─────
    print("\n>>> RANKING GERAL (nota qualidade + velocidade ponderada)")

    modelos_score = []
    for modelo, resultados in todos_resultados.items():
        sucessos = [r for r in resultados if r.sucesso]
        if not sucessos:
            continue
        media_qualidade = sum(r.nota for r in sucessos) / len(sucessos)
        media_tps = sum(r.tokens_por_segundo for r in sucessos) / len(sucessos)
        # Score: 70% qualidade, 30% velocidade (normalizada)
        max_tps = max(
            sum(r.tokens_por_segundo for r in todos_resultados[m] if r.sucesso)
            / max(len([rr for rr in todos_resultados[m] if rr.sucesso]), 1)
            for m in todos_resultados
        ) or 1
        score = media_qualidade * 0.7 + (media_tps / max_tps * 10) * 0.3
        truncamentos = sum(1 for r in sucessos if r.truncou)
        modelos_score.append({
            "modelo": modelo,
            "score": score,
            "qualidade": media_qualidade,
            "tps": media_tps,
            "tempo_medio": sum(r.tempo_total for r in sucessos) / len(sucessos),
            "truncou": truncamentos,
        })

    modelos_score.sort(key=lambda x: x["score"], reverse=True)

    print(f"{'#':<3} {'Modelo':<42} {'Score':<8} {'Qual':<8} {'Tok/s':<8} {'Tempo':<8} {'Trunc':<6}")
    print("-" * 100)
    for i, m in enumerate(modelos_score, 1):
        trunc_flag = f" {m['truncou']}x" if m['truncou'] else "  -"
        print(f"{i:<3} {m['modelo']:<42} {m['score']:<8.1f} {m['qualidade']:<8.1f} {m['tps']:<8.1f} {m['tempo_medio']:<8.1f}s{trunc_flag}")

    # ─── Detalhes por tarefa ─────────────────────────────────
    print("\n" + "=" * 100)
    print("DETALHES POR TAREFA")
    print("=" * 100)

    tarefas_nomes = [t["nome"] for t in TAREFAS]
    for tarefa in tarefas_nomes:
        print(f"\n>>> {tarefa}")
        best_modelo = None
        best_nota = -1

        for modelo in sorted(todos_resultados.keys()):
            rs = [r for r in todos_resultados[modelo] if r.tarefa == tarefa]
            if not rs or not rs[0].sucesso:
                continue
            r = rs[0]
            nota_str = f"{r.nota:.0f}/10"
            trunc_str = " [TRUNCOU]" if r.truncou else ""
            print(f"  {modelo:<42} qual:{nota_str:<6} {r.tokens_por_segundo:<6.1f}tok/s {r.tempo_total:<6.1f}s{trunc_str}")

            if r.nota > best_nota:
                best_nota = r.nota
                best_modelo = modelo

        if best_modelo:
            print(f"  {'=> Melhor:':<10} {best_modelo:<42} (nota {best_nota:.0f}/10)")

    # ─── Análise de truncamento ──────────────────────────────
    print("\n" + "=" * 100)
    print("ANÁLISE DE TRUNCAMENTO (respostas cortadas)")
    print("=" * 100)
    tem_trunc = False
    for modelo, resultados in todos_resultados.items():
        truncados = [r for r in resultados if r.truncou]
        if truncados:
            tem_trunc = True
            tarefas_t = [f"{r.tarefa}({r.tokens_gerados}tok)" for r in truncados]
            print(f"  {modelo:<42} → {', '.join(tarefas_t)}")
    if not tem_trunc:
        print("  Nenhum modelo truncou com limite de 2048 tokens.")

    # ─── Notas detalhadas ────────────────────────────────────
    print("\n" + "=" * 100)
    print("NOTAS DETALHADAS POR CRITÉRIO")
    print("=" * 100)
    for tarefa in tarefas_nomes:
        print(f"\n>>> {tarefa}")
        header_exibido = False
        for modelo in sorted(todos_resultados.keys()):
            rs = [r for r in todos_resultados[modelo] if r.tarefa == tarefa]
            if not rs or not rs[0].sucesso:
                continue
            r = rs[0]
            q = r.qualidade
            criterios = {k: v for k, v in q.items() if k != "nota" and isinstance(v, bool)}
            ativos = [k for k, v in criterios.items() if v]
            if not header_exibido:
                print(f"  {'Modelo':<42} {'Nota':<6} {'Acertos'}")
                print(f"  {'-'*42} {'-'*6} {'-'*30}")
                header_exibido = True
            print(f"  {modelo:<42} {r.nota:<6.0f} {', '.join(ativos)}")

    # ─── Resumo final e recomendação ─────────────────────────
    print("\n" + "=" * 100)
    print("RESUMO FINAL E RECOMENDAÇÃO")
    print("=" * 100)

    if modelos_score:
        melhor = modelos_score[0]
        print(f"\n== Melhor geral: {melhor['modelo']}")
        print(f"   Score: {melhor['score']:.1f} | Qualidade: {melhor['qualidade']:.1f}/10 | {melhor['tps']:.1f} tok/s")

        # Categorias
        leves = [m for m in modelos_score if "1.5" in m["modelo"] or "mini" in m["modelo"] or "7b" in m["modelo"]]
        medios = [m for m in modelos_score if "8b" in m["modelo"] or "9b" in m["modelo"] or "12b" in m["modelo"]]
        pesados = [m for m in modelos_score if "14b" in m["modelo"] or "30b" in m["modelo"] or "30B" in m["modelo"]]

        if leves:
            melhor_leve = max(leves, key=lambda x: x["score"])
            print(f"   -> Melhor leve (<5GB): {melhor_leve['modelo']} (qual:{melhor_leve['qualidade']:.1f} tps:{melhor_leve['tps']:.0f})")
        if medios:
            melhor_medio = max(medios, key=lambda x: x["score"])
            print(f"   -> Melhor medio (5-10GB): {melhor_medio['modelo']} (qual:{melhor_medio['qualidade']:.1f} tps:{melhor_medio['tps']:.0f})")
        if pesados:
            melhor_pesado = max(pesados, key=lambda x: x["score"])
            print(f"   -> Melhor pesado (>10GB): {melhor_pesado['modelo']} (qual:{melhor_pesado['qualidade']:.1f} tps:{melhor_pesado['tps']:.0f})")

        # Melhor qualidade pura
        melhor_qualidade = max(modelos_score, key=lambda x: x["qualidade"])
        mais_rapido = max(modelos_score, key=lambda x: x["tps"])
        print(f"\n   => Melhor qualidade pura: {melhor_qualidade['modelo']} ({melhor_qualidade['qualidade']:.1f}/10)")
        print(f"   => Mais rapido: {mais_rapido['modelo']} ({mais_rapido['tps']:.0f} tok/s)")

    print(f"\nResultados salvos em benchmark_resultados.json")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark Ollama para OpenCode + MCR")
    parser.add_argument("--modelos", nargs="+", help="Modelos específicos")
    parser.add_argument("--tarefa", help="Apenas uma tarefa")
    args = parser.parse_args()

    modelos = args.modelos or MODELOS
    tarefas = [t for t in TAREFAS if t["nome"] == args.tarefa] if args.tarefa else TAREFAS

    print(f"Modelos: {len(modelos)}  |  Tarefas: {len(tarefas)}")
    print(f"Limite: NENHUM (resposta completa) | Temp: 0.3")
    for m in modelos:
        print(f"  - {m}")

    todos_resultados = {}
    for modelo in modelos:
        print(f"\n{'=' * 60}")
        print(f"Testando: {modelo}")
        print(f"{'=' * 60}")
        try:
            resultados = testar_modelo(modelo, tarefas)
            todos_resultados[modelo] = resultados
        except Exception as e:
            print(f"FALHA CATASTRÓFICA: {e}")
            continue

    gerar_relatorio(todos_resultados)

    relatorio = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modelos": {},
    }
    for modelo, resultados in todos_resultados.items():
        relatorio["modelos"][modelo] = [
            {
                "tarefa": r.tarefa,
                "tempo_total": r.tempo_total,
                "tokens_gerados": r.tokens_gerados,
                "tokens_por_segundo": r.tokens_por_segundo,
                "sucesso": r.sucesso,
                "erro": r.erro,
                "nota": r.nota,
                "qualidade": r.qualidade,
                "truncou": r.truncou,
            }
            for r in resultados
        ]

    with open("benchmark_resultados.json", "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)

    print(f"\nResultados salvos em benchmark_resultados.json")


if __name__ == "__main__":
    main()
