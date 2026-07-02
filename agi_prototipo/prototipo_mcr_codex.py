#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 2: MCRCodex — Auto-Modificacao Real de Codigo
=====================================================
SelfModify apenas detectava. Codex SUBSTITUI, GERA e VALIDA.
Usa MCRGenerator para criar codigo novo. Bateria de testes como fitness.
"""
import os, sys, re, shutil, json, time, ast
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    CerebroAGI, MCRDecisorUniversal
)
from prototipo_mcr_config import C


class MCRCodex:
    """Auto-modificacao real: substitui parametros, gera codigo, evolui.
    
    Fluxo:
      1. escanear() — encontra hardcodes no codigo
      2. substituir() — troca valor fixo por chamada adaptativa
      3. gerar_codigo() — cria novas classes/funcoes para gaps
      4. evoluir() — loop completo: escaneia -> gera -> testa -> aplica
    """
    
    PARAMS_DETECTAVEIS = {
        "passos": int, "max_iter": int, "max_passos": int,
        "threshold": float, "conf_min": float, "dim": int,
        "limite": int, "max_candidatos": int, "dim_fp": int,
        "num_buckets": int, "fator_desconto": float, "epsilon": float,
        "max_ciclos": int, "max_episodios": int,
    }
    
    def __init__(self, cerebro: CerebroAGI = None):
        self.cerebro = cerebro or CerebroAGI()
        self.mk = MCR("codex")
        self.threshold = MCRThreshold("codex")
        self.historico: List[Dict] = []
        self.patch_dir = os.path.join(os.path.dirname(__file__), "..", "patches")
        os.makedirs(self.patch_dir, exist_ok=True)

    def escanear_arquivo(self, caminho: str = None) -> List[Dict]:
        """Escaneia arquivo em busca de parametros substituiveis."""
        if caminho is None:
            caminho = os.path.join(os.path.dirname(__file__), "prototipo_agi_completo.py")
        if not os.path.exists(caminho):
            return []
        try:
            with open(caminho, "r", encoding="utf-8", errors="replace") as f:
                linhas = f.readlines()
        except Exception:
            return []
        
        hardcodes = []
        for i, linha in enumerate(linhas):
            s = linha.strip()
            if not s or s.startswith("#") or s.startswith('"""') or s.startswith("'''"):
                continue
            # Detecta parametro = valor numerico
            for param_name in self.PARAMS_DETECTAVEIS:
                padrao = rf'\b{param_name}\s*=\s*(\d+\.?\d*)\b'
                m = re.search(padrao, s)
                if m:
                    valor = m.group(1)
                    hardcodes.append({
                        "linha": i + 1,
                        "parametro": param_name,
                        "valor_atual": valor,
                        "tipo": self.PARAMS_DETECTAVEIS[param_name].__name__,
                        "codigo": s[:80],
                        "arquivo": caminho,
                    })
                    break
        return hardcodes

    def substituir(self, arquivo: str, linha_num: int, param_nome: str,
                   novo_valor: str, fazer_backup: bool = True) -> bool:
        """Substitui um parametro em uma linha especifica."""
        if not os.path.exists(arquivo):
            return False
        
        if fazer_backup:
            backup = arquivo + ".bak"
            shutil.copy2(arquivo, backup)
            self.mk.aprender("BACKUP", backup)
        
        with open(arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        
        if linha_num < 1 or linha_num > len(linhas):
            return False
        
        linha = linhas[linha_num - 1]
        padrao = rf'({param_nome}\s*=\s*)\d+\.?\d*'
        nova_linha = re.sub(padrao, rf'\g<1>{novo_valor}', linha)
        
        if nova_linha == linha:
            return False
        
        linhas[linha_num - 1] = nova_linha
        with open(arquivo, "w", encoding="utf-8") as f:
            f.writelines(linhas)
        
        self.historico.append({
            "tipo": "substituicao",
            "arquivo": arquivo,
            "linha": linha_num,
            "parametro": param_nome,
            "antes": linha.strip()[:60],
            "depois": nova_linha.strip()[:60],
        })
        self.threshold.aprender(f"substituir:{param_nome}", 1.0)
        return True

    def gerar_classe(self, gap: Dict) -> str:
        """Gera codigo para uma nova classe que preenche um gap."""
        nome_classe = f"MCR{gap['nome'].title().replace('_', '')}"
        descricao = gap.get("descricao", "")
        
        template = f'''class {nome_classe}:
    """Gerado automaticamente pelo MCRCodex para: {descricao}"""
    def __init__(self, motor=None):
        self.mk = MCR("{nome_classe}")
        self.threshold = MCRThreshold("{nome_classe}")
    
    def executar(self, *args, **kwargs):
        resultado = self.mk.predizer(str(args[:2]))
        if resultado[0] and resultado[1] > 0.1:
            return resultado[0]
        return self._fallback(*args, **kwargs)
    
    def _fallback(self, *args, **kwargs):
        return None
    
    def aprender(self, entrada, saida):
        self.mk.aprender(str(entrada)[:C("historico_max") // 2], str(saida)[:C("historico_max") // 2])
    
    def stats(self) -> Dict:
        return {{
            "classe": "{nome_classe}",
            "gap": "{descricao}",
            "exemplos": self.mk.total,
        }}
'''
        return template

    def evoluir(self, arquivo_alvo: str = None, bateria_testes=None,
                max_iter: int = 10) -> Dict:
        """Ciclo evolutivo completo.
        
        1. Escaneia arquivo por hardcodes
        2. Para cada hardcode, gera variacoes
        3. Testa cada variacao com a bateria
        4. Aplica a melhor
        """
        if arquivo_alvo is None:
            arquivo_alvo = os.path.join(os.path.dirname(__file__), "prototipo_agi_completo.py")
        
        resultados = []
        for ciclo in range(max_iter):
            hardcodes = self.escanear_arquivo(arquivo_alvo)
            if not hardcodes:
                break
            
            melhor_score = -1
            melhor_substituicao = None
            
            for hc in hardcodes[:C("top_k")]:
                valor_atual = hc["valor_atual"]
                
                # Gera variacoes (80%, 100%, 120% do valor atual)
                try:
                    v = float(valor_atual)
                    for mult in [0.8, 0.9, 1.1, 1.2, 1.5, 2.0]:
                        novo = str(int(v * mult)) if hc["tipo"] == "int" else str(round(v * mult, 1))
                        if bateria_testes:
                            # Testa a variacao
                            self.substituir(arquivo_alvo, hc["linha"],
                                            hc["parametro"], novo, fazer_backup=True)
                            try:
                                score = bateria_testes() if callable(bateria_testes) else 0
                            except:
                                score = 0
                            # Reverte
                            self.reverter(arquivo_alvo)
                            
                            if score > melhor_score:
                                melhor_score = score
                                melhor_substituicao = (hc["linha"], hc["parametro"], novo)
                except ValueError:
                    continue
            
            # Aplica a melhor substituicao
            if melhor_substituicao and melhor_score > 0:
                linha, param, valor = melhor_substituicao
                self.substituir(arquivo_alvo, linha, param, valor)
                resultados.append({
                    "ciclo": ciclo,
                    "linha": linha,
                    "parametro": param,
                    "novo_valor": valor,
                    "score": round(melhor_score, 4),
                })
        
        return {
            "ciclos": len(resultados),
            "modificacoes": resultados,
            "arquivo": arquivo_alvo,
        }

    def reverter(self, arquivo: str) -> bool:
        """Restaura backup."""
        backup = arquivo + ".bak"
        if os.path.exists(backup):
            shutil.copy2(backup, arquivo)
            return True
        return False

    def stats(self) -> Dict:
        return {
            "parametros_conhecidos": len(self.PARAMS_DETECTAVEIS),
            "modificacoes": len(self.historico),
            "ultimas": self.historico[-C("janela_recente"):] if self.historico else [],
        }


class MCRSelfTest:
    """Auto-teste: valida que modificacoes nao quebram o sistema."""
    
    def __init__(self, caminho_base: str = None):
        self.caminho_base = caminho_base or os.path.dirname(os.path.abspath(__file__))
        self.mk = MCR("selftest")
    
    def testar_modulo(self, nome_modulo: str) -> float:
        """Testa um modulo especifico e retorna nota 0-10."""
        try:
            if nome_modulo == "world":
                from prototipo_agi_completo import MCRWorld, EstadoMundo, MotorFisica
                w = MCRWorld()
                e = EstadoMundo.criar_simples()
                e2 = MotorFisica.executar(e, "andar_dir")
                w.aprender(e, "andar_dir", e2)
                acao = w.predizer_acao(e, e2)
                return 10.0 if acao == "andar_dir" else 5.0
            
            elif nome_modulo == "coupling":
                from prototipo_agi_completo import MCRCoupling
                cp = MCRCoupling()
                for _ in range(C("top_k") + 2):
                    cp.alimentar_transicao("byte", "palavra", "B:41", "Fogo")
                cp.recalcular_pesos()
                return 10.0 if cp.peso("byte", "palavra") > 0 else 0.0
            
            elif nome_modulo == "planner":
                from prototipo_agi_completo import MCRPlanner, MCRWorld, EstadoMundo
                w = MCRWorld()
                p = MCRPlanner(w)
                e = EstadoMundo.criar_simples()
                plan = p.plano(e, e)
                return 10.0 if isinstance(plan, list) else 0.0
            
            return 5.0  # modulo desconhecido
        except Exception as e:
            return 0.0

    def detectar_regressao(self, antes: Dict, depois: Dict) -> bool:
        """True se houve regressao (nota caiu > 20%)."""
        for modulo in antes:
            if depois.get(modulo, 0) < antes.get(modulo, 0) * 0.8:
                return True
        return False
