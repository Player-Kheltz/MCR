"""Blank Filler Universal — "Código criar código" + LLM preencher blanks.
Engine generica: qualquer conteudo (codigo, docs, analises) pode ter blanks
que sao preenchidos pela IA individualmente, reduzindo alucinacao e erros.

Fluxo:
  1. Esqueleto: estrutura com marcadores @BLANK_ID
  2. Listar blanks: extrai os IDs
  3. Preencher: IA preenche CADA blank com contexto focado
  4. Montar: substitui blanks no esqueleto

Uso:
    bf = BlankFiller(ia)
    skel = bf.gerar_esqueleto("crie um validador de email", "codigo")
    preenchido = bf.preencher_tudo(skel, "validador de email")
"""
import re, os


class BlankFiller:
    """Engine universal de preenchimento de blanks via IA."""
    
    MARKER = '@BLANK_'
    
    def __init__(self, ia, tools=None):
        self._ia = ia
        self._tools = tools  # ToolOrchestrator opcional
    
    def gerar_esqueleto(self, contexto, tipo='texto', max_blanks=5):
        """Gera um esqueleto com @BLANK_ID a partir de um contexto.
        
        Args:
            contexto: Descricao do que gerar
            tipo: 'codigo' | 'texto' | 'analise' | 'relatorio'
            max_blanks: Maximo de blanks no esqueleto
        
        Returns:
            str: Esqueleto com marcadores @BLANK_X
        """
        instrucao_tipo = {
            'codigo': 'Gere a ESTRUTURA do codigo (funcoes, assinaturas, classes). '
                      'Marque as PARTES A IMPLEMENTAR com @BLANK_1, @BLANK_2 etc.',
            'texto': 'Gere a ESTRUTURA do texto (secoes, topicos). '
                     'Marque ANALISES que precisam de preenchimento com @BLANK_1.',
            'analise': 'Gere a ESTRUTURA da analise (argumentos, evidencias). '
                       'Marque CONCLUSAO com @BLANK_1.',
            'relatorio': 'Gere o ESQUELETO do relatorio com secoes. '
                         'Marque CONTEUDO a ser preenchido com @BLANK_N.',
        }.get(tipo, 'Gere o esqueleto. Marque partes a preencher com @BLANK_N.')
        
        prompt = (
            f"[SISTEMA]\nVoce e um gerador de esqueletos.\n{instrucao_tipo}\n\n"
            f"[CONTEXTO]\n{contexto}\n\n"
            f"[REGRA]\nMaximo de {max_blanks} blanks. Use @BLANK_1, @BLANK_2 etc.\n"
            f"Gere APENAS o esqueleto, sem preencher os blanks.\n"
            f"Responda em PT-BR."
        )
        
        return self._ia.gerar(prompt, 0.3, 'leve') or ""
    
    def listar_blanks(self, esqueleto):
        """Extrai todos os IDs de blanks de um esqueleto.
        
        Returns:
            list: ['@BLANK_1', '@BLANK_2', ...]
        """
        return list(set(re.findall(r'@BLANK_\w+', esqueleto)))
    
    def preencher_blank(self, esqueleto, blank_id, contexto, tipo='texto'):
        """Preenche UM blank especifico com ajuda da IA.
        
        O prompt inclui o esqueleto + o blank especifico + contexto.
        A IA gera APENAS o conteudo para aquele blank.
        """
        prompt = (
            f"[SISTEMA]\nVoce esta preenchendo um blank em um esqueleto.\n"
            f"Preencha APENAS o blank {blank_id}, de forma ESPECIFICA e CONCISA.\n"
            f"Nao gere o esqueleto todo, apenas o conteudo do blank.\n\n"
            f"[ESQUELETO]\n{esqueleto}\n\n"
            f"[BLANK A PREENCHER]\n{blank_id}\n\n"
            f"[CONTEXTO]\n{contexto}\n\n"
            f"[RESPOSTA]\n"
            f"Apenas o texto para {blank_id}, sem o nome do blank."
        )
        
        resultado = self._ia.gerar(prompt, 0.3, 'leve') or ''
        return resultado.strip()
    
    def preencher_tudo(self, esqueleto, contexto, tipo='texto', modo='cadeia', callback=None):
        """Preenche TODOS os blanks do esqueleto.
        
        Args:
            modo: 'cadeia' = cada blank ve o resultado dos anteriores (default)
                  'paralelo' = blanks independentes (cada um recebe so o contexto base)
            callback: funcao(blank_id, conteudo) para SSE/narrador
        """
        blanks = self.listar_blanks(esqueleto)
        resultado = esqueleto
        contexto_acumulado = contexto
        
        for blank_id in sorted(blanks):
            # Contexto local (2 linhas antes/depois do blank)
            linhas = resultado.split('\n')
            contexto_local = ""
            for i, linha in enumerate(linhas):
                if blank_id in linha:
                    ini = max(0, i - 2)
                    fim = min(len(linhas), i + 3)
                    contexto_local = '\n'.join(linhas[ini:fim])
                    break
            
            # Se modo cadeia, inclui contexto dos blanks anteriores
            ctx_final = contexto
            if modo == 'cadeia' and contexto_acumulado != contexto:
                ctx_final = contexto_acumulado
            
            prompt_blank = (
                f"[SISTEMA]\nPreencha o blank {blank_id} no contexto abaixo.\n"
                f"Responda APENAS com o conteudo para {blank_id}.\n"
                f"Nao inclua o nome do blank.\n\n"
                f"[CONTEXTO LOCAL]\n{contexto_local}\n\n"
                f"[CONTEXTO GERAL]\n{ctx_final}\n\n"
                f"[BLANK]\n{blank_id}\n\n"
                f"[RESPOSTA]"
            )
            
            conteudo_blank = self._ia.gerar(prompt_blank, 0.3, 'leve') or ''
            conteudo_blank = conteudo_blank.strip()
            
            # Substitui o blank no resultado
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
