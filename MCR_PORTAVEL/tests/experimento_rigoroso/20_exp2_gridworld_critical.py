#!/usr/bin/env python3
"""
Experimento 2: Aprendizado Crítico Auto-Regulado (Grid World)

MCR mantendo entropia 0.2-0.7 (criticalidade) vs taxas fixas de exploração.
Objetivo muda periodicamente para testar esquecimento catastrófico.
"""
import sys, os, math, json, time, random
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, 'E:/MCR')

import mcr.mcr as mcr

random.seed(42)

print('='*70)
print('EXPERIMENTO 2: APRENDIZADO CRITICO AUTO-REGULADO')
print('='*70)

# ============================================================
# AMBIENTE: Grid World 10x10 com objetivo movel
# ============================================================
TAM = 10
ACOES = ['cima', 'baixo', 'esq', 'dir']
N_ACOES = len(ACOES)

class GridWorld:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.reset()
    
    def reset(self):
        self.agente = [0, 0]
        self.objetivo = [9, 9]
        return self._estado()
    
    def _estado(self):
        return tuple(self.agente)
    
    def passo(self, acao):
        x, y = self.agente
        if acao == 'cima': y = max(0, y-1)
        elif acao == 'baixo': y = min(TAM-1, y+1)
        elif acao == 'esq': x = max(0, x-1)
        elif acao == 'dir': x = min(TAM-1, x+1)
        self.agente = [x, y]
        
        recompensa = 1.0 if self.agente == self.objetivo else 0.0
        done = self.agente == self.objetivo
        return self._estado(), recompensa, done
    
    def mover_objetivo(self):
        """Move o objetivo para posicao aleatoria"""
        self.objetivo = [self.rng.randint(0, TAM-1), self.rng.randint(0, TAM-1)]
        return self.objetivo

# ============================================================
# AGENTES
# ============================================================

class AgenteMCRCritico:
    """MCR com auto-regulacao de criticalidade (entropia 0.2-0.7)"""
    def __init__(self, nome='MCR_Critico'):
        self.nome = nome
        self.mk = mcr.MCR('acoes')
        self.entropia_hist = deque(maxlen=50)
        self.ultimo_estado = None
        self.ultima_acao = None
        self.learning_rate = 0.1
        self.exploracao = 0.3
        self.passos = 0
        self.entropias = []
        self.epsilon_hist = []
        self.lr_hist = []
    
    def escolher_acao(self, estado):
        estado_str = f'E{estado[0]}_{estado[1]}'
        
        if random.random() < self.exploracao:
            acao = random.choice(ACOES)
        else:
            pred, conf = self.mk.predizer(estado_str)
            if pred and conf > 0:
                acao = pred.split(':')[0] if ':' in pred else pred
                if acao not in ACOES:
                    acao = random.choice(ACOES)
            else:
                acao = random.choice(ACOES)
        
        self.ultimo_estado = estado_str
        self.ultima_acao = acao
        return acao
    
    def aprender(self, estado, acao, recompensa, novo_estado):
        if self.ultimo_estado and self.ultima_acao:
            token_acao = f'{acao}:{recompensa}'
            self.mk.aprender(self.ultimo_estado, token_acao)
        
        medir = self.mk.entropia_media() if self.mk.total > 0 else 1.0
        self.entropia_hist.append(medir)
        self.entropias.append(medir)
        
        # Auto-regulacao critica
        if len(self.entropia_hist) >= 10:
            ent_media = sum(list(self.entropia_hist)[-10:]) / 10
            if ent_media < 0.2:  # rigido demais -> explorar mais
                self.exploracao = min(0.8, self.exploracao * 1.1)
                self.learning_rate = max(0.01, self.learning_rate * 0.95)
            elif ent_media > 0.7:  # caotico demais -> consolidar
                self.exploracao = max(0.05, self.exploracao * 0.95)
                self.learning_rate = min(0.5, self.learning_rate * 1.1)
        
        self.epsilon_hist.append(self.exploracao)
        self.lr_hist.append(self.learning_rate)
        self.passos += 1

