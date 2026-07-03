"""Blank Filler Universal — preenche blanks via MCR em vez de LLM."""
import re, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
try:
    from MCR import MCRMotor, MCRPreencher, MCRGenerator
    _mcr_motor = MCRMotor()
    _mcr_preencher = MCRPreencher(_mcr_motor)
    _mcr_gen = MCRGenerator(_mcr_motor, _mcr_preencher)
    _TEM_MCR = True
except ImportError:
    _TEM_MCR = False


class BlankFiller:
    """Engine universal de preenchimento de blanks via MCR."""
    
    MARKER = '@BLANK_'
    
    def __init__(self, ia=None, tools=None):
        self._ia = ia
        self._tools = tools
    
    def gerar_esqueleto(self, contexto, tipo='texto', max_blanks=5):
        if _TEM_MCR:
            return f"@BLANK_1 para {contexto[:30]}"
        if self._ia:
            prompt = f"[SISTEMA]\nGere esqueleto com @BLANK_N.\n\n[CONTEXTO]\n{contexto}\n\n[REGRA]\nMax {max_blanks} blanks.\n[ESQUELETO]"
            return self._ia.gerar(prompt, 0.3, 'leve') or ""
        return f"@BLANK_1"

    def listar_blanks(self, esqueleto):
        return list(set(re.findall(r'@BLANK_\w+', esqueleto)))
    
    def preencher_blank(self, esqueleto, blank_id, contexto, tipo='texto'):
        if _TEM_MCR:
            conteudo = _mcr_preencher.executar(blank_id)
            if conteudo and conteudo != blank_id:
                return conteudo
        if self._ia:
            prompt = f"[SISTEMA]\nPreencha {blank_id}.\n\n[ESQUELETO]\n{esqueleto}\n\n[BLANK]\n{blank_id}\n\n[RESPOSTA]"
            resultado = self._ia.gerar(prompt, 0.3, 'leve') or ''
            return resultado.strip()
        return f"conteudo_{blank_id}"
    
    def preencher_tudo(self, esqueleto, contexto, tipo='texto', modo='cadeia', callback=None):
        blanks = self.listar_blanks(esqueleto)
        resultado = esqueleto
        contexto_acumulado = contexto
        
        for blank_id in sorted(blanks):
            if _TEM_MCR:
                conteudo_blank = _mcr_preencher.executar(blank_id)
            elif self._ia:
                prompt = f"[SISTEMA]\nPreencha {blank_id}.\n\n[CONTEXTO]\n{contexto}\n\n[BLANK]\n{blank_id}\n\n[RESPOSTA]"
                conteudo_blank = self._ia.gerar(prompt, 0.3, 'leve') or ''
                conteudo_blank = conteudo_blank.strip()
            else:
                conteudo_blank = f"conteudo_{blank_id}"
            
            resultado = resultado.replace(blank_id, conteudo_blank, 1)
            if modo == 'cadeia':
                contexto_acumulado += '\n' + conteudo_blank
            if callback:
                callback(blank_id, conteudo_blank)
        
        return resultado
    
    def gerar_e_preencher(self, contexto, tipo='texto', callback=None):
        """Metodo unico: gera esqueleto + preenche todos os blanks.
        Retorna (esqueleto, preenchido, blanks)."""
        esqueleto = self.gerar_esqueleto(contexto, tipo)
        preenchido = self.preencher_tudo(esqueleto, contexto, tipo, callback)
        blanks = self.listar_blanks(esqueleto)
        return esqueleto, preenchido, blanks
