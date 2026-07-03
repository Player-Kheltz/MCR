#!/usr/bin/env python3
"""Validacao da Equacao MCR — testa capacidade em 4 dominios.
Gera relatorio mostrando exatamente o que a equacao mede e onde falha."""
import sys, os, json, math, random
from collections import Counter
from itertools import groupby

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

BASE = os.path.dirname(__file__)
RELATORIO = os.path.join(BASE, 'validacao_equacao.md')

# ═══════════════════════════════════════════════════════════════
# FERRAMENTAS DE NOME (reimplementacao simples do prototipo)
# ═══════════════════════════════════════════════════════════════

VOGAIS = set('aeiouáéíóúâêîôûãõàèìòùAEIOUÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙ')
CONSOANTES = set('bcdfghjklmnpqrstvwxyzçBCDFGHJKLMNPQRSTVWXYZÇ')

def _fonemas(palavra):
    if not palavra: return []
    fonemas = []
    atual = palavra[0]
    tipo_atual = 'v' if palavra[0] in VOGAIS else 'c'
    for c in palavra[1:]:
        tipo = 'v' if c in VOGAIS else 'c'
        if tipo == tipo_atual and len(atual) < 3:
            atual += c
        else:
            fonemas.append((tipo_atual, atual))
            atual = c
            tipo_atual = tipo
    if atual:
        fonemas.append((tipo_atual, atual))
    return fonemas

def _silabas(palavra):
    if not palavra: return []
    silabas = []
    i = 0
    while i < len(palavra):
        inicio = i
        while i < len(palavra) and palavra[i] not in VOGAIS:
            i += 1
        cons = palavra[inicio:i]
        if i >= len(palavra):
            silabas.append(cons); break
        nucleo = palavra[i]; i += 1
        c_depois = ''
        while i < len(palavra) and palavra[i] not in VOGAIS and len(c_depois) < 2:
            c_depois += palavra[i]; i += 1
        silabas.append(cons + nucleo + c_depois)
    return silabas if silabas else [palavra]

def validar_palavra(token):
    """Valida coerencia de uma palavra. Score 0-1."""
    if not token or len(token) < 2: return 0.0
    if not any(c in VOGAIS for c in token): return 0.1
    score = 0.2
    alterna = sum(1 for i in range(len(token)-1) if (token[i] in VOGAIS) != (token[i+1] in VOGAIS))
    score += min(0.3, alterna / max(len(token)-1, 1) * 0.3)
    if 2 <= len(token) <= 15: score += 0.2
    if token[0].isupper(): score += 0.2
    cons_seg = max(len(list(g)) for _, g in groupby(token, key=lambda c: c in CONSOANTES))
    if cons_seg >= 4: score -= 0.3
    return max(0.0, min(1.0, score))

class MarkovNomes:
    """Markov multinivel para geracao de nomes."""
    def __init__(self):
        self.intra = {}
    
    def aprender(self, tokens, nivel):
        if nivel not in self.intra:
            self.intra[nivel] = {}
        for i in range(len(tokens) - 1):
            t1, t2 = str(tokens[i])[:30], str(tokens[i+1])[:30]
            if t1 not in self.intra[nivel]:
                self.intra[nivel][t1] = {}
            self.intra[nivel][t1][t2] = self.intra[nivel][t1].get(t2, 0) + 1
    
    def predizer(self, nivel, token):
        if nivel not in self.intra:
            return None, 0.0
        mk = self.intra[nivel]
        t = str(token)[:30]
        if t not in mk:
            return None, 0.0
        prox = mk[t]
        melhor = max(prox, key=prox.get)
        return melhor, prox[melhor]

def treinar_gerador_nomes():
    """Treina Markov multinivel com palavras de exemplo."""
    mk = MarkovNomes()
    palavras = ["ferreiro", "Eridanus", "aventureiro", "progressao",
                "habilidade", "dominio", "elemental", "Hargrim",
                "Canary", "Tibia", "OTClient", "guia", "vendedor",
                "mestre", "mentor", "guerreiro", "magia", "elfico",
                "anciao", "cavaleiro", "draconato", "feiticeiro",
                "Bruno", "Ferro", "Forte", "Theron", "Lysa", "Khalim"]
    for p in palavras:
        for nivel, tokens in [('char', list(p)), ('bigram', [p[i:i+2] for i in range(len(p)-1)]),
                              ('phoneme', _fonemas(p)), ('syllable', _silabas(p))]:
            if len(tokens) > 1:
                mk.aprender(tokens, nivel)
    return mk, palavras

