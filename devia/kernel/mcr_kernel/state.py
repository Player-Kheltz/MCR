#!/usr/bin/env python3
"""state.py — Global state constants, data, boot, and auto-start.

Estado global mutável (_MCR_STATE, _MCR_DATA), bootstrap
e auto-start do sistema.
"""
import os


_MCR_STATE = {
    'versao': 5.0,
    'thresholds': {
        'revisor_eixo': [0.35, 0.4, 0.45, 0.38, 0.42],
        'revisor_entropia': [0.75, 0.8, 0.85, 0.78, 0.82],
        'ep_score': [0.25, 0.3, 0.35, 0.28, 0.32],
        'ep_taxa': [0.65, 0.7, 0.75, 0.68, 0.72],
        'kg_sim': [0.7, 0.75, 0.8, 0.72, 0.77],
        'util_sim': [0.7, 0.75, 0.8, 0.72, 0.77],
        'val_sim': [0.75, 0.8, 0.85, 0.78, 0.82],
        'reconstructor_ent': [0.12, 0.15, 0.18, 0.13, 0.16],
        'reconstructor_sim': [0.65, 0.7, 0.75, 0.68, 0.72],
    },
    'pesos': {
        'erro': 5.0, 'ctx': 4.0, 'causa': 3.0, 'solucao': 2.0,
    },
    'indice_modulos': {},
    'indice_comandos': {},
    'classes_essenciais': [
        'MCR', 'MCRFingerprint', 'MCRSystem', 'MCRConector',
        'MCRCadeia', 'MCRPergunta', 'MCRPeso', 'MCREntropia',
        'MCRRuido', 'MCRDecisor', 'MCRDiagnostico',
        'MCRBridge', 'MCRKGAuto', 'MCRExpansao', 'MCRMeta',
        'MCRPesoNota', 'MCRThreshold', 'MCRFuel', 'MCRMetaGap',
        'MCRMestreV2', 'MCRFilosofia', 'MCRFeedback', 'MCRMetaNivel',
        'MCRNivel', 'MCRDocIndex', 'MCRFragmento', 'MCRFragmentador',
        'MCRBufferKG', 'MCRAutoMelhoria',
    ]
}


_MCR_DATA = """
{"erro": "(empty)", "solucao": "Estado inicial - dados serao carregados pelo MCRPersistencia", "ctx": "init", "timestamp": 0}
"""


class MCRAutoStart:
    """Auto-start: MCR se auto-organiza quando o sistema inicia."""
    
    _cache_checksum = None
    _cache_path = None
    
    @classmethod
    def _calc_checksum(cls, kg):
        if not kg: return 0
        licoes = kg._get_licoes()
        ts = max(l.get('timestamp', 0) for l in licoes) if licoes else 0
        ctxs = '|'.join(sorted(set(l.get('ctx', '?') for l in licoes)))
        return hash((len(licoes), ts, ctxs)) % (10**12)
    
    @staticmethod
    def iniciar() -> dict:
        from .memory import _get_kg, MCRBridge
        try:
            kg = _get_kg()
            if not kg: return {'erro': 'KG indisponivel'}
            bridge = MCRBridge()
            bridge.descobrir()
            checksum = MCRAutoStart._calc_checksum(kg)
            if checksum == MCRAutoStart._cache_checksum:
                licoes = kg._get_licoes()
                uteis = [l for l in licoes 
                         if l.get('solucao','') and len(l.get('solucao','')) > 50
                         and not l.get('solucao','').startswith('{')
                         and not l.get('inactive')]
                return {
                    'aproveitamento': f"{len(uteis)/max(len(licoes),1)*100:.0f}%",
                    'uteis': len(uteis), 'total': len(licoes),
                    'cache': 'hit',
                }
            # Auto-organiza
            from .meta import MCRMetaNivel
            from .memory import MCRKGAuto
            from .decisor import MCRPesoNota, MCRThreshold
            from .evolution import MCRFuel
            from .persistence import MCRDocIndex
            acoes = []
            # 1. Fuel se necessario
            fuel = MCRFuel(kg, bridge)
            if fuel.abastecer_se_precisar():
                acoes.append("fuel")
            # 2. Dedup + limpeza
            auto = MCRKGAuto(kg)
            dedup = auto.dedup()
            if dedup > 0: acoes.append(f"dedup:{dedup}")
            limpeza = auto.limpar()
            if limpeza['removidos'] > 0: acoes.append(f"limpeza:{limpeza['removidos']}")
            # 3. Indexa docs
            try:
                doc_idx = MCRDocIndex()
                n = doc_idx.indexar()
                if n > 0: acoes.append(f"docs:{n}")
            except: pass
            # 4. MetaNivel
            meta_nivel = MCRMetaNivel()
            meta_nivel.alimentar(str(_MCR_STATE).encode())
            acoes.append(f"niveis:{meta_nivel.diagnosticar()['n_niveis']}")
            licoes = kg._get_licoes()
            uteis = [l for l in licoes 
                     if l.get('solucao','') and len(l.get('solucao','')) > 50
                     and not l.get('solucao','').startswith('{')
                     and not l.get('inactive')]
            MCRAutoStart._cache_checksum = checksum
            return {
                'aproveitamento': f"{len(uteis)/max(len(licoes),1)*100:.0f}%",
                'uteis': len(uteis), 'total': len(licoes),
                'acoes': acoes,
            }
        except Exception as e:
            return {'erro': str(e)[:100]}


class MCRBoot:
    """Boot auto-dirigido do MCR.py."""
    
    def __init__(self):
        self.mk = None
    
    def iniciar(self):
        """MCR decide o que fazer no boot."""
        try:
            from .engine import MCR
            self.mk = MCR("boot")
            # 1. Carrega estado
            from .persistence import MCRPersistencia
            pers = MCRPersistencia()
            dados = pers.carregar_dados()
            # 2. Auto-diagnostico
            from .decisor import MCRDecisor
            dec = MCRDecisor("boot_decision")
            estado_boot = f"dados:{len(dados.get('licoes',[]))}_ass:{len(dados.get('assinaturas',{}))}"
            acao = dec.decidir(estado_boot)
            # 3. Executa acao decidida
            resultado = {'status': 'ok', 'acao': acao, 'dados': len(dados.get('licoes', []))}
            if acao == 'auto_start' or 'fuel' in acao:
                print("[MCRBoot] Executando auto-start...")
                auto_res = MCRAutoStart.iniciar()
                resultado['auto_start'] = auto_res
            # 4. Verifica integridade
            from .meta import MCRSelfHeal
            heal = MCRSelfHeal.verificar()
            resultado['self_heal'] = heal
            self.mk.aprender("BOOT", f"acao:{acao}")
            return resultado
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'status': 'erro', 'erro': str(e)[:200]}


# Executa auto-verificacao no carregamento
_MCR_SELF_CHECK = None
try:
    from .meta import MCRSelfHeal
    _MCR_SELF_CHECK = MCRSelfHeal.verificar()
except:
    pass
