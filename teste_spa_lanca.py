"""Teste: MCR-DevIA cria habilidade SPA — Lanca das Sombras (Morte)."""
import sys, os, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import _llm, _decider, _validator

pergunta = "Crie uma habilidade chamada Lanca das Sombras para o dominio Morte (id 6). Nivel minimo 10. E uma habilidade single-target do tipo dano_extra. Deve aplicar condicao de vida drenada life_leech 15%. Foco minimo 50%. Use o motor_habilidades.lua v2.0 e respeite o campo categoria."

# 1. Classifica
classe, conf = _decider.classificar(pergunta)
print(f'[CLASSIFICACAO] {classe} (conf={conf:.2f})')

# 2. Encontra habilidades reais do Canary para usar como exemplo
habilidades_dir = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
exemplos = []
for f in sorted(os.listdir(habilidades_dir)):
    if not f.endswith('.lua'):
        continue
    caminho = os.path.join(habilidades_dir, f)
    with open(caminho, 'r', encoding='iso-8859-1', errors='replace') as fh:
        conteudo = fh.read()
    # Pega uma habilidade de exemplo que tenha efeitoConfig com life_leech ou dano_extra
    if 'life_leech' in conteudo or ('dano_extra' in conteudo and 'efeitoConfig' in conteudo):
        # Extrai so a primeira habilidade do arquivo (ate o primeiro HABILIDADES[...] = {
        import re
        match = re.search(r'HABILIDADES\[\d+\]\s*=\s*\{', conteudo)
        if match:
            start = match.start()
            # Encontra o fechamento
            depth = 0
            end = start
            for i in range(start, len(conteudo)):
                if conteudo[i] == '{':
                    depth += 1
                elif conteudo[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            trecho = conteudo[start:end]
            if len(trecho) > 100:
                exemplos.append((f, trecho))
        if len(exemplos) >= 3:
            break

if not exemplos:
    # Fallback: usa qualquer habilidade
    for f in sorted(os.listdir(habilidades_dir))[:5]:
        caminho = os.path.join(habilidades_dir, f)
        with open(caminho, 'r', encoding='iso-8859-1', errors='replace') as fh:
            conteudo = fh.read()
        import re
        match = re.search(r'HABILIDADES\[\d+\]\s*=\s*\{[\s\S]*?\n\}', conteudo)
        if match:
            trecho = match.group(0)[:1500]
            if len(trecho) > 100 and 'efeitoConfig' in trecho:
                exemplos.append((f, trecho))
                break

print(f'[EXEMPLOS] {len(exemplos)} habilidades encontradas')
for nome, _ in exemplos:
    print(f'  - {nome}')

if exemplos:
    nome_ex, codigo_ex = exemplos[0]
    if len(codigo_ex) > 1500:
        codigo_ex = codigo_ex[:1500]
    
    prompt = (
        f"Aqui esta um exemplo real de habilidade SPA do Canary:\n\n"
        f"=== EXEMPLO ({nome_ex}) ===\n"
        f"{codigo_ex}\n=== FIM EXEMPLO ===\n\n"
        f"Baseado neste exemplo, crie uma nova habilidade:\n"
        f"- Nome: 'Lanca das Sombras'\n"
        f"- Dominio: Morte (id 6)\n"
        f"- Nivel minimo: 10\n"
        f"- Tipo: gatilho\n"
        f"- Categoria: single\n"
        f"- Tipo de efeito: dano_extra\n"
        f"- life_leech: 15%%\n"
        f"- Foco minimo: 50%%\n"
        f"- Use o campo efeitoConfig com tipo=\"dano_extra\"\n"
        f"- Respeite o formato HABILIDADES[ID] = { ... }\n"
        f"- Responda APENAS com o codigo Lua da habilidade.\n"
    )
    
    t0 = time.time()
    resp = _llm.gerar(prompt, modelo='qwen2.5-coder:7b', temp=0.3)
    t = time.time() - t0
    
    val = _validator.validar(pergunta, resp, codigo_ex[:500])
    
    print(f'\n[TEMPO] {t:.1f}s')
    print(f'[VALIDACAO] sim={val["similaridade"]:.3f} valido={val["valida"]}')
    print(f'\n=== CODIGO GERADO ===')
    print(resp[:2000])
    print(f'\n=== FIM ===')
    
    # Checks
    checks = [
        ('HABILIDADES[ID]', 'HABILIDADES' in resp and 'ID' in resp),
        ('nome = Lanca das Sombras', 'Lanca das Sombras' in resp or 'Lanca' in resp),
        ('dominio = {6}', '6' in resp or 'Morte' in resp or 'morte' in resp.lower()),
        ('efeitoConfig com tipo', 'efeitoConfig' in resp and 'tipo' in resp),
        ('dano_extra', 'dano_extra' in resp),
        ('life_leech', 'life_leech' in resp or 'leech' in resp),
        ('categoria = single', 'single' in resp),
        ('condicaoFocoMin = 50', '50' in resp),
        ('nivelMin = 10', '10' in resp or 'nivelMin' in resp),
        ('cor', 'cor' in resp.lower() or 'COR.' in resp),
    ]
    ok_count = sum(1 for _, ok in checks if ok)
    print(f'\n[CHECKS] {ok_count}/{len(checks)}')
    for nome_ck, ok in checks:
        marc = "OK" if ok else "X"
        print(f'  {nome_ck}: {marc}')
    
    if ok_count >= 7:
        print(f'\n[VEREDITO] Habilidade SPA gerada com sucesso!')
    else:
        acertos = ok_count
        total = len(checks)
        print(f'\n[VEREDITO] Precisando melhorar ({acertos}/{total})')

else:
    print('[ERRO] Nenhum exemplo de habilidade encontrado')
