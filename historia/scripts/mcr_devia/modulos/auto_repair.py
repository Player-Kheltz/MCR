"""AutoRepair — Repara codigo com erro baseado na mensagem do validador.

Quando o validador detecta um erro (linha, descricao), o AutoRepair
usa o FAST model para corrigir o codigo em UMA tentativa.

Conceito: Se o validador ACHOU o erro, o reparador SABE o que corrigir.
Nao precisa de loop — erro conhecido = correcao direta.

Uso:
    reparador = AutoRepair(ia)
    codigo_corrigido = reparador.reparar(codigo_errado, erros, linguagem)
"""
from modulos.util import extrair_codigo_puro


class AutoRepair:
    """Corrige codigo com erro baseado na mensagem do validador.
    
    Uma unica tentativa — com o erro apontado (linha, descricao),
    o LLM consegue corrigir de primeira.
    """

    def __init__(self, ia):
        self.ia = ia

    def reparar(self, codigo, erros, linguagem):
        """Repara codigo com erro em UMA tentativa.
        
        Args:
            codigo: Codigo com erro
            erros: Lista de mensagens de erro do validador
            linguagem: Linguagem do codigo (python, javascript, etc)
        
        Returns:
            Codigo corrigido (string), ou codigo original se falhar
        """
        if not erros or not codigo:
            return codigo

        prompt = (
            f"Corrija o erro abaixo no codigo {linguagem}.\n"
            f"ERRO: {erros[0]}\n\n"
            f"CODIGO:\n```{linguagem}\n{codigo}\n```\n\n"
            f"Responda APENAS com o codigo CORRIGIDO, sem explicacao. "
            f"CODIGO CORRIGIDO:"
        )

        try:
            codigo_reparado = self.ia.fast(prompt, 0.2, 'leve')
            if codigo_reparado:
                codigo_puro = extrair_codigo_puro(codigo_reparado)
                if len(codigo_puro) > len(codigo) * 0.3:  # pelo menos 30% do tamanho original
                    return codigo_puro
        except Exception as e:
            print(f"[AutoRepair] Erro: {e}")

        return codigo

    def reparar_e_validar(self, codigo, erros, linguagem, tool_orch):
        """Repara e re-valida em uma unica chamada.
        
        Retorna o codigo corrigido se a re-validacao passar.
        """
        codigo_reparado = self.reparar(codigo, erros, linguagem)
        if codigo_reparado != codigo:
            r = tool_orch.executar('validar_codigo', {'codigo': codigo_reparado})
            if r.get('resultado', {}).get('valido'):
                return codigo_reparado, True
        return codigo, False

    def reparar_com_validacao(self, codigo, linguagem="lua", tool_orch=None):
        """Repara e valida o codigo automaticamente, com ate 3 tentativas.
        
        Usa validar_codigo do ToolOrchestrator para verificar o resultado.
        Se tool_orch for None, retorna a primeira tentativa sem validacao.
        
        Args:
            codigo: Codigo com erro (string)
            linguagem: Linguagem do codigo (padrao 'lua')
            tool_orch: ToolOrchestrator para validacao (opcional)
        
        Returns:
            dict: {'sucesso': bool, 'corrigido': str}
        """
        erros_dummy = ["Erro desconhecido - validacao via reparar_com_validacao"]
        for _tentativa in range(3):
            codigo_reparado = self.reparar(codigo, erros_dummy, linguagem)
            if tool_orch and codigo_reparado != codigo:
                r = tool_orch.executar('validar_codigo', {'codigo': codigo_reparado})
                if r.get('resultado', {}).get('valido'):
                    return {'sucesso': True, 'corrigido': codigo_reparado}
            elif codigo_reparado == codigo:
                break
            codigo = codigo_reparado
        return {'sucesso': False, 'corrigido': codigo}
