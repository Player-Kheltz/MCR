[find_example] Tipo: python_script | Projeto: Script básico
[find_example] Encontrados 1 exemplo
=== EXEMPLO: scripts\show_time.py (score:3) ===
#!/usr/bin/env python3
"""
show_time.py â€” Mostra a hora atual no sistema.

Uso:
    python "scripts/show_time.py"
"""

import datetime

def show_current_time():
    current_time = datetime.datetime.now()
    print("Hora atual:", current_time.strftime("%H:%M:%S"))

if __name__ == "__main__":
    show_current_time()