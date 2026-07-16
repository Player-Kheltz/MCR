import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

from pathlib import Path
from mcr.discriminador_anatomia import avaliar_sprite

print('=== Sprites da Esfera v2 ===')
for f in sorted(Path(_ROOT) / 'poc_output' / 'sprites_esfera_v2').glob('*.png'):
    r = avaliar_sprite(str(f))
    s = 'OK' if r['ok'] else 'FALHOU'
    print('  %s: %.3f (%s) reg=%d cores=%d fg=%.2f dom=%.2f' % (
        f.name, r['score'], s, r['n_regioes'], r['n_cores'], r['prop_fg'], r['dominancia']))

print()
print('=== Orcs de referência ===')
for f in sorted((Path(_ROOT) / 'poc_output').glob('orc_*_ref.png'))[:5]:
    r = avaliar_sprite(str(f))
    s = 'OK' if r['ok'] else 'FALHOU'
    print('  %s: %.3f (%s) reg=%d cores=%d fg=%.2f dom=%.2f' % (
        f.name, r['score'], s, r['n_regioes'], r['n_cores'], r['prop_fg'], r['dominancia']))

print()
print('=== Shields de referência ===')
for f in sorted((Path(_ROOT) / 'poc_output').glob('shield_ref_*.png'))[:5]:
    r = avaliar_sprite(str(f))
    s = 'OK' if r['ok'] else 'FALHOU'
    print('  %s: %.3f (%s) reg=%d cores=%d fg=%.2f dom=%.2f' % (
        f.name, r['score'], s, r['n_regioes'], r['n_cores'], r['prop_fg'], r['dominancia']))