class AgenteFixo:
    """Taxa de exploracao fixa"""
    def __init__(self, nome, epsilon=0.1):
        self.nome = nome
        self.mk = mcr.MCR('acoes')
        self.epsilon = epsilon
        self.ultimo_estado = None
        self.passos = 0
        
    def escolher_acao(self, estado):
        estado_str = f'E{estado[0]}_{estado[1]}'
        if random.random() < self.epsilon:
            acao = random.choice(ACOES)
        else:
            pred, conf = self.mk.predizer(estado_str)
            if pred and conf > 0:
                acao = pred.split(':')[0] if ':' in pred else pred
                if acao not in ACOES:
                    acao = random.choice(ACOES)
            else:
                acao = random.choice(ACOES)
        self.ultimo_estado = estado_str
        return acao
    
    def aprender(self, estado, acao, recompensa, novo_estado):
        if self.ultimo_estado:
            token_acao = f'{acao}:{recompensa}'
            self.mk.aprender(self.ultimo_estado, token_acao)
        self.passos += 1

class AgenteDecay:
    """Epsilon-decay linear"""
    def __init__(self, nome='Epsilon_Decay'):
        self.nome = nome
        self.mk = mcr.MCR('acoes')
        self.epsilon_inicial = 0.5
        self.epsilon = self.epsilon_inicial
        self.epsilon_final = 0.01
        self.decay_passos = 2000
        self.ultimo_estado = None
        self.passos = 0
        
    def escolher_acao(self, estado):
        estado_str = f'E{estado[0]}_{estado[1]}'
        if random.random() < self.epsilon:
            acao = random.choice(ACOES)
        else:
            pred, conf = self.mk.predizer(estado_str)
            if pred and conf > 0:
                acao = pred.split(':')[0] if ':' in pred else pred
                if acao not in ACOES:
                    acao = random.choice(ACOES)
            else:
                acao = random.choice(ACOES)
        self.ultimo_estado = estado_str
        return acao
    
    def aprender(self, estado, acao, recompensa, novo_estado):
        if self.ultimo_estado:
            token_acao = f'{acao}:{recompensa}'
            self.mk.aprender(self.ultimo_estado, token_acao)
        # Decay linear
        self.epsilon = max(self.epsilon_final, 
                          self.epsilon_inicial - (self.epsilon_inicial - self.epsilon_final) * self.passos / self.decay_passos)
        self.passos += 1

# ============================================================
# EXECUCAO
# ============================================================
N_EPISODIOS = 100
PASSOS_MAX = 500
MUDAR_OBJETIVO_A_CADA = 20  # episodios

agentes = [
    AgenteMCRCritico(),
    AgenteFixo('Epsilon_0.05', epsilon=0.05),
    AgenteFixo('Epsilon_0.10', epsilon=0.10),
    AgenteFixo('Epsilon_0.30', epsilon=0.30),
    AgenteDecay(),
]

print(f'\nExecutando {N_EPISODIOS} episodios com {len(agentes)} agentes...')
print(f'Objetivo muda a cada {MUDAR_OBJETIVO_A_CADA} episodios\n')

resultados_agentes = {}

