"""Add self-awareness check after each heartbeat beat"""
with open(r'E:\Projeto MCR\sandbox\mcr_heartbeat.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the end of bater() method and add self-check
old = """        log(f'Saude: {n_licoes} licoes, {n_reparos} reparos, batida #{self.batidas}')"""

new = """        log(f'Saude: {n_licoes} licoes, {n_reparos} reparos, batida #{self.batidas}')
        
        # Auto-consciencia: verifica se esta preso em algum padrao
        self._auto_check(n_reparos)"""

c = c.replace(old, new)

# Add the _auto_check method before the main block
old_main = """if __name__ == '__main__':"""

new_method = """    def _auto_check(self, n_reparos):
        """Verifica se esta repetindo o mesmo erro."""
        # Se o numero de reparos nao muda, algo esta errado
        if hasattr(self, 'ultimos_reparos'):
            if self.ultimos_reparos == n_reparos:
                log('[AUTO-CONSCIENCIA] Reparos nao evoluiram. Possivel loop.')
                # Toque mais forte se ja tentou varias vezes
                if self.batidas >= 3:
                    log('[AUTO-CONSCIENCIA] Toque: ja tentei reparar ' + str(self.batidas) + 'x sem sucesso. Preciso de uma abordagem diferente.')
            else:
                log('[AUTO-CONSCIENCIA] Reparos evoluindo. Continuando.')
        self.ultimos_reparos = n_reparos

""" + old_main

c = c.replace(old_main, new_method)

with open(r'E:\Projeto MCR\sandbox\mcr_heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'heartbeat.py', 'exec')
    print('OK! Auto-consciencia integrada ao batimento cardiaco!')
except SyntaxError as e:
    print(f'Error: {e}')
