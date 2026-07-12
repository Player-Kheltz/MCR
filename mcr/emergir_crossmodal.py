"""
mcr.emergir_crossmodal — Emergir Cross-Modal (C4).

Despacha ideias criativas por domínio: visual, código, áudio, texto.
Cada domínio tem um handler que converte a ideia em representação específica.

Uso:
    engine = EmergirCrossModal()
    resultado = engine.despachar(
        ideia="E se a textura do orc virasse uma melodia?",
        dominios=['visual', 'audio']
    )
"""
from typing import Dict, List, Optional, Callable
from collections import defaultdict


class DominioHandler:
    """Handler base para um domínio de saída."""
    
    nome = 'base'
    descricao = 'Handler base'
    
    def processar(self, ideia: Dict, contexto: Dict = None) -> Dict:
        """Processa uma ideia neste domínio.
        
        Args:
            ideia: dict com 'ideia', 'conceito_a', 'conceito_b', 'descricao'
            contexto: dict opcional com dados extras (regioes, paleta, etc.)
        
        Returns:
            dict com resultado do processamento
        """
        raise NotImplementedError


class LuaHandler(DominioHandler):
    """Handler para geração de código Lua (Canary OTServ)."""
    
    nome = 'lua'
    descricao = 'Geração de scripts Lua para Canary'
    
    def __init__(self, llm_func: Callable = None):
        self.llm_func = llm_func
    
    def processar(self, ideia: Dict, contexto: Dict = None) -> Dict:
        if not self.llm_func:
            return {'sucesso': False, 'erro': 'LLM não disponível', 'dominio': self.nome}
        
        prompt = self._montar_prompt(ideia, contexto)
        try:
            codigo = self.llm_func(prompt, modelo='qwen2.5-coder:7b')
            return {'sucesso': True, 'codigo': codigo, 'dominio': self.nome, 'prompt': prompt}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'dominio': self.nome}
    
    def _montar_prompt(self, ideia: Dict, contexto: Dict = None) -> str:
        conceito_a = ideia.get('conceito_a', {})
        conceito_b = ideia.get('conceito_b', {})
        return (
            f"Escreva um script Lua para o servidor Canary que implemente:\n\n"
            f"{ideia.get('ideia', '')}\n\n"
            f"Conceito A: {conceito_a.get('tipo', '?')} ({', '.join(conceito_a.get('apis', [])[:2])})\n"
            f"Conceito B: {conceito_b.get('tipo', '?')} ({', '.join(conceito_b.get('apis', [])[:2])})\n\n"
            f"Use APIs canary padrão. O código deve ser funcional e bem comentado."
        )


class VisualHandler(DominioHandler):
    """Handler para processamento visual (sprites, regiões, paleta)."""
    
    nome = 'visual'
    descricao = 'Processamento de sprites e regiões cromáticas'
    
    def processar(self, ideia: Dict, contexto: Dict = None) -> Dict:
        ctx = contexto or {}
        regioes = ctx.get('regioes', [])
        paleta = ctx.get('paleta', {})
        
        if not regioes:
            return {'sucesso': False, 'erro': 'Sem regiões visuais no contexto', 'dominio': self.nome}
        
        # Extrair propriedades visuais
        cores = [r.get('cor_media_rgb', (0, 0, 0)) for r in regioes]
        areas = [r.get('area', 0) for r in regioes]
        exccs = [r.get('excentricidade', 1.0) for r in regioes]
        
        # Gerar descrição visual
        desc = self._descrever_sprite(regioes)
        
        return {
            'sucesso': True,
            'dominio': self.nome,
            'descricao_visual': desc,
            'n_regioes': len(regioes),
            'cores': cores,
            'areas': areas,
            'excentricidades': exccs,
        }
    
    def _descrever_sprite(self, regioes: List[Dict]) -> str:
        """Gera descrição textual de um sprite a partir de suas regiões."""
        partes = []
        for i, r in enumerate(regioes):
            L, a, b = r.get('cor_media_lab', (50, 0, 0))
            area = r.get('area', 0)
            excc = r.get('excentricidade', 1.0)
            
            # Descrever cor
            if L < 30: cor = "escuro"
            elif L < 60: cor = "médio"
            else: cor = "claro"
            
            if abs(a) > 20 and b > 10: cor += " amarelado"
            elif abs(a) > 20 and b < -10: cor += " avermelhado"
            elif a < -20: cor += " esverdeado"
            elif abs(b) > 20: cor += " azulado"
            
            # Descrever forma
            if excc < 1.2: forma = "quadrada"
            elif excc < 2.0: forma = "retangular"
            else: forma = "alongada"
            
            partes.append(f"região {i}: {cor}, {forma}, {area}px")
        
        return "; ".join(partes) if partes else "sprite vazio"


class AudioHandler(DominioHandler):
    """Handler para mapeamento visual → áudio (síntese por parâmetros)."""
    
    nome = 'audio'
    descricao = 'Mapeamento de regiões para parâmetros sonoros'
    
    def processar(self, ideia: Dict, contexto: Dict = None) -> Dict:
        ctx = contexto or {}
        regioes = ctx.get('regioes', [])
        
        if not regioes:
            return {'sucesso': False, 'erro': 'Sem regiões no contexto', 'dominio': self.nome}
        
        # Mapear propriedades visuais → parâmetros sonoros
        notas = []
        for i, r in enumerate(regioes):
            L, a, b = r.get('cor_media_lab', (50, 0, 0))
            area = r.get('area', 0)
            excc = r.get('excentricidade', 1.0)
            
            # Luminância → volume
            volume = L / 100.0
            
            # Matiz → frequência (mapeamento cromático-sonoro)
            import math
            angulo = math.atan2(b, a)  # -π a π
            freq = 220 * (2 ** (angulo / math.pi * 2))  # 220-880 Hz
            
            # Área → duração
            duracao = min(area / 100.0, 2.0)  # 0.1s a 2s
            
            # Excentricidade → timbre (0=sine, 1=sawtooth)
            timbre = min((excc - 1.0) / 3.0, 1.0)
            
            notas.append({
                'frequencia': round(freq, 1),
                'volume': round(volume, 2),
                'duracao': round(duracao, 2),
                'timbre': round(timbre, 2),
            })
        
        return {
            'sucesso': True,
            'dominio': self.nome,
            'notas': notas,
            'n_notas': len(notas),
            'descricao': f"{len(notas)} notas mapeadas de {len(regioes)} regiões",
        }


class TextoHandler(DominioHandler):
    """Handler para geração de texto descritivo."""
    
    nome = 'texto'
    descricao = 'Geração de descrição textual'
    
    def processar(self, ideia: Dict, contexto: Dict = None) -> Dict:
        desc = ideia.get('ideia', '')
        conceito_a = ideia.get('conceito_a', {}).get('tipo', '?')
        conceito_b = ideia.get('conceito_b', {}).get('tipo', '?')
        
        texto = (
            f"Conexão criativa entre {conceito_a} e {conceito_b}:\n\n"
            f"{desc}\n\n"
            f"Essa ideia explora a interseção entre domínios normalmente "
            f"desconectados, gerando possibilidades novas para o ecossistema."
        )
        
        return {
            'sucesso': True,
            'dominio': self.nome,
            'texto': texto,
        }


class EmergirCrossModal:
    """Engine de criatividade cross-modal.
    
    Despacha ideias para múltiplos domínios (visual, código, áudio, texto).
    Cada domínio processa a ideia de acordo com suas capacidades.
    """
    
    DOMINIOS_PADRAO = {
        'lua': LuaHandler,
        'visual': VisualHandler,
        'audio': AudioHandler,
        'texto': TextoHandler,
    }
    
    def __init__(self, llm_func: Callable = None, dominios: Dict[str, type] = None):
        """
        Args:
            llm_func: função LLM para geração de código (opcional)
            dominios: dict {nome: HandlerClass} (opcional, usa padrões)
        """
        dominios = dominios or self.DOMINIOS_PADRAO
        self.handlers = {}
        for nome, cls in dominios.items():
            if nome == 'lua':
                self.handlers[nome] = cls(llm_func=llm_func)
            else:
                self.handlers[nome] = cls()
    
    def despachar(self, ideia: Dict, dominios: List[str] = None,
                  contexto: Dict = None) -> Dict:
        """Despacha uma ideia para múltiplos domínios.
        
        Args:
            ideia: dict com 'ideia', 'conceito_a', 'conceito_b'
            dominios: lista de nomes de domínios (None = todos)
            contexto: dict com dados extras (regioes, paleta, etc.)
        
        Returns:
            dict {dominio_nome: resultado}
        """
        dominios = dominios or list(self.handlers.keys())
        resultados = {}
        
        for nome in dominios:
            handler = self.handlers.get(nome)
            if not handler:
                resultados[nome] = {'sucesso': False, 'erro': f'Domínio desconhecido: {nome}'}
                continue
            
            resultados[nome] = handler.processar(ideia, contexto)
        
        return resultados
    
    def listar_dominios(self) -> List[Dict]:
        """Lista domínios disponíveis."""
        return [
            {'nome': nome, 'descricao': handler.descricao}
            for nome, handler in self.handlers.items()
        ]
