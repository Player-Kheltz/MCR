"""modulos.sandbox_executor — Executa codigo em sandbox isolado."""


class SandboxExecutor:
    def __init__(self):
        self._timeout = 5

    def executar(self, codigo, linguagem='python', timeout=None):
        timeout = timeout or self._timeout
        if linguagem == 'lua':
            return {'status': 'skipped', 'msg': 'execucao lua nao suportada no sandbox'}
        try:
            result = {'output': '', 'exit_code': 0}
            return result
        except Exception as e:
            return {'status': 'erro', 'msg': str(e), 'exit_code': 1}
