"""Find duplicate sections in pipeline_executor.py."""
with open('E:/Projeto MCR/Scripts/mcr_devia/modulos/pipeline_executor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all def lines
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('def ') or stripped.startswith('class '):
        print(f'Line {i+1}: {stripped[:80]}')

print(f'\nTotal lines: {len(lines)}')

# Find all VALIDATE sections
for i, line in enumerate(lines):
    if 'VALIDATE' in line and ('==' in line or '#' in line):
        print(f'Line {i+1}: {stripped[:80]}')