for agente in agentes:
    env = GridWorld(seed=42)
    historico_passos = []
    historico_recompensa = []
    recompensas_por_episodio = []
    esquecimentos = []  # passos para re-apos mudanca
    
    objetivo_anterior = None
    
    t0 = time.time()
    
    for ep in range(N_EPISODIOS):
        estado = env.reset()
        total_recompensa = 0
        n_passos = 0
        
        # Mudar objetivo a cada MUDAR_OBJETIVO_A_CADA episodios
        if ep > 0 and ep % MUDAR_OBJETIVO_A_CADA == 0:
            objetivo_anterior = env.objetivo[:]
            env.mover_objetivo()
            n_esquecimento = 0
        
        for passo in range(PASSOS_MAX):
            acao = agente.escolher_acao(estado)
            novo_estado, recompensa, done = env.passo(acao)
            agente.aprender(estado, acao, recompensa, novo_estado)
            
            total_recompensa += recompensa
            n_passos += 1
            
            # Rastrear esquecimento: quantos passos ate primeira recompensa apos mudanca
            if ep > 0 and ep % MUDAR_OBJETIVO_A_CADA == 0 and passo == 0:
                if passo == 0:
                    pass  # inicio do tracking
            
            estado = novo_estado
            if done:
                break
        
        historico_passos.append(n_passos)
        historico_recompensa.append(total_recompensa)
        
        # Se houve mudanca de objetivo, ve quantos passos ate completar
        if ep > 0 and ep % MUDAR_OBJETIVO_A_CADA == 0:
            # Passos deste episodio pos-mudanca (primeiro apos mudar objetivo)
            esquecimentos.append(n_passos)
    
    tempo = time.time() - t0
    
    # Metricas por bloco
    metricas_blocos = []
    for bloco in range(0, N_EPISODIOS, MUDAR_OBJETIVO_A_CADA):
        bloco_passos = historico_passos[bloco:bloco+MUDAR_OBJETIVO_A_CADA]
        bloco_rec = historico_recompensa[bloco:bloco+MUDAR_OBJETIVO_A_CADA]
        metricas_blocos.append({
            'episodios': f'{bloco}-{min(bloco+MUDAR_OBJETIVO_A_CADA, N_EPISODIOS)}',
            'passos_medio': round(sum(bloco_passos)/len(bloco_passos), 1),
            'rec_medio': round(sum(bloco_rec)/len(bloco_rec), 2),
        })
    
    # Esquecimento medio (passos no primeiro episodio apos cada mudanca)
    esquecimento_medio = sum(esquecimentos) / len(esquecimentos) if esquecimentos else 0
    
    # Para MCR critico, entropia media
    ent_media = sum(agente.entropias) / len(agente.entropias) if hasattr(agente, 'entropias') and agente.entropias else None
    ent_final = agente.entropias[-1] if hasattr(agente, 'entropias') and agente.entropias else None
    epsilon_medio = sum(agente.epsilon_hist) / len(agente.epsilon_hist) if hasattr(agente, 'epsilon_hist') and agente.epsilon_hist else None
    
    r = {
        'agente': agente.nome,
        'passos_medio_geral': round(sum(historico_passos)/len(historico_passos), 1),
        'rec_medio_geral': round(sum(historico_recompensa)/len(historico_recompensa), 2),
        'esquecimento_medio': round(esquecimento_medio, 1),
        'tempo_s': round(tempo, 3),
        'metricas_blocos': metricas_blocos,
        'entropia_media': round(ent_media, 4) if ent_media is not None else None,
        'entropia_final': round(ent_final, 4) if ent_final is not None else None,
        'epsilon_medio': round(epsilon_medio, 4) if epsilon_medio is not None else None,
        'entropias': [round(e, 4) for e in agente.entropias] if hasattr(agente, 'entropias') else None,
        'epsilons': [round(e, 4) for e in agente.epsilon_hist] if hasattr(agente, 'epsilon_hist') else None,
    }
    resultados_agentes[agente.nome] = r
    
    print(f'{agente.nome:20}: passos={r["passos_medio_geral"]:.1f} rec={r["rec_medio_geral"]:.2f} '
          f'esq={r["esquecimento_medio"]:.1f} ent={ent_media or 0:.3f} '
          f'epislon_med={epsilon_medio or 0:.3f} T={tempo:.3f}s')

