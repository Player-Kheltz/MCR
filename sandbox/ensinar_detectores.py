"""Ensinar detectores via MCR-DevIA"""
import subprocess

cmds = [
    ['Detector: divisao por zero potencial', 'Expressoes como atk / (def - 10) podem dividir por zero', 'Detectar divisao por expressao que pode resultar em zero', 'deteccao'],
    ['Detector: chave string vs numero', 'config[1] e config["1"] sao chaves diferentes em Lua', 'Detectar mesmo objeto usando chave string e numero', 'deteccao'],
    ['Detector: SQL injection potencial', 'Concatenar string em query permite SQL injection', 'Detectar db.query com .. e aspas', 'deteccao'],
    ['Detector: loop infinito sem break', 'while true sem break nunca termina', 'Detectar while true e verificar se ha break', 'deteccao'],
    ['Detector: setmetatable sobrescreve metatable', 'setmetatable em objeto nativo quebra metatable padrao', 'Detectar setmetatable em arquivos Lua', 'deteccao'],
    ['Detector: codigo morto apos return', 'Codigo apos return nunca executa', 'Detectar linhas entre return e end', 'deteccao'],
]

for args in cmds:
    cmd = ['python', 'E:/Projeto MCR/scripts/mcr_devia/mcr_devia.py', 'ensinar'] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip())

print('6 detectores ensinados ao MCR-DevIA. Total: 77 licoes')
