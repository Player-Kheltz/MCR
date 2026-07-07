import re, math, os, json

CAMINHO_MAPA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'Projeto MCR', 'Canary', 'data', 'logs', 'regions_map.txt')

class Escada:
    def __init__(self, origem, destino, reg_destino):
        self.origem = origem
        self.destino = destino
        self.reg_destino = reg_destino

class Regiao:
    def __init__(self, nome, id_global, z, centro, x_range, y_range,
                 n_tiles, n_escadas, escadas):
        self.nome = nome
        self.id = id_global
        self.z = z
        self.centro = centro
        self.x_min, self.x_max = x_range
        self.y_min, self.y_max = y_range
        self.n_tiles = n_tiles
        self.n_escadas = n_escadas
        self.escadas = escadas
        self.vizinhos = set()

class MapaTibia:
    def __init__(self, caminho=None):
        self.regioes = {}
        self.por_z = {}
        self.carregar(caminho or CAMINHO_MAPA)
    
    def carregar(self, caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            texto = f.read()
        
        blocos = re.split(r'={2,}', texto)
        
        for bloco in blocos:
            bloco = bloco.strip()
            if not bloco or not bloco.startswith('Regiao:'):
                continue
            self._parse_regiao(bloco)
        
        self._construir_grafo()
        print(f"Mapa: {len(self.regioes)} regioes, "
              f"{sum(len(r.escadas) for r in self.regioes.values())} escadas, "
              f"{sum(len(r.vizinhos) for r in self.regioes.values()) // 2} conexoes")
    
    def _parse_regiao(self, bloco):
        linhas = bloco.split('\n')
        
        m = re.search(r'Regiao: (\S+)\s+\(ID global (\d+)\)', linhas[0])
        if not m:
            return
        nome = m.group(1)
        id_global = int(m.group(2))
        
        m_z = re.search(r'Andar: Z=(-?\d+)', linhas[1])
        z = int(m_z.group(1)) if m_z else 7
        
        m_c = re.search(r'Centro: \((\d+),(\d+)\)', linhas[1])
        centro = (int(m_c.group(1)), int(m_c.group(2))) if m_c else (0, 0)
        
        m_a = re.search(r'X\[(\d+)\.\.(\d+)\]\s+Y\[(\d+)\.\.(\d+)\]', linhas[2])
        if m_a:
            x_min, x_max = int(m_a.group(1)), int(m_a.group(2))
            y_min, y_max = int(m_a.group(3)), int(m_a.group(4))
        else:
            x_min = x_max = y_min = y_max = 0
        
        m_s = re.search(r'Tiles:\s*(\d+)\s+Escadas:\s*(\d+)', linhas[3])
        n_tiles = int(m_s.group(1)) if m_s else 0
        n_escadas = int(m_s.group(2)) if m_s else 0
        
        escadas = []
        for linha in linhas[6:]:
            linha = linha.strip()
            if not linha or linha.startswith('--'):
                break
            # Match: NUM : (x, y, z) (reg SRC) -> (x, y, z) (reg DST)
            m_esc = re.search(r'\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(-?\d+)\s*\)\s*\(reg\s*(\d+)\)\s*->\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(-?\d+)\s*\)\s*\(reg\s*(\d+)\)', linha)
            if m_esc:
                origem = (int(m_esc.group(1)), int(m_esc.group(2)), int(m_esc.group(3)))
                destino = (int(m_esc.group(5)), int(m_esc.group(6)), int(m_esc.group(7)))
                reg_destino = int(m_esc.group(8))
                escadas.append(Escada(origem, destino, reg_destino))
        
        regiao = Regiao(nome, id_global, z, centro,
                       (x_min, x_max), (y_min, y_max),
                       n_tiles, n_escadas, escadas)
        self.regioes[id_global] = regiao
        
        if z not in self.por_z:
            self.por_z[z] = []
        self.por_z[z].append(regiao)
    
    def _construir_grafo(self):
        for reg in self.regioes.values():
            for esc in reg.escadas:
                if esc.reg_destino != reg.id:
                    reg.vizinhos.add(esc.reg_destino)
                    if esc.reg_destino in self.regioes:
                        self.regioes[esc.reg_destino].vizinhos.add(reg.id)
    
    def regiao_em(self, x, y, z):
        for reg in self.regioes.values():
            if reg.z != z:
                continue
            if reg.x_min <= x <= reg.x_max and reg.y_min <= y <= reg.y_max:
                return reg
        return None
    
    def _h(self, x1, y1, x2, y2):
        return abs(x1 - x2) + abs(y1 - y2)
    
    def _astar_mundo(self, x1, y1, z1, x2, y2, z2, regioes_permitidas=None):
        """A* 2D (ignora Z) - busca no plano XY com mudancas de Z via escadas"""
        
        if regioes_permitidas and len(regioes_permitidas) == 1:
            # So uma regiao: pathfinding 2D simples
            reg = self.regioes[regioes_permitidas[0]]
            return self._astar_2d(x1, y1, x2, y2, reg)
        
        # Multi-regiao: busca no grafo de regioes + escadas
        alvo = (x2, y2, z2)
        
        # A* no espaco de (x, y, z)
        abertos = [(self._h(x1, y1, x2, y2), 0, x1, y1, z1)]
        g_score = {(x1, y1, z1): 0}
        veio_de = {}
        visitados = set()
        
        while abertos:
            _, g, cx, cy, cz = abertos.pop(0)
            estado = (cx, cy, cz)
            
            if estado == alvo:
                caminho = [estado]
                while estado != (x1, y1, z1):
                    estado = veio_de[estado]
                    caminho.append(estado)
                caminho.reverse()
                return caminho
            
            if estado in visitados:
                continue
            visitados.add(estado)
            
            reg = self.regiao_em(cx, cy, cz)
            if not reg:
                continue
            
            # Movimentos 4-direcoes dentro da mesma regiao
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = cx+dx, cy+dy
                if regioes_permitidas:
                    nreg = self.regiao_em(nx, ny, cz)
                    if not nreg or nreg.id not in regioes_permitidas:
                        continue
                novo_estado = (nx, ny, cz)
                tent_g = g + 1
                if novo_estado not in g_score or tent_g < g_score[novo_estado]:
                    g_score[novo_estado] = tent_g
                    f = tent_g + self._h(nx, ny, x2, y2) + abs(cz - z2) * 2
                    veio_de[novo_estado] = estado
                    abertos.append((f, tent_g, nx, ny, cz))
                    abertos.sort(key=lambda x: x[0])
            
            # Escadas: mudam de Z
            for esc in reg.escadas:
                ex, ey, ez = esc.origem
                if abs(ex - cx) + abs(ey - cy) <= 2:
                    dx, dy, dz = esc.destino
                    nreg = self.regiao_em(dx, dy, dz)
                    if regioes_permitidas and nreg and nreg.id not in regioes_permitidas:
                        continue
                    novo_estado = (dx, dy, dz)
                    tent_g = g + 2  # custo extra para subir escada
                    if novo_estado not in g_score or tent_g < g_score[novo_estado]:
                        g_score[novo_estado] = tent_g
                        f = tent_g + self._h(dx, dy, x2, y2) + abs(dz - z2) * 2
                        veio_de[novo_estado] = estado
                        abertos.append((f, tent_g, dx, dy, dz))
                        abertos.sort(key=lambda x: x[0])
        
        return None
    
    def _astar_2d(self, x1, y1, x2, y2, regiao):
        """A* 2D dentro de uma regiao"""
        abertos = [(self._h(x1, y1, x2, y2), x1, y1)]
        g_score = {(x1, y1): 0}
        veio_de = {}
        visitados = set()
        
        while abertos:
            _, cx, cy = abertos.pop(0)
            
            if (cx, cy) == (x2, y2):
                caminho = [(cx, cy)]
                while (cx, cy) != (x1, y1):
                    cx, cy = veio_de[(cx, cy)]
                    caminho.append((cx, cy))
                caminho.reverse()
                return [(x, y, regiao.z) for (x, y) in caminho]
            
            if (cx, cy) in visitados:
                continue
            visitados.add((cx, cy))
            
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = cx+dx, cy+dy
                if not (regiao.x_min <= nx <= regiao.x_max and regiao.y_min <= ny <= regiao.y_max):
                    continue
                if (nx, ny) in visitados:
                    continue
                
                tent_g = g_score[(cx, cy)] + 1
                if (nx, ny) not in g_score or tent_g < g_score[(nx, ny)]:
                    g_score[(nx, ny)] = tent_g
                    veio_de[(nx, ny)] = (cx, cy)
                    abertos.append((tent_g + self._h(nx, ny, x2, y2), nx, ny))
                    abertos.sort(key=lambda x: x[0])
        
        return None
    
    def caminho(self, x1, y1, z1, x2, y2, z2):
        """Encontra caminho entre dois pontos no mundo"""
        r1 = self.regiao_em(x1, y1, z1)
        r2 = self.regiao_em(x2, y2, z2)
        if not r1 or not r2:
            return None
        
        # A* no grafo de regioes
        caminho_regioes = self._astar_regioes(r1.id, r2.id)
        if caminho_regioes is None:
            return self._astar_mundo(x1, y1, z1, x2, y2, z2, [r1.id, r2.id])
        
        # Se mesma regiao, pathfinding direto
        if r1.id == r2.id:
            return self._astar_2d(x1, y1, x2, y2, r1)
        
        return self._astar_mundo(x1, y1, z1, x2, y2, z2, caminho_regioes)
    
    def _astar_regioes(self, orig_id, dest_id):
        """A* no grafo de regioes"""
        r_orig = self.regioes.get(orig_id)
        r_dest = self.regioes.get(dest_id)
        if not r_orig or not r_dest:
            return None
        
        abertos = [(abs(r_orig.centro[0]-r_dest.centro[0]) + abs(r_orig.centro[1]-r_dest.centro[1]), orig_id)]
        g_score = {orig_id: 0}
        veio_de = {}
        visitados = set()
        
        while abertos:
            _, cid = abertos.pop(0)
            if cid == dest_id:
                caminho = [dest_id]
                while cid != orig_id:
                    cid = veio_de[cid]
                    caminho.append(cid)
                caminho.reverse()
                return caminho
            
            if cid in visitados:
                continue
            visitados.add(cid)
            
            reg = self.regioes.get(cid)
            if not reg:
                continue
            
            for vid in reg.vizinhos:
                if vid in visitados:
                    continue
                vreg = self.regioes.get(vid)
                if not vreg:
                    continue
                
                tent_g = g_score[cid] + 1
                if vid not in g_score or tent_g < g_score[vid]:
                    g_score[vid] = tent_g
                    f = tent_g + abs(vreg.centro[0]-r_dest.centro[0]) + abs(vreg.centro[1]-r_dest.centro[1])
                    veio_de[vid] = cid
                    abertos.append((f, vid))
                    abertos.sort(key=lambda x: x[0])
        
        return None
    
    def distancia(self, x1, y1, z1, x2, y2, z2):
        caminho = self.caminho(x1, y1, z1, x2, y2, z2)
        if caminho:
            return len(caminho) - 1
        return abs(x1-x2) + abs(y1-y2) + abs(z1-z2) * 10
    
    def ponto_central(self, regiao_id):
        reg = self.regioes.get(regiao_id)
        if reg:
            return (reg.centro[0], reg.centro[1], reg.z)
        return None


if __name__ == "__main__":
    import time
    print("=" * 60)
    print("MUNDO TIBIA - Pathfinding (VALIDACAO)")
    print("=" * 60)
    
    t0 = time.time()
    mapa = MapaTibia()
    print(f"Carregado em {time.time()-t0:.3f}s")
    
    # Estatisticas por andar
    for z in sorted(mapa.por_z.keys()):
        regs = mapa.por_z[z]
        print(f"  Z={z}: {len(regs)} regioes, {sum(r.n_tiles for r in regs)} tiles")
    
    # Testes de pathfinding
    print("\nTestes de pathfinding:")
    
    # Regiao 0: Z7_R0 (centro ~971,995)
    cent0 = mapa.ponto_central(0)
    if cent0:
        x0, y0, z0 = cent0
        print(f"  Regiao 0 centro: ({x0},{y0},{z0})")
        
        # Andar 5 passos pra cada direcao
        for destino in [(x0+5, y0, z0), (x0, y0+5, z0), (x0-5, y0, z0)]:
            dx, dy, dz = destino
            t1 = time.time()
            cam = mapa.caminho(x0, y0, z0, dx, dy, dz)
            dt = time.time() - t1
            if cam:
                print(f"    ({x0},{y0}) -> ({dx},{dy}): {len(cam)-1} passos em {dt:.3f}s")
            else:
                print(f"    ({x0},{y0}) -> ({dx},{dy}): sem caminho ({dt:.3f}s)")
    
    # Teste inter-regiao (se houver vizinhos)
    for rid in [0, 1, 5]:
        reg = mapa.regioes.get(rid)
        if reg and reg.vizinhos:
            for vid in list(reg.vizinhos)[:1]:
                vreg = mapa.regioes.get(vid)
                if vreg:
                    t1 = time.time()
                    cam = mapa.caminho(reg.centro[0], reg.centro[1], reg.z,
                                      vreg.centro[0], vreg.centro[1], vreg.z)
                    dt = time.time() - t1
                    if cam:
                        print(f"  {reg.nome} -> {vreg.nome}: {len(cam)-1} passos em {dt:.3f}s")
                        print(f"    Primeiros: {cam[:3]} ... Ultimos: {cam[-3:]}")
                    else:
                        print(f"  {reg.nome} -> {vreg.nome}: sem caminho ({dt:.3f}s)")
    
    # Grafo de regioes
    print(f"\nRegioes com conexoes:")
    for rid in sorted(mapa.regioes.keys()):
        reg = mapa.regioes[rid]
        if reg.vizinhos:
            print(f"  {reg.nome} -> {[mapa.regioes[v].nome for v in sorted(reg.vizinhos)]}")
    
    print("\n" + "=" * 60)
