```python
#!/usr/bin/env python3
"""
show_time.py â€” Script Python para mostrar a hora atual.

Uso:
    python "scripts/show_time.py"
"""

import datetime

def show_current_time():
    current_time = datetime.datetime.now()
    print(f"A hora atual é: {current_time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    show_current_time()
```