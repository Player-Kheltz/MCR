"""modulos.agent_loop — Loop de agente para execucao autonoma."""


class AgentLoop:
    def __init__(self):
        self._passos = []

    def executar(self, tarefa, max_passos=5):
        self._passos.append({'tarefa': tarefa, 'status': 'executado'})
        return {'status': 'ok', 'passos': len(self._passos)}