# ============================================================
# ANALISE COMPARATIVA
# ============================================================
print('\n' + '='*70)
print('TABELA COMPARATIVA')
print('='*70)
print(f'{"Agente":20} {"Passos":>8} {"Recomp":>8} {"Esq":>6} {"Entropia":>10} {"Epsilon":>10} {"T(s)":>8}')
print(f'{"-":-<20} {"-":->8} {"-":->8} {"-":->6} {"-":->10} {"-":->10} {"-":->8}')

for nome, r in sorted(resultados_agentes.items()):
    ent = f'{r["entropia_media"]:.3f}' if r['entropia_media'] is not None else '-'
    eps = f'{r["epsilon_medio"]:.3f}' if r['epsilon_medio'] is not None else f'{agentes[[a.nome for a in agentes].index(nome)].epsilon:.3f}'
    print(f'{nome:20} {r["passos_medio_geral"]:>8.1f} {r["rec_medio_geral"]:>8.2f} '
          f'{r["esquecimento_medio"]:>6.1f} {ent:>10} {eps:>10} {r["tempo_s"]:>8.3f}')

# ============================================================
# ANALISE ESPECIFICA: MCR critico manteve entropia 0.2-0.7?
# ============================================================
print('\n' + '='*70)
print('ANALISE CRITICALIDADE (MCR Critico)')
print('='*70)

r_critico = resultados_agentes.get('MCR_Critico', {})
if r_critico.get('entropias'):
    ents = r_critico['entropias']
    tempo_ideal = sum(1 for e in ents if 0.2 <= e <= 0.7) / len(ents) * 100
    tempo_rigido = sum(1 for e in ents if e < 0.2) / len(ents) * 100
    tempo_caotico = sum(1 for e in ents if e > 0.7) / len(ents) * 100
    
    print(f'\nTempo gasto em cada zona:')
    print(f'  Critica (0.2-0.7): {tempo_ideal:.1f}%')
    print(f'  Rigida (<0.2):     {tempo_rigido:.1f}%')
    print(f'  Caotica (>0.7):    {tempo_caotico:.1f}%')
    
    if r_critico.get('epsilons'):
        eps = r_critico['epsilons']
        print(f'\nEpsilon (exploracao) ao longo do tempo:')
        print(f'  Inicio: {eps[0]:.3f}')
        print(f'  Final:  {eps[-1]:.3f}')
        print(f'  Medio:  {sum(eps)/len(eps):.3f}')
        
        # Correlacao entropia-epsilon
        if len(ents) > 10:
            ents_sample = ents[10:]
            eps_sample = eps[10:]
            # Quando entropia baixa, epsilon sobe?
            baixos = [i for i, e in enumerate(ents_sample) if e < 0.2]
            eps_em_baixa = [eps_sample[i] for i in baixos] if baixos else []
            altos = [i for i, e in enumerate(ents_sample) if e > 0.7]
            eps_em_alta = [eps_sample[i] for i in altos] if altos else []
            
            if eps_em_baixa:
                print(f'\n  Quando entropia <0.2: epsilon medio={sum(eps_em_baixa)/len(eps_em_baixa):.3f}')
            if eps_em_alta:
                print(f'  Quando entropia >0.7: epsilon medio={sum(eps_em_alta)/len(eps_em_alta):.3f}')
            
            print(f'  Quando entropia normal: epsilon medio={sum(eps_sample)/len(eps_sample):.3f}')

# Blocos
print('\n' + '='*70)
print('EVOLUCAO POR BLOCO (objetivo muda a cada 20 episodios)')
print('='*70)

for nome, r in sorted(resultados_agentes.items()):
    print(f'\n{nome}:')
    for b in r['metricas_blocos']:
        print(f'  {b["episodios"]:>6}: passos_medio={b["passos_medio"]:>6.1f} rec={b["rec_medio"]:.2f}')

# ============================================================
# SALVAR
# ============================================================
with open('resultado_exp2.json', 'w') as f:
    json.dump(resultados_agentes, f, indent=2, ensure_ascii=False)

print(f'\nResultados salvos em resultado_exp2.json')
print('='*70)
