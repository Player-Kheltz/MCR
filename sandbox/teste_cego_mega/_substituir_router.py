#!/usr/bin/env python3
"""Substitui o router regex por FAST chain no supervisor.py."""
import re

path = r"E:\Projeto MCR\scripts\mcr_devia\modulos\supervisor.py"
with open(path, "r", encoding="utf-8") as f:
    s = f.read()

# Encontra a secao do router
start_markers = ["ROTEADOR UNIVERSAL DE INTENCOES", "# Matematica basica", "Router: que horas/data"]
end_marker = "FASE 1: MENTE PENSA"

start = -1
for m in start_markers:
    pos = s.find(m)
    if pos >= 0:
        start = pos
        break

end = s.find(end_marker)

if start > 0 and end > 0:
    # Vai para o inicio da linha
    s_start = s.rfind("\n", 0, start)
    s_end = s.rfind("\n", 0, end)
    
    new_router = (
        '        # ====================================================\n'
        '        # ROTEADOR IA EM CADEIA (FAST1 classifica -> FAST2 delega)\n'
        '        # ====================================================\n'
        '        import subprocess as _sub, datetime as _dt\n'
        '        _respostas_rapidas = []\n'
        '        _precisa_ia = False\n\n'
        '        try:\n'
        '            from modulos.util import fast as _rfast\n'
        '            # FAST 1: classifica a mensagem em topicos\n'
        '            _r1 = _rfast("Classifique em topicos separados por virgula: " + texto[:500] + " Topicos: HORARIO, TEMPO, MATEMATICA, PI, CRIACAO, SAUDE, CURIOSIDADE, RECURSOS, OUTRO. Responda:", 0.1, "leve")\n'
        '            if _r1:\n'
        '                for _t in [t.strip() for t in _r1.upper().split(",")]:\n'
        '                    # FAST 2: decide ferramenta\n'
        '                    _r2 = _rfast("Topico: " + _t + " Ferramenta: PYTHON, TASKLIST, IA? R:", 0.1, "leve")\n'
        '                    if _r2:\n'
        '                        _ferr = _r2.strip().upper()\n'
        '                        if "PYTHON" in _ferr or "HORARIO" in _t or "TEMPO" in _t:\n'
        '                            if "HORARIO" in _t or "TEMPO" in _t:\n'
        '                                _agora = _dt.datetime.now()\n'
        '                                _respostas_rapidas.append("Sao " + _agora.strftime("%H:%M:%S") + " do dia " + _agora.strftime("%d/%m/%Y"))\n'
        '                                _amanha = _agora.replace(hour=0, minute=0, second=0, microsecond=0) + _dt.timedelta(days=1)\n'
        '                                _diff = int((_amanha - _agora).total_seconds())\n'
        '                                if _diff > 0: _respostas_rapidas.append("Faltam " + str(_diff) + " segundos para meia-noite")\n'
        '                            if "MATEMATICA" in _t:\n'
        '                                for _m in re.findall(r"(\\d+)\\s*[\\*x]\\s*(\\d+)", texto):\n'
        '                                    _respostas_rapidas.append(str(_m[0]) + " x " + str(_m[1]) + " = " + str(int(_m[0])*int(_m[1])))\n'
        '                            if "PI" in _t:\n'
        '                                _respostas_rapidas.append("PI = 3.1415926535897932384626433832795...")\n'
        '                        elif "TASKLIST" in _ferr or "RECURSOS" in _t:\n'
        '                            _rr = _sub.run(\'tasklist /fi \"STATUS eq running\" /nh\', capture_output=True, text=True, timeout=15, shell=True)\n'
        '                            if _rr and _rr.stdout:\n'
        '                                _respostas_rapidas.append("Processos ativos: " + str(len([l for l in _rr.stdout.split(chr(10)) if l.strip()])))\n'
        '                        if "CRIACAO" in _t or "SAUDE" in _t or "CURIOSIDADE" in _t or "OUTRO" in _t:\n'
        '                            _precisa_ia = True\n'
        '        except:\n'
        '            pass\n\n'
        '        if _respostas_rapidas and _precisa_ia:\n'
        '            contexto_extra += chr(10) + "[PARCIAL] " + chr(10).join(_respostas_rapidas) + chr(10) + "[/PARCIAL]" + chr(10)\n'
        '        elif _respostas_rapidas:\n'
        '            return chr(10).join(_respostas_rapidas)\n'
    )
    
    s = s[:s_start+1] + new_router + s[s_end+1:]
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)
    print("Router substituido com sucesso!")
else:
    print(f"Erro: start={start}, end={end}")
