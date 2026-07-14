"""Mina dados reais dos diretórios Canary para substituir hardcodes."""
import sys, json, re, statistics
from pathlib import Path
from collections import Counter, defaultdict
sys.path.insert(0, 'E:/MCR')
from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR

def minerar_npcs():
    """Extrai looktype e health de NPCs reais."""
    looktypes = defaultdict(list)
    healths = []
    keywords = ['ferreiro','mago','guarda','vendedor','mercador','elfo','anao',
                'anão','orc','padeiro','druida','alquimista','cavaleiro','ladrao',
                'arqueiro','taverneiro','carpinteiro','artesao','bibliotecario',
                'cocheiro','mensageiro','cozinheiro','tecelao','minerador','pescador',
                'lenhador','ourives','curandeiro','cacador']
    
    for f in CANARY_NPC_DIR.glob('*.lua'):
        try:
            c = f.read_text(encoding='latin-1', errors='replace')
        except Exception:
            continue
        
        # Extrai lookType
        m = re.search(r'lookType\s*=\s*(\d+)', c)
        if m:
            lt = int(m.group(1))
            fname = f.stem.lower()
            for kw in keywords:
                if kw in fname:
                    looktypes[kw].append(lt)
        
        # Extrai health
        m = re.search(r'npcConfig\.health\s*=\s*(\d+)', c)
        if m:
            healths.append(int(m.group(1)))
    
    # Computa mediana por keyword
    looktype_map = {}
    for kw, vals in looktypes.items():
        if len(vals) >= 2:
            try:
                looktype_map[kw] = int(statistics.median(vals))
            except Exception:
                looktype_map[kw] = max(set(vals), key=vals.count)
    
    health_median = int(statistics.median(healths)) if healths else 100
    
    return looktype_map, health_median, len(healths)


def minerar_monstros():
    """Extrai stats, race, loot de monstros reais."""
    stats_all = []  # (health, exp, speed)
    race_map = defaultdict(Counter)  # keyword -> {race: count}
    loot_items = Counter()  # (id, chance, maxCount) -> count
    name_tokens = Counter()
    
    for f in CANARY_MONSTER_DIR.glob('**/*.lua'):
        try:
            c = f.read_text(encoding='latin-1', errors='replace')
        except Exception:
            continue
        
        # Extrai stats
        h = re.search(r'health\s*=\s*(\d+)', c)
        e = re.search(r'experience\s*=\s*(\d+)', c)
        s = re.search(r'speed\s*=\s*(\d+)', c)
        race_m = re.search(r'race\s*=\s*"(\w+)"', c)
        
        if h and e and s:
            stats_all.append((int(h.group(1)), int(e.group(1)), int(s.group(1))))
        
        # Extrai race -> keyword mapping
        if race_m:
            race = race_m.group(1)
            fname = f.stem.lower()
            tokens = re.findall(r'[a-z]{3,}', fname)
            for t in tokens:
                race_map[t][race] += 1
                name_tokens[t] += 1
        
        # Extrai loot
        for lm in re.finditer(r'\{\s*id\s*=\s*(\d+)\s*,\s*chance\s*=\s*(\d+)\s*,\s*maxCount\s*=\s*(\d+)\s*\}', c):
            loot_items[(int(lm.group(1)), int(lm.group(2)), int(lm.group(3)))] += 1
    
    # Classifica tiers por percentil de health
    hs = sorted(s[0] for s in stats_all)
    n = len(hs)
    p33 = hs[int(n*0.33)] if n > 2 else 300
    p66 = hs[int(n*0.66)] if n > 2 else 800
    
    low = [(h,e,s) for h,e,s in stats_all if h <= p33]
    mid = [(h,e,s) for h,e,s in stats_all if p33 < h <= p66]
    high = [(h,e,s) for h,e,s in stats_all if h > p66]
    
    def median_stats(tier):
        if not tier: return (250, 400, 120)
        return (int(statistics.median([t[0] for t in tier])),
                int(statistics.median([t[1] for t in tier])),
                int(statistics.median([t[2] for t in tier])))
    
    stats_map = {'low': median_stats(low), 'medium': median_stats(mid), 'high': median_stats(high)}
    
    # Top loot items
    top_loot = loot_items.most_common(3)
    loot_default = [{'id': lid, 'chance': lc, 'maxCount': lm} for (lid, lc, lm), _ in top_loot]
    
    return {
        'stats': stats_map, 'loot': loot_default,
        'race_map': dict(race_map), 'n_monstros': len(stats_all),
        'thresholds': (p33, p66), 'name_tokens': dict(name_tokens.most_common(50)),
    }


if __name__ == '__main__':
    lm, hm, n_npc = minerar_npcs()
    md = minerar_monstros()
    
    print(f'NPCs analisados: {n_npc}')
    print(f'Health mediana: {hm}')
    print(f'Looktypes ({len(lm)}):')
    for k, v in sorted(lm.items()):
        print(f'  {k}: {v}')
    print(f'\nMonstros analisados: {md["n_monstros"]}')
    print(f'Tiers (p33={md["thresholds"][0]}, p66={md["thresholds"][1]}):')
    for tier, (h, e, s) in md['stats'].items():
        print(f'  {tier}: hp={h}, exp={e}, spd={s}')
    print(f'Top loot: {md["loot"]}')
    print(f'Race map sample (5):')
    for kw in list(md['race_map'].keys())[:5]:
        print(f'  {kw}: {md["race_map"][kw].most_common(3)}')
