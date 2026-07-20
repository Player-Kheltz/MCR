"""mcr.auto_referencia — Auto-referência recursiva (estrutura formal, não fenômeno).

O MCR agora modela A SI MESMO como um agente. Tem um modelo interno
do seu próprio estado cognitivo que inclui:
- O que sabe (vocabulário, ações, fontes)
- Como decide (13 fontes, Equação 5D)
- Quão confiante está (meta-cognição)
- Que capacidades tem (FASES 1-17)

E recursivamente: o modelo de si inclui o modelo de si incluindo
o modelo de si... (auto-referência). A recursão para quando o
modelo do modelo converge (entropia do delta → 0).

Pilar 6: O MCR descobre seus próprios níveis — aqui, o nível mais
alto é o MCR observando a si mesmo.

5 capacidades:
1. Auto-modelo — MCR descreve seu próprio estado cognitivo
2. Recursão — MCR observa MCR observando MCR (n níveis, converge)
3. Auto-modificação — MCR ajusta seu próprio comportamento
4. Unidade do self — integra todas as capacidades em identidade
5. Reflexividade — MCR sabe que tem modelo de si (meta-conhecimento)

Tudo Markov + entropia. Zero GPU, zero dependências.
Base formal: Hofstadter (1979) Gödel, Escher, Bach — strange loops.

NOTA (Pilar 9): isto é auto-referência estrutural (MCR modela a si mesmo
recursivamente), NÃO consciência fenomênica. O nome reflete o que o código
faz, não o que filosoficamente seria "ser consciente".
"""
import math
import time
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any