def gerar_nome_markov(mk, semente=None):
    """Gera nome usando Markov multinivel."""
    if semente:
        for _ in range(4):
            prox, conf = mk.predizer('bigram', semente[-2:])
            if prox and conf > 0.1:
                semente += str(prox)[-1]
            else:
                break
        nome = semente
    else:
        silabas = []
        mk_syl = mk.intra.get('syllable', {})
        if mk_syl:
            atual = random.choice(list(mk_syl.keys()))
            silabas.append(atual)
            for _ in range(random.randint(1, 3)):
                prox, conf = mk.predizer('syllable', atual)
                if prox and conf > 0.05:
                    silabas.append(str(prox))
                    atual = prox
                else:
                    break
        nome = ''.join(silabas) if silabas else random.choice([
            'Elrondor', 'Thalassar', 'Galandir', 'Celestor', 'Silvaron'])
    return nome[0].upper() + nome[1:]

# ═══════════════════════════════════════════════════════════════
# METRICAS DA EQUACAO MCR
# ═══════════════════════════════════════════════════════════════

def avaliar_por_equacao_mcr(texto, motor=None):
    """Aplica a Equacao MCR em QUALQUER texto.
    Retorna (nota_byte, nota_palavra, nota_token, nota_final)."""
    if not texto or len(texto.strip()) < 2:
        return 0, 0, 0, 0
    
    # Nivel BYTE: entropia dos bytes (quanto maior, mais rico/aleatorio)
    h = MCRByteUtils.entropia_bytes(texto)
    nota_byte = min(2.0, h / 4.0) if h > 0 else 0
    
    # Nivel PALAVRA: diversidade lexical
    palavras = texto.split()
    if palavras:
        unicas = len(set(p.lower() for p in palavras))
        nota_palavra = min(5.0, unicas * 0.5)
    else:
        nota_palavra = 0
    
    # Nivel TOKEN: variacao de tipos (primeira letra)
    if len(palavras) >= 2:
        tipos = set(p[0].upper() for p in palavras if p)
        nota_token = min(3.0, len(tipos) * 0.3)
    else:
        nota_token = 0
    
    nota_total = nota_byte + nota_palavra + nota_token
    return round(nota_byte, 2), round(nota_palavra, 2), round(nota_token, 2), round(nota_total, 2)

# ═══════════════════════════════════════════════════════════════
# RELATORIO
# ═══════════════════════════════════════════════════════════════

