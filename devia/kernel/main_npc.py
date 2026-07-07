#!/usr/bin/env python3
"""
MCRNPCv2 - Game Loop Principal
Integra: HDC + SDM + Mapa + Percepcao + NPCs + Rede
"""
import time, random, json, os, sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

from mundo_tibia import MapaTibia
from npc_vivo import MCRNPCv2
from rede_npcs import RedeNPCs
from hdc_core import HDCVocab

class SimulacaoMCR:
    def __init__(self):
        self.tick_atual = 0
        self.hora = 8  # comeca de manha
        self.jogadores = {}  # nome -> info
        self.historico = []
        self.jogadores_por_regiao = defaultdict(list)
        
        print("=" * 60)
        print("MCRNPCv2 - SIMULACAO DO MUNDO TIBIA")
        print("=" * 60)
        print()
        
        # Carregar mapa
        print("Carregando mapa...")
        self.mapa = MapaTibia()
        
        # Criar rede
        print("\nCriando NPCs...")
        self.rede = RedeNPCs()
        self._criar_npcs()
        
        # Criar jogadores simulados
        self._criar_jogadores()
        
        print(f"\n{len(self.rede.npcs)} NPCs prontos em {len(self.rede.por_regiao)} regioes")
        print("=" * 60)
    
    def _criar_npcs(self):
        """Cria NPCs em diferentes regioes"""
        npcs_config = [
            # (nome, profissao, x, y, z, regiao_id)
            ("Joao", "ferreiro", 971, 995, 7, 0),
            ("Maria", "bibliotecario", 975, 1000, 7, 0),
            ("Zaran", "mercador", 1000, 1005, 7, 0),
            ("Thor", "ferreiro", 965, 1015, 6, 4),
            ("Luna", "bibliotecario", 954, 1007, 7, 1),
        ]
        
        itens_iniciais = {
            "ferreiro": ["espada de ferro", "escudo de madeira", "martelo", "bigorna"],
            "bibliotecario": ["livro de magia", "mapa antigo", "pergaminho"],
            "mercador": ["pocao de vida", "anel de protecao", "corda", "tocha"],
        }
        
        for nome, profissao, x, y, z, reg_id in npcs_config:
            npc = MCRNPCv2(nome, profissao, x, y, z, reg_id, self.mapa)
            for item in itens_iniciais.get(profissao, []):
                npc.adicionar_item(item)
            self.rede.registrar(npc)
    
    def _criar_jogadores(self):
        """Cria jogadores simulados para teste"""
        self.jogadores = {
            "Kheltz": {"x": 972, "y": 996, "z": 7, "n_visitas": 0, "ultima_fala": ""},
            "Rook": {"x": 970, "y": 994, "z": 7, "n_visitas": 0, "ultima_fala": ""},
        }
    
    def _atualizar_hora(self):
        """Ciclo dia-noite: 10 ticks = 1 hora"""
        if self.tick_atual > 0 and self.tick_atual % 10 == 0:
            self.hora = (self.hora + 1) % 24
    
    def _mover_jogadores(self):
        """Jogadores andam aleatoriamente pelo mapa"""
        for nome, info in self.jogadores.items():
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            info['x'] += dx
            info['y'] += dy
            info['n_visitas'] += 1
    
    def _atualizar_jogadores_por_regiao(self):
        """Agrupa jogadores por regiao"""
        self.jogadores_por_regiao.clear()
        for nome, info in self.jogadores.items():
            reg = self.mapa.regiao_em(info['x'], info['y'], info['z'])
            if reg:
                self.jogadores_por_regiao[reg.id].append({
                    'nome': nome,
                    'dist': random.randint(2, 5),
                    'ultima_fala': info['ultima_fala'],
                })
    
    def tick(self):
        """Um ciclo completo da simulacao"""
        self.tick_atual += 1
        self._atualizar_hora()
        
        # Mover jogadores a cada 2 ticks
        if self.tick_atual % 2 == 0:
            self._mover_jogadores()
        
        self._atualizar_jogadores_por_regiao()
        
        # Executar todos NPCs
        resultados = self.rede.executar_todos(
            jogadores_por_regiao=self.jogadores_por_regiao,
            hora=self.hora
        )
        
        # Broadcast seletivo: NPCs com alta entropia compartilham
        for nome, npc in self.rede.npcs.items():
            if npc.hist_entropia and len(npc.hist_entropia) >= 5:
                ent_media = sum(list(npc.hist_entropia)[-5:]) / 5
                if ent_media > 0.5:
                    # Evento surpreendente: broadcast local
                    if npc.ultimo_hd:
                        self.rede.broadcast_local(nome, npc.ultimo_hd, raio=8)
        
        self.historico.append(resultados)
        
        # Log resumido
        acoes_interessantes = [f"{n}: {r}" for n, r in resultados.items()
                              if "falar" in r or "andou" in r or "comerciar" in r]
        
        return {
            'tick': self.tick_atual,
            'hora': self.hora,
            'periodo': "dia" if 6 <= self.hora <= 18 else "noite",
            'jogadores_online': len(self.jogadores),
            'acoes': acoes_interessantes[:5],
        }
    
    def conversar(self, nome_npc, nome_jogador, mensagem):
        """Jogador conversa com um NPC"""
        npc = self.rede.npcs.get(nome_npc)
        if not npc:
            return f"NPC {nome_npc} nao encontrado."
        
        resposta = npc.falar(mensagem)
        
        # Registrar no jogador
        if nome_jogador in self.jogadores:
            self.jogadores[nome_jogador]['ultima_fala'] = mensagem
        
        # Broadcast da conversa para NPCs proximos
        hd_fala = npc.percepcao.vocab.bundle(nome_jogador, mensagem[:20])
        self.rede.broadcast_local(nome_npc, hd_fala, raio=5)
        
        return resposta
    
    def relatorio(self):
        """Gera relatorio do estado atual"""
        resumo_rede = self.rede.resumo()
        return {
            'tick': self.tick_atual,
            'hora': self.hora,
            'jogadores': dict(self.jogadores),
            'npcs': resumo_rede['npcs'],
        }
    
    def modo_autonomo(self, n_ticks=50, intervalo=0.1):
        """Roda N ticks automaticamente"""
        print(f"\nIniciando modo autonomo por {n_ticks} ticks...")
        print()
        
        for _ in range(n_ticks):
            info = self.tick()
            
            # Mostrar apenas eventos interessantes
            if info['acoes']:
                hora_str = f"{info['hora']:02d}:00"
                print(f"  [{hora_str}] {', '.join(info['acoes'][:3])}")
            
            time.sleep(intervalo)
        
        print(f"\nModo autonomo concluido ({n_ticks} ticks)")
        print()
        
        # Estatisticas finais
        total_falas = sum(1 for h in self.historico
                         for r in h.values() if 'falar' in r)
        total_andou = sum(1 for h in self.historico
                         for r in h.values() if 'andou' in r)
        print(f"Total de falas: {total_falas}")
        print(f"Total de movimentos: {total_andou}")
        
        # Estado final dos NPCs
        print(f"\nEstado final dos NPCs:")
        resumo = self.rede.resumo()
        for nome, info in resumo['npcs'].items():
            print(f"  {nome} ({info['profissao']}): pos={info['pos']} "
                  f"exploracao={info['exploracao']:.3f}")

    def modo_interativo(self):
        """Modo interativo: jogador conversa com NPCs"""
        print("\nModo interativo. Comandos:")
        print("  falar <NPC> <mensagem>")
        print("  status")
        print("  tick")
        print("  sair")
        print()
        
        while True:
            cmd = input("> ").strip()
            
            if cmd == "sair":
                break
            elif cmd == "status":
                r = self.relatorio()
                print(f"Tick {r['tick']}, hora {r['hora']}:00")
                for nome, info in r['npcs'].items():
                    print(f"  {nome}: ({info['pos'][0]},{info['pos'][1]},{info['pos'][2]}) "
                          f"explor={info['exploracao']:.2f}")
            elif cmd == "tick":
                info = self.tick()
                print(f"Tick {info['tick']} concluido (hora {info['hora']}:00)")
                for acao in info['acoes'][:5]:
                    print(f"  {acao}")
            elif cmd.startswith("falar "):
                partes = cmd[6:].split(" ", 1)
                if len(partes) == 2:
                    npc_nome, msg = partes
                    resp = self.conversar(npc_nome, "Kheltz", msg)
                    print(f"  {npc_nome}: {resp}")
                else:
                    print("  Use: falar <NPC> <mensagem>")
            else:
                print("  Comandos: falar <NPC> <msg>, status, tick, sair")


if __name__ == "__main__":
    sim = SimulacaoMCR()
    
    # Rodar modo autonomo primeiro
    sim.modo_autonomo(n_ticks=20, intervalo=0.05)
    
    # Depois modo interativo
    print("\n" + "=" * 60)
    print("Entrando no modo interativo...")
    print("=" * 60)
    sim.modo_interativo()
