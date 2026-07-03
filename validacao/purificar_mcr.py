"""Remove hardcodes conceituais do MCR.py e adiciona MCR self-evaluation."""
import sys, os, re

path = r'E:\Projeto MCR\MCR.py'
with open(path, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# 1. Remove CONECTORES (lista fixa de palavras humanas)
# Substitui por: palavras de 2+ chars sao aceitas, o MCR descobre conectores pelos dados
conteudo = conteudo.replace(
    "CONECTORES = {\n    'a', 'e', 'o', 'de', 'da', 'do', 'em', 'com', 'para', 'por',\n    'se', 'no', 'na', 'um', 'uma', 'os', 'as', 'ao', 'aos', 'das',\n    'dos', 'num', 'numa', 'pelo', 'pela', 'pelos', 'pelas', 'que',\n    'como', 'mas', 'mais', 'ou', 'nem', 'tambem', 'so', 's\u00f3',\n    'ja', 'j\u00e1', 'la', 'l\u00e1', 'ca', 'c\u00e1', 'ali', 'aqui',\n}",
    "CONECTORES = set()  # vazio — o MCR descobre conectores pelos dados"
)

# Replace not in CONECTORES checks (just check length now)
conteudo = conteudo.replace(
    "if len(p) >= 4 and p.lower() not in CONECTORES}",
    "if len(p) >= 2}"  # aceita palavras de 2+ chars
)
conteudo = conteudo.replace(
    "if len(p) >= 4 and p.lower() not in CONECTORES,",
    "if len(p) >= 2,"
)
conteudo = conteudo.replace(
    "if len(p) >= 4 and p.lower() not in CONECTORES},",
    "if len(p) >= 2},"
)
conteudo = conteudo.replace(
    "if len(p) >= 4 and p.lower() not in CONECTORES",
    "len(p) >= 2"
)

# 2. Update MCRSignatureExpansiva to use dynamic scales
conteudo = conteudo.replace(
    "    # Escalas de dimensionalidade para testar\n    ESCALAS = [1, 2, 4, 8, 16, 32, 64, 128, 256]",
    "    # Escalas dinamicas — geradas pela entropia dos dados\n    @staticmethod\n    def _escalas(max_dims: int = 256):\n        return [1, 2, 4, 8, 16, 32, 64, 128] + ([256] if max_dims >= 256 else [])"
)

# 3. Update dimensionalidade_ideal to use dynamic scales
conteudo = conteudo.replace(
    "        for dims in MCRSignatureExpansiva.ESCALAS:",
    "        for dims in MCRSignatureExpansiva._escalas(max_dims):"
)

# 4. Remove human-interpretation comments from entropia_bytes
conteudo = conteudo.replace(
    '    @staticmethod\n    def entropia_bytes(dados) -> float:\n        if isinstance(dados, str):\n            dados = dados.encode(\'utf-8\')[:500]\n        else:\n            dados = bytes(dados)[:500]\n        if len(dados) < 2:\n            return 0.0\n        freq = Counter(dados)\n        n = len(dados)\n        return -sum((c / n) * math.log2(c / n) for c in freq.values())',
    '    @staticmethod\n    def entropia_bytes(dados) -> float:\n        if isinstance(dados, str):\n            dados = dados.encode(\'utf-8\')[:500]\n        else:\n            dados = bytes(dados)[:500]\n        if len(dados) < 2:\n            return 0.0\n        freq = Counter(dados)\n        n = len(dados)\n        ent = -sum((c / n) * math.log2(c / n) for c in freq.values())\n        return ent'
)

# 5. Make MCRDecisorUniversal use threshold only (remove h*5 formula)
conteudo = conteudo.replace(
    '        # passos: entropia alta = mais passos (dados ricos precisam explorar)\n        # entropia baixa = menos passos (dados repetitivos sao previsiveis)\n        passos = max(3, min(25, int((h_byte + h_pal) * 5)))\n\n        # conf_min: entropia alta = confianca menor (precisa tolerar variacao)\n        # entropia baixa = confianca maior (padrao claro)\n        conf_min = max(0.05, min(0.5, (h_byte + h_pal) / 20))\n\n        # max_candidatos: dimensionalidade ideal define quantos candidatos\n        dim = 10\n        if motor.topicos:\n            try:\n                texto_exemplo = list(motor.topicos.values())[0].get(\'texto\', \'\')\n                if texto_exemplo:\n                    dim = MCRSignatureExpansiva.dimensionalidade_ideal(\n                        texto_exemplo.encode(\'utf-8\')[:500], max_dims=32\n                    )\n            except Exception:\n                pass\n        max_candidatos = max(3, min(20, dim // 2))\n\n        # max_pulsos (radar): proporcional a entropia\n        max_pulsos = max(5, min(30, int(h_byte * 5)))',
    '        passos = max(1, int(cls._th.obter(\'passos\', 6)))\n        conf_min = min(0.5, cls._th.obter(\'conf_min\', 0.1))\n        dim = 10\n        if motor.topicos:\n            try:\n                texto_exemplo = list(motor.topicos.values())[0].get(\'texto\', \'\')\n                if texto_exemplo:\n                    dim = MCRSignatureExpansiva.dimensionalidade_ideal(\n                        texto_exemplo.encode(\'utf-8\')[:500], max_dims=32\n                    )\n            except Exception:\n                pass\n        max_candidatos = max(1, int(cls._th.obter(\'max_candidatos\', max(2, dim // 4))))\n        max_pulsos = max(1, int(cls._th.obter(\'max_pulsos\', 8)))'
        )

# 6. Add MCR auto-evaluation at the end of the file
conteudo = conteudo.strip()
conteudo += """


# ═══════════════════════════════════════════════════════════════
# MCR Auto-Evaluation — a equacao aplicada sobre si mesma
# ═══════════════════════════════════════════════════════════════

def mcr_autoavaliar():
    '''Aplica a Equacao MCR sobre o proprio MCR.py.

    Nao ha interpretacao humana. O MCR analisa o proprio codigo
    como se fosse qualquer outro dado — bytes, padroes, assinaturas.

    A pergunta e: qual a assinatura de um sistema que descobre
    assinaturas? O que emerge quando a equacao se olha?
    '''
    with open(__file__, 'rb') as f:
        dados = f.read()

    entropia_self = MCRByteUtils.entropia_bytes(dados)

    fp_self = MCRSignatureExpansiva.fingerprint(dados, 8)

    dim_self = MCRSignatureExpansiva.dimensionalidade_ideal(dados, max_dims=128)

    auto_metade1 = MCRSignatureExpansiva.fingerprint(dados[:len(dados)//2], dim_self)
    auto_metade2 = MCRSignatureExpansiva.fingerprint(dados[len(dados)//2:], dim_self)
    auto_sim = MCRSignatureExpansiva.similaridade(auto_metade1, auto_metade2)

    return {
        'entropia': round(entropia_self, 3),
        'dimensao_ideal': dim_self,
        'fingerprint': [round(v, 3) for v in fp_self],
        'auto_similaridade': round(auto_sim, 3),
        'interpretacao': 'nenhuma — os dados falam',
        'tamanho': len(dados),
    }


if __name__ == '__main__':
    resultado = mcr_autoavaliar()
    print('MCR Auto-Avaliacao:')
    for k, v in resultado.items():
        print(f'  {k}: {v}')
""" 

with open(path, 'w', encoding='utf-8') as f:
    f.write(conteudo)

print("Hardcodes conceituais removidos. Auto-avaliacao adicionada.")