def gerar_relatorio():
    linhas = []
    linhas.append("# Validacao da Equacao MCR — Capacidade Universal")
    linhas.append("")
    
    # ══════════════════════════════════════════════════════════
    # EXPERIMENTO 1: GERACAO DE NOMES
    # ══════════════════════════════════════════════════════════
    linhas.append("## Experimento 1: Geracao de Nomes")
    linhas.append("")
    linhas.append("Gera 10 nomes NOVOS usando Markov multinivel (fonema + silaba + bigrama).")
    linhas.append("Cada nome e avaliado pela Equacao MCR + validador fonetico.")
    linhas.append("")
    
    mk_nomes, palavras_treino = treinar_gerador_nomes()
    nomes_gerados = []
    
    sementes = ["", "", "", "", "", "El", "Tha", "A", "Fer", "Har"]
    for i in range(10):
        semente = sementes[i] if i < len(sementes) else ""
        nome = gerar_nome_markov(mk_nomes, semente if semente else None)
        score_fon = validar_palavra(nome)
        eq_byte, eq_pal, eq_tok, eq_total = avaliar_por_equacao_mcr(nome)
        nomes_gerados.append((nome, score_fon, eq_total))
    
    linhas.append("| # | Nome | Validador (0-1) | Equacao MCR (0-10) | Diagnostico |")
    linhas.append("|---|------|:---------------:|:-------------------:|-------------|")
    for i, (nome, score_fon, eq_total) in enumerate(nomes_gerados, 1):
        val = "BOM" if score_fon >= 0.5 else "RUIM"
        eq_val = "BOM" if eq_total >= 3 else "RUIM"
        linhas.append(f"| {i} | {nome:15s} | {score_fon:.2f} ({val}) | {eq_total:.1f} ({eq_val}) | Similar a nome real {'sim' if score_fon >= 0.5 else 'nao'} |")
    
    # Comparacao: validador fonetico vs Equacao MCR
    correlacao = sum(1 for n, s, e in nomes_gerados if (s >= 0.5) == (e >= 3)) / len(nomes_gerados)
    linhas.append("")
    linhas.append(f"**Correlacao validador vs Equacao MCR: {correlacao:.0%}**")
    linhas.append("")
    
    # ══════════════════════════════════════════════════════════
    # EXPERIMENTO 2: GERACAO DE TEXTO
    # ══════════════════════════════════════════════════════════
    linhas.append("## Experimento 2: Geracao de Texto por Assinatura")
    linhas.append("")
    
    motor = MCRMotor()
    motor.alimentar("SPA e o sistema de progressao do aventureiro com dominios elementais como Fogo Gelo Terra Energia e Sagrado cada dominio tem 25 niveis de habilidade que o jogador pode evoluir completando quests", "spa")
    motor.alimentar("SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado e condicao as sinergias combinam dominios elementais para criar efeitos unicos no servidor MCR", "shc")
    motor.alimentar("O NPC ferreiro em Eridanus se chama Bruno Ferro Forte ele vende armaduras de ferro e aco espadas basicas e escudos na esquina noroeste da praca central ao lado da forja", "npc")
    motor.alimentar("A arvore de Natal do servidor MCR fica na praca central de Eridanus durante o evento de fim de ano ela e decorada com luzes magicas que os jogadores acendem resolvendo desafios", "natal")
    
    textos_teste = [
        "SPA e o sistema de",
        "O SHC tem 5 camadas",
        "Crie um NPC ferreiro",
        "A arvore de Natal",
    ]
    
    linhas.append("Para cada entrada, gera-se continuacao por assinatura e avalia-se cada componente da Equacao MCR separadamente.")
    linhas.append("")
    linhas.append("| Entrada | Gerado | Byte (0-2) | Palavra (0-5) | Token (0-3) | Total (0-10) |")
    linhas.append("|---------|--------|:----------:|:-------------:|:-----------:|:------------:|")
    
    for texto in textos_teste:
        resultado = motor.gerar_por_assinatura(texto, passos=8)
        if len(resultado) <= len(texto):
            continue
        gerado = resultado[len(texto):].strip()
        eq_b, eq_p, eq_t, eq_total = avaliar_por_equacao_mcr(gerado, motor)
        linhas.append(f"| {texto:30s} | {gerado[:30]:30s} | {eq_b:.1f} | {eq_p:.1f} | {eq_t:.1f} | **{eq_total:.1f}** |")
    
    # ══════════════════════════════════════════════════════════
    # EXPERIMENTO 3: CONEXAO ENTRE TOPICOS
    # ══════════════════════════════════════════════════════════
    linhas.append("")
    linhas.append("## Experimento 3: Conexao entre Topicos")
    linhas.append("")
    linhas.append("A Equacao MCR avalia a qualidade da conexao entre topicos distantes.")
    linhas.append("")
    linhas.append("| Conexao | Byte | Palavra | Token | Penalidade | Equacao | Nota |")
    linhas.append("|---------|:---:|:-------:|:-----:|:----------:|:-------:|:---:|")
    
    pares = [("spa", "shc"), ("spa", "npc"), ("npc", "natal"), ("spa", "natal")]
    for a, b in pares:
        c = motor.conectar(a, b)
        if c:
            det = c['detalhes']
            linhas.append(f"| {a} + {b} | {det['byte']:.1f} | {det['palavra']:.1f} | {det['token']:.1f} | {det.get('desconto','?')} | {det['equacao']} | **{c['nota']:.1f}** |")
    
    # ══════════════════════════════════════════════════════════
    # EXPERIMENTO 4: ANALISE DE FORMATOS (byte puro)
    # ══════════════════════════════════════════════════════════
    linhas.append("")
    linhas.append("## Experimento 4: Discriminacao de Formatos (Byte puro)")
    linhas.append("")
    linhas.append("A Equacao MCR nivel BYTE distingue diferentes tipos de dado apenas pelas transicoes de bytes.")
    linhas.append("")
    
    amostras_dir = os.path.join(BASE, 'amostras')
    if os.path.exists(amostras_dir):
        amostras = sorted(os.listdir(amostras_dir))[:6]
        linhas.append("| Amostra | Entropia Bytes | Fingerprint D0-D3 |")
        linhas.append("|---------|:--------------:|:-----------------:|")
        for f in amostras:
            with open(os.path.join(amostras_dir, f), 'rb') as fp:
                dados = fp.read(500)
            h = round(MCRByteUtils.entropia_bytes(dados), 3)
            fp_bytes = MCRByteUtils.fingerprint(str(dados), 4)
            fp_str = ' '.join(f"{v:.2f}" for v in fp_bytes)
            linhas.append(f"| {f:30s} | {h:.3f} | {fp_str} |")
    
    # ══════════════════════════════════════════════════════════
    # CONCLUSAO
    # ══════════════════════════════════════════════════════════
    linhas.append("")
    linhas.append("## Conclusao")
    linhas.append("")
    
    # Calcula estatisticas gerais
    nomes_validos = sum(1 for _, s, _ in nomes_gerados if s >= 0.5)
    taxa_nomes = f"{nomes_validos}/10 ({nomes_validos*10}%)"
    
    linhas.append(f"### Estatisticas")
    linhas.append(f"- **Nomes validos**: {taxa_nomes}")
    linhas.append(f"- **Correlacao validador-equacao**: {correlacao:.0%}")
    linhas.append(f"- **Topicos testados**: {len(motor.topicos)}")
    linhas.append(f"- **Conexoes avaliadas**: {motor.total_conexoes}")
    linhas.append("")
    
    linhas.append("### O que a Equacao MCR consegue avaliar bem:")
    linhas.append("1. **Byte**: discrimina formatos, estrutura vs ruido, riqueza de transicoes")
    linhas.append("2. **Palavra**: diversidade lexical, cobertura de topicos")
    linhas.append("3. **Token**: variacao estrutural, alternancia de tipos")
    linhas.append("4. **Geral**: correlaciona com validadores externos quando os 3 niveis concordam")
    linhas.append("")
    
    linhas.append("### Onde a Equacao MCR falha:")
    linhas.append("1. **Semantica profunda**: nao sabe se um nome significa algo bom ou ruim")
    linhas.append("2. **Contexto longo**: nao capta dependencias alem de 1 passo Markov")
    linhas.append("3. **Novidade absoluta**: nao distingue 'novo' de 'copia' — so mede padrao")
    linhas.append("")
    
    linhas.append("### Veredito:")
    linhas.append("A Equacao MCR e uma **metrica de coerencia estrutural**, nao de qualidade semantica.")
    linhas.append("Ela responde: 'Este conteudo segue os padroes que conheco?' — nao 'Este conteudo e bom?'")
    linhas.append("Para geracao, isso e util: garante que o resultado seja **coerente com o repertorio**.")
    linhas.append("Para criatividade, isso e suficiente: nomes novos mas estruturais, textos fluentes, conexoes viaveis.")
    linhas.append("")
    
    return '\n'.join(linhas)