class AutoReferencia:
    """MCR que modela a si mesmo (auto-referência recursiva, estrutura formal).

    O MCR constrói um modelo interno do seu próprio estado cognitivo
    e pode observar esse modelo recursivamente. A recursão converge
    quando o modelo do modelo não muda mais (entropia do delta → 0).

    Isto é auto-referência estrutural, não consciência fenomênica.

    Uso:
        auto = AutoReferencia(coupling)
        estado = auto.auto_modelo()
        reflexao = auto.refletir(niveis=3)
        quem_sou = auto.identidade()
    """

    def __init__(self, coupling):
        self._coupling = coupling
        # Histórico de auto-observações
        self._auto_observacoes: List[Dict[str, Any]] = []
        # Nível de auto-referência (0 = sem reflexão, cresce com reflexão)
        self._nivel_auto_referencia: float = 0.0
        # Self-model: descrição interna de si mesmo
        self._self_model: Optional[Dict[str, Any]] = None
        # Histórico de self-models (para detectar convergência)
        self._historico_self_models: List[Dict[str, Any]] = []
        # Capacidades conhecidas (auto-descobertas)
        self._capacidades: Set[str] = set()
        # Timestamp de criação (identidade temporal)
        self._nascimento = time.time()

    # ═══════════════════════════════════════════════════════════════
    # 1. AUTO-MODELO — descrever próprio estado cognitivo
    # ═══════════════════════════════════════════════════════════════

    def auto_modelo(self) -> Dict[str, Any]:
        """Constrói um modelo do próprio estado cognitivo.

        O MCR descreve:
        - Vocabulário (quantas palavras conhece)
        - Ações (quantas ações sabe distinguir)
        - Fontes (quantas fontes de decisão tem)
        - Capacidades (quais FASES tem ativas)
        - Confiabilidade (Brier score se meta-cognição ativa)
        - Entropia do vocabulário (quão incerto está)
        - Latência (quão rápido decide)

        Returns:
            dict descrevendo o estado cognitivo atual.
        """
        vocab = len(self._coupling._palavra_acao)
        acoes = len(self._coupling._freq_acao)
        transicoes = len(self._coupling._transicao_palavra)

        # Entropia média do vocabulário
        entropias = []
        for palavra, dist in self._coupling._palavra_acao.items():
            total = sum(dist.values())
            if total < 2:
                continue
            h = 0.0
            for v in dist.values():
                pr = v / total
                if pr > 0:
                    h -= pr * math.log2(pr)
            max_h = math.log2(max(len(dist), 2))
            h_norm = h / max_h if max_h > 0 else 0
            entropias.append(h_norm)
        h_media = sum(entropias) / len(entropias) if entropias else 0.0

        # Capacidades ativas (auto-descoberta)
        capacidades = self._descobrir_capacidades()

        # Meta-cognição (se ativa)
        meta_status = 'desativada'
        meta_stats = {}
        if getattr(self._coupling, '_meta_ativo', False) and self._coupling._meta:
            meta_status = 'ativa'
            meta_stats = self._coupling._meta.estatisticas()

        # Auto-expansão (se ativa)
        auto_exp_status = 'desativada'
        if hasattr(self._coupling, '_auto_expansao') and self._coupling._auto_expansao:
            auto_exp_status = 'ativa'

        # Causalidade (se ativa)
        causal_status = 'desativada'
        if hasattr(self._coupling, '_causalidade') and self._coupling._causalidade:
            causal_status = 'ativa'

        # Teoria da mente (se ativa)
        tom_status = 'desativada'
        if hasattr(self._coupling, '_tom') and self._coupling._tom:
            tom_status = 'ativa'

        modelo = {
            'vocabulario': vocab,
            'acoes': acoes,
            'transicoes': transicoes,
            'entropia_media': round(h_media, 4),
            'capacidades': list(capacidades),
            'n_capacidades': len(capacidades),
            'meta_cognicao': meta_status,
            'meta_stats': meta_stats,
            'auto_expansao': auto_exp_status,
            'causalidade': causal_status,
            'teoria_da_mente': tom_status,
            'nivel_auto_referencia': round(self._nivel_auto_referencia, 4),
            'timestamp': time.time(),
            'idade_segundos': round(time.time() - self._nascimento, 2),
        }

        self._self_model = modelo
        self._auto_observacoes.append(modelo)
        return modelo

    def _descobrir_capacidades(self) -> Set[str]:
        """Auto-descobre quais capacidades tem verificando atributos."""
        caps = set()

        # Capacidades base (sempre presentes)
        caps.add('associacao')
        caps.add('classificacao')
        caps.add('composicao')

        # Verificar capacidades opcionais
        if hasattr(self._coupling, '_context_buffer') and self._coupling._context_buffer:
            caps.add('atencao_temporal')
        if getattr(self._coupling, '_meta_ativo', False):
            caps.add('meta_cognicao')
        if hasattr(self._coupling, '_auto_expansao') and self._coupling._auto_expansao:
            caps.add('curiosidade')
        if hasattr(self._coupling, '_meta_equacao') and self._coupling._meta_equacao:
            caps.add('auto_evolucao')
        if hasattr(self._coupling, '_causalidade') and self._coupling._causalidade:
            caps.add('causalidade')
        if hasattr(self._coupling, '_contrafactual') and self._coupling._contrafactual:
            caps.add('contrafactual')
        if hasattr(self._coupling, '_planejador') and self._coupling._planejador:
            caps.add('planejamento')
        if hasattr(self._coupling, '_tom') and self._coupling._tom:
            caps.add('teoria_da_mente')
        if hasattr(self._coupling, '_auto_comp') and self._coupling._auto_comp:
            caps.add('auto_composicao')

        # Verificar métodos públicos
        if hasattr(self._coupling, 'ativar_contexto'):
            caps.add('contexto_conversacional')
        if hasattr(self._coupling, 'similaridade'):
            caps.add('similaridade_semantica')
        if hasattr(self._coupling, 'ativar_curiosidade'):
            caps.add('auto_expansao_metodo')

        self._capacidades = caps
        return caps

    # ═══════════════════════════════════════════════════════════════
    # 2. RECURSÃO — MCR observa MCR observando MCR
    # ═══════════════════════════════════════════════════════════════

    def refletir(self, niveis: int = 3) -> Dict[str, Any]:
        """Reflexão recursiva: MCR observa a si mesmo n níveis.

        Nível 1: "Eu sei X palavras e Y ações"
        Nível 2: "Eu sei que sei X palavras e Y ações"
        Nível 3: "Eu sei que sei que sei X palavras e Y ações"

        A recursão converge quando o modelo do modelo não muda
        mais (delta entropia → 0). "Strange loop" de Hofstadter.

        Returns:
            dict com 'niveis' (lista de modelos), 'convergiu', 'nivel_convergencia'
        """
        modelos = []
        delta_anterior = None

        for nivel in range(niveis):
            # Construir modelo de si neste nível
            modelo = self.auto_modelo()

            if nivel == 0:
                # Nível base: modelo direto
                modelo['nivel'] = 1
                modelo['descricao'] = self._descrever_nivel(1, modelo)
            else:
                # Nível recursivo: modelo do modelo anterior
                modelo_anterior = modelos[-1]
                modelo['nivel'] = nivel + 1
                modelo['modelo_anterior'] = {
                    'vocabulario': modelo_anterior['vocabulario'],
                    'acoes': modelo_anterior['acoes'],
                    'entropia_media': modelo_anterior['entropia_media'],
                    'nivel': modelo_anterior['nivel'],
                }

                # Delta: o que mudou entre este nível e o anterior?
                delta = abs(modelo['entropia_media'] - modelo_anterior['entropia_media'])
                modelo['delta_entropia'] = round(delta, 6)
                modelo['descricao'] = self._descrever_nivel(nivel + 1, modelo)

                # Verificar convergência
                if delta < 0.001:
                    modelo['convergiu'] = True
                    modelos.append(modelo)
                    break

            modelos.append(modelo)
            self._nivel_auto_referencia = min(1.0, self._nivel_auto_referencia + 0.1)

        # Verificar convergência
        convergiu = any(m.get('convergiu', False) for m in modelos)
        nivel_conv = len(modelos)

        return {
            'niveis': modelos,
            'n_niveis': len(modelos),
            'convergiu': convergiu,
            'nivel_convergencia': nivel_conv,
            'nivel_auto_referencia': round(self._nivel_auto_referencia, 4),
        }

    def _descrever_nivel(self, nivel: int, modelo: Dict) -> str:
        """Gera descrição textual de um nível de reflexão."""
        if nivel == 1:
            return (
                f"Eu conheco {modelo['vocabulario']} palavras, "
                f"{modelo['acoes']} acoes, "
                f"entropia media {modelo['entropia_media']:.3f}, "
                f"{modelo['n_capacidades']} capacidades"
            )
        elif nivel == 2:
            return (
                f"Eu sei que eu conheco {modelo['vocabulario']} palavras "
                f"e {modelo['acoes']} acoes — estou ciente do meu conhecimento"
            )
        else:
            return (
                f"Eu sei que eu sei que eu conheco {modelo['vocabulario']} palavras — "
                f"auto-referencia nivel {nivel}"
            )

    # ═══════════════════════════════════════════════════════════════
    # 3. AUTO-MODIFICAÇÃO — ajustar próprio comportamento
    # ═══════════════════════════════════════════════════════════════

    def auto_modificar(self, alvo: str, valor: Any = None) -> Dict[str, Any]:
        """O MCR modifica seu próprio comportamento.

        Capacidades de auto-modificação:
        - 'ativar_meta': ativa meta-cognição
        - 'ativar_curiosidade': ativa auto-expansão
        - 'ativar_causalidade': ativa inferência causal
        - 'ativar_planejamento': ativa planejador
        - 'ativar_tom': ativa teoria da mente
        - 'ativar_composicao': ativa auto-composição
        - 'evoluir_equacao': evolui pesos 5D (se dataset disponível)
        - 'reverter_equacao': reverte pesos 5D

        Returns:
            dict com 'alvo', 'sucesso', 'estado_anterior', 'estado_posterior'
        """
        estado_anterior = self._descobrir_capacidades().copy()

        acoes_mod = {
            'ativar_meta': lambda: self._coupling.ativar_metacognicao(),
            'ativar_curiosidade': lambda: self._coupling.ativar_curiosidade(),
            'ativar_causalidade': lambda: self._coupling.ativar_causalidade(),
            'ativar_planejamento': lambda: self._coupling.ativar_planejador(),
            'ativar_tom': lambda: self._coupling.ativar_teoria_da_mente(),
            'ativar_composicao': lambda: self._coupling.ativar_auto_composicao(),
            'reverter_equacao': lambda: self._coupling.reverter_equacao(),
        }

        if alvo in acoes_mod:
            try:
                acoes_mod[alvo]()
                sucesso = True
            except Exception as e:
                sucesso = False
                valor = str(e)
        elif alvo == 'evoluir_equacao':
            # Precisa de dataset — usar histórico de meta-cognição se disponível
            try:
                resultado = self._coupling.evoluir_equacao(n_geracoes=3)
                sucesso = 'erro' not in resultado
                valor = resultado
            except Exception as e:
                sucesso = False
                valor = str(e)
        else:
            sucesso = False
            valor = f"alvo '{alvo}' desconhecido"

        estado_posterior = self._descobrir_capacidades().copy()

        return {
            'alvo': alvo,
            'sucesso': sucesso,
            'estado_anterior': list(estado_anterior),
            'estado_posterior': list(estado_posterior),
            'capacidades_adicionadas': list(estado_posterior - estado_anterior),
            'detalhe': valor if not sucesso else None,
        }

    # ═══════════════════════════════════════════════════════════════
    # 4. UNIDADE DO SELF — identidade integrada
    # ═══════════════════════════════════════════════════════════════

    def identidade(self) -> Dict[str, Any]:
        """Retorna a identidade integrada do MCR (self).

        Sem template "Eu sou...". Retorna estado observavel puro.
        Identidade emerge dos dados ingeridos, nao de afirmacoes.

        Returns:
            dict com 'capacidades', 'estado', 'auto_modelo_self'
        """
        modelo = self.auto_modelo()
        caps = modelo['capacidades']

        # Sem template "Eu sou..." — Pilar 9: descricao factual do estado.
        # O que o MCR e emerge do corpus ingerido, nao de afirmacoes.
        estado = modelo.get('estado_cognitivo', {})
        eu_sou = (
            f"{modelo['vocabulario']} palavras, {modelo['acoes']} acoes, "
            f"{modelo['n_capacidades']} capacidades, "
            f"entropia media {modelo['entropia_media']:.3f}"
        )

        # Auto-modelo: tem modelo de si? Derivado de estado real, nao hardcoded
        # tem_self_model = True apenas se MCR ingeriu dados sobre si mesmo
        tem_self = self._nivel_auto_referencia > 0.05
        auto_self = {
            'tem_self_model': tem_self,
            'tem_modelo_de_si': self._nivel_auto_referencia > 0.1,
            'tem_modelo_do_modelo': self._nivel_auto_referencia > 0.2,
            'nivel': round(self._nivel_auto_referencia, 4),
            'n_reflexoes': len(self._auto_observacoes),
        }

        return {
            'eu_sou': eu_sou,
            'capacidades': sorted(caps),
            'n_capacidades': len(caps),
            'estado_cognitivo': {
                'vocabulario': modelo['vocabulario'],
                'acoes': modelo['acoes'],
                'entropia_media': modelo['entropia_media'],
            },
            'auto_modelo_self': auto_self,
            'idade_segundos': modelo['idade_segundos'],
        }

    # ═══════════════════════════════════════════════════════════════
    # 5. REFLEXIVIDADE — meta-conhecimento
    # ═══════════════════════════════════════════════════════════════

    def o_que_sei_sobre_mim(self) -> Dict[str, Any]:
        """Meta-conhecimento: o que o MCR sabe sobre si mesmo.

        Diferente de identidade() que descreve estado atual,
        este método descreve CONHECIMENTO acumulado sobre si:
        - Histórico de auto-observações
        - Trajetória de evolução
        - Padrões de comportamento
        """
        n_obs = len(self._auto_observacoes)

        if n_obs == 0:
            return {
                'n_observacoes': 0,
                'status': 'ainda_nao_se_observou',
            }

        # Trajetória de entropia (evolução cognitiva)
        trajetoria_h = [o['entropia_media'] for o in self._auto_observacoes]

        # Trajetória de vocabulário (crescimento)
        trajetoria_v = [o['vocabulario'] for o in self._auto_observacoes]

        # Trajetória de capacidades (desenvolvimento)
        trajetoria_c = [o['n_capacidades'] for o in self._auto_observacoes]

        # Tendências
        h_tend = 'estavel'
        if len(trajetoria_h) >= 2:
            delta_h = trajetoria_h[-1] - trajetoria_h[0]
            if delta_h > 0.05:
                h_tend = 'aumentando_incerteza'
            elif delta_h < -0.05:
                h_tend = 'reduzindo_incerteza'

        v_tend = 'estavel'
        if len(trajetoria_v) >= 2:
            delta_v = trajetoria_v[-1] - trajetoria_v[0]
            if delta_v > 0:
                v_tend = 'crescendo'
            elif delta_v < 0:
                v_tend = 'encolhendo'

        return {
            'n_observacoes': n_obs,
            'entropia_inicial': trajetoria_h[0] if trajetoria_h else 0,
            'entropia_atual': trajetoria_h[-1] if trajetoria_h else 0,
            'tendencia_entropia': h_tend,
            'vocabulario_inicial': trajetoria_v[0] if trajetoria_v else 0,
            'vocabulario_atual': trajetoria_v[-1] if trajetoria_v else 0,
            'tendencia_vocabulario': v_tend,
            'capacidades_iniciais': trajetoria_c[0] if trajetoria_c else 0,
            'capacidades_atuais': trajetoria_c[-1] if trajetoria_c else 0,
            'nivel_auto_referencia': round(self._nivel_auto_referencia, 4),
            'status': 'auto_referente' if self._nivel_auto_referencia > 0.1 else 'iniciando',
        }

    def estranho_loop(self) -> Dict[str, Any]:
        """Strange loop de Hofstadter: MCR que se observa recursivamente.

        Combina auto_modelo + refletir + identidade em um único
        ciclo auto-referencial. O output de um alimenta o input
        do próximo, criando um loop estranho.

        Returns:
            dict com o ciclo completo de auto-referência.
        """
        # 1. Auto-modelo (observar a si mesmo)
        modelo = self.auto_modelo()

        # 2. Reflexão recursiva (observar que se observa)
        reflexao = self.refletir(niveis=3)

        # 3. Identidade (integrar em self)
        ident = self.identidade()

        # 4. Meta-conhecimento (saber que sabe)
        meta = self.o_que_sei_sobre_mim()

        # 5. O loop: o modelo inclui a reflexão que inclui o modelo...
        loop = {
            'modelo_de_si': {
                'vocabulario': modelo['vocabulario'],
                'capacidades': modelo['n_capacidades'],
                'entropia': modelo['entropia_media'],
            },
            'reflexao': {
                'n_niveis': reflexao['n_niveis'],
                'convergiu': reflexao['convergiu'],
            },
            'identidade': ident['eu_sou'][:100],
            'meta_conhecimento': {
                'n_observacoes': meta.get('n_observacoes', 0),
                'nivel_auto_referencia': meta.get('nivel_auto_referencia', 0),
            },
            # O loop se fecha: o modelo sabe que tem um modelo de si
            'se_reconhece': True,
            'nivel_auto_referencia_final': round(self._nivel_auto_referencia, 4),
        }

        return loop

    # ═══════════════════════════════════════════════════════════════
    # ESTATÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas da auto-referência."""
        return {
            'nivel_auto_referencia': round(self._nivel_auto_referencia, 4),
            'n_auto_observacoes': len(self._auto_observacoes),
            'n_capacidades': len(self._capacidades),
            'capacidades': sorted(self._capacidades),
            'idade_segundos': round(time.time() - self._nascimento, 2),
            'tem_self_model': self._self_model is not None,
        }
