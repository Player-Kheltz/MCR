code = '''        "Analisa arquivo."
        path_analisar = args[0]
        desc_extra = ""
        if len(args) > 1:
            desc_extra = " ".join(args[1:])'''

print('Original:')
for i, line in enumerate(code.split('\n')):
    print(f'  {i}: len={len(line)} {repr(line[:60])}')

print()
print('After -4:')
for ln in code.split('\n'):
    if ln.startswith('    '):
        print(f'  len={len(ln)} -> {repr(ln[4:][:60])}')
    else:
        print(f'  len={len(ln)} -> {repr(ln[:60])}')