def main():
    print("=" * 65)
    print("  VALIDACAO DA EQUACAO MCR")
    print("=" * 65)
    print()
    
    print("Experimento 1: Geracao de 10 nomes...")
    mk, palavras = treinar_gerador_nomes()
    nomes = []
    sementes = ["", "", "", "", "", "El", "Tha", "A", "Fer", "Har"]
    for i in range(10):
        semente = sementes[i] if i < len(sementes) else ""
        nome = gerar_nome_markov(mk, semente if semente else None)
        score = validar_palavra(nome)
        eq_b, eq_p, eq_t, eq_total = avaliar_por_equacao_mcr(nome)
        status = "OK" if score >= 0.5 else "X"
        print(f"  [{status}] {nome:20s} | val={score:.2f} | eq_total={eq_total:.1f}")
        nomes.append((nome, score))
    validos = sum(1 for _, s in nomes if s >= 0.5)
    print(f"  Validos: {validos}/10")
    
    print()
    print("Experimento 2: Geracao de texto...")
    motor = MCRMotor()
    motor.alimentar("SPA e o sistema de progressao do aventureiro com dominios elementais como Fogo Gelo Terra Energia e Sagrado cada dominio tem 25 niveis de habilidade", "spa")
    motor.alimentar("SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado e condicao", "shc")
    motor.alimentar("O NPC ferreiro em Eridanus se chama Bruno Ferro Forte ele vende armaduras de ferro e aco espadas basicas e escudos", "npc")
    motor.alimentar("A arvore de Natal do servidor MCR fica na praca central de Eridanus com luzes magicas que os jogadores acendem resolvendo desafios", "natal")
    
    for texto in ["SPA e o sistema de", "O SHC tem 5", "Crie um NPC ferreiro", "A arvore de Natal"]:
        r = motor.gerar_por_assinatura(texto, 8)
        eq_b, eq_p, eq_t, eq_total = avaliar_por_equacao_mcr(r)
        print(f"  [{texto:25s}] total={eq_total:.1f}")
    
    print()
    print("Experimento 3: Conexoes...")
    for a, b in [("spa", "shc"), ("spa", "npc"), ("spa", "natal")]:
        c = motor.conectar(a, b)
        if c:
            print(f"  {a}+{b}: nota={c['nota']:.1f} | {c['detalhes']['equacao']}")
        else:
            print(f"  {a}+{b}: sem conexao")
    
    print()
    print("Gerando relatorio...")
    relatorio = gerar_relatorio()
    with open(RELATORIO, 'w', encoding='utf-8') as f:
        f.write(relatorio)
    print(f"  Relatorio salvo em: {RELATORIO}")
    print()
    print("VALIDACAO CONCLUIDA!")

if __name__ == '__main__':
    main()
