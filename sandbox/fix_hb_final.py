"""Fix heartbeat properly"""
with open(r'E:\Projeto MCR\sandbox\mcr_heartbeat.py', 'r', encoding='utf-8') as f:
    c = f.read()

# The _auto_check method has issues. Let me look at it more carefully
# and replace it cleanly

# Find where the _auto_check method is
import re
idx = c.find('def _auto_check')
if idx > 0:
    # Remove from _auto_check to __main__
    end = c.find("if __name__ ==")
    if end > idx:
        c = c[:idx] + c[end:]
        print('Removed broken _auto_check method')
    else:
        print('Could not find end marker')
else:
    print('_auto_check not found, might already be fixed')

# Fix the log line about saude (the previous patch may have added extra )
c = c.replace('pass\n        \n        # Auto-consciencia', '\n        # Auto-consciencia')

with open(r'E:\Projeto MCR\sandbox\cr_heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'hb.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
