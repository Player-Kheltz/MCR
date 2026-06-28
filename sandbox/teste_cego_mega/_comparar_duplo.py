import os, re

def analisar(texto, nome):
    m = {}
    m['chars'] = len(texto)
    m['linhas'] = len(texto.split('\n'))
    blocos = re.findall(r'```(?:python|rust)?\s*\n(.*?)```', texto, re.DOTALL)
    m['blocos'] = len(blocos)
    m['linhas_codigo'] = sum(len(b.split('\n')) for b in blocos)
    erros = 0
    for b in blocos:
        try:
            compile(b.strip(), '<test>', 'exec')
        except:
            erros += 1
    m['erros'] = erros
    # Termos tecnicos
    termos = ['async', 'await', 'locale', 'hybrid', 'encoding', 'score', 'memory',
              'thread', 'safety', 'concorrencia', 'ownership', 'borrowing', 'unsafe',
              'Mente', 'Conselho', 'memoria', 'aprendizado']
    m['termos'] = sum(1 for t in termos if t.lower() in texto.lower())
    return m

base = r"E:\Projeto MCR\sandbox\teste_cego_mega"
mcr = open(os.path.join(base, "respostas_mcr", "duplo_mcr.txt"), "r", encoding="utf-8-sig", errors="replace").read()
cloud = open(os.path.join(base, "respostas_cloud", "duplo_cloud.txt"), "r", encoding="utf-8-sig", errors="replace").read()

m = analisar(mcr, "MCR")
c = analisar(cloud, "Cloud")

print("=" * 65)
print("  COMPARATIVO TESTE CEGO DUPLO")
print("=" * 65)
print(f"\n{'Metrica':<30} {'MCR':<12} {'Cloud':<12}")
print("-" * 55)
for k in ['chars', 'linhas', 'blocos', 'linhas_codigo', 'erros', 'termos']:
    mv = m.get(k,0)
    cv = c.get(k,0)
    win = "MCR" if mv > cv else ("Cloud" if cv > mv else "=")
    if k == 'erros':
        win = "MCR" if mv < cv else ("Cloud" if cv < mv else "=")
    print(f"  {k:<30} {mv:<12} {cv:<12}  {win}")

print(f"\n  Pontos fortes MCR:")
print(f"    - Codigo Rust seguro (sem unsafe, sem locale global)")
print(f"    - Testes unitarios inclusos")
print(f"    - 3 riscos de seguranca identificados")
print(f"\n  Pontos fortes Cloud:")
print(f"    - Explicacao detalhada do fluxo Mente-Corpo")
print(f"    - Codigo Python completo da melhoria")
print(f"\n  Gargalos MCR:")
if m['erros'] > 0:
    print(f"    - {m['erros']} erro(s) de sintaxe no codigo gerado")
print(f"\n  Gargalos Cloud:")
if c['erros'] > 0:
    print(f"    - {c['erros']} erro(s) de sintaxe no codigo gerado")
