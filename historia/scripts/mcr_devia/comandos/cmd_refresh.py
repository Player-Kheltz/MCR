"""Comando: refresh - Hot-reload de comandos sem reiniciar."""
def register():
    return {
        "name": "refresh",
        "desc": "Recarrega todos os comandos de comandos/ sem reiniciar o kernel",
        "handler": execute,
        "args": [],
        "categoria": "kernel",
    }

def execute(kg, ia, args, ctx_crew=None):
    # Access kernel via context - passed through kg attribute
    kernel = getattr(kg, '_kernel_ref', None)
    if not kernel:
        print('[Refresh] Kernel nao disponivel. Use MCR_DevIA-Kernel.py')
        return True
    n = kernel.loader.refresh()
    print(f'[Refresh] {n} comandos recarregados')
    return True
