"""EncodingDetector — detecta encoding por extensão do arquivo.

Regras (PERSONALIDADE.md):
- .lua → ISO-8859-1 (Latin-1) — servidor exige Latin-1 para Lua
- .cpp, .hpp, .c, .h → UTF-8 com /utf-8 no MSVC
- .cs, .xaml, .sln → UTF-8 (C#, .NET)
- .go → UTF-8
- .md, .txt, .xml, .json, .yaml, .yml, .toml, .cfg → UTF-8
- default → UTF-8
"""
import os

ENCODING_MAP = {
    ".lua": "iso-8859-1",
    ".cpp": "utf-8",
    ".hpp": "utf-8",
    ".c": "utf-8",
    ".h": "utf-8",
    ".cs": "utf-8",
    ".xaml": "utf-8",
    ".sln": "utf-8",
    ".csproj": "utf-8",
    ".go": "utf-8",
    ".md": "utf-8",
    ".txt": "utf-8",
    ".xml": "utf-8",
    ".json": "utf-8",
    ".yaml": "utf-8",
    ".yml": "utf-8",
    ".toml": "utf-8",
    ".cfg": "utf-8",
    ".conf": "utf-8",
    ".ini": "utf-8",
    ".py": "utf-8",
    ".js": "utf-8",
    ".ts": "utf-8",
    ".css": "utf-8",
    ".html": "utf-8",
    ".sql": "utf-8",
    ".sh": "utf-8",
    ".bat": "utf-8",
    ".ps1": "utf-8",
    ".cmake": "utf-8",
}

def detectar_encoding(caminho: str, padrao: str = "utf-8") -> str:
    """Detecta encoding baseado na extensão do arquivo."""
    _, ext = os.path.splitext(caminho)
    return ENCODING_MAP.get(ext.lower(), padrao)


def tentar_ler(caminho: str, encoding: str = None) -> tuple[str, list[str]]:
    """Tenta ler arquivo com encoding específico.
    
    Retorna (encoding_usado, linhas).
    Se encoding for None, detecta automaticamente.
    Se falhar com encoding detectado, tenta fallback utf-8/latin-1.
    """
    if encoding is None:
        encoding = detectar_encoding(caminho)
    
    tentativas = [encoding]
    if encoding == "utf-8":
        tentativas.append("iso-8859-1")
    elif encoding == "iso-8859-1":
        tentativas.append("utf-8")
    else:
        tentativas.extend(["utf-8", "iso-8859-1"])
    
    for enc in tentativas:
        try:
            with open(caminho, 'r', encoding=enc) as f:
                linhas = f.readlines()
            return enc, linhas
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
        except Exception as e:
            return enc, [f"[EncodingDetector] Erro ao ler: {e}\n"]
    
    # Fallback: lê com errors='replace'
    with open(caminho, 'r', encoding="utf-8", errors='replace') as f:
        return "utf-8(replace)", f.readlines()


def escrever(caminho: str, conteudo: str):
    """Escreve arquivo com encoding correto."""
    encoding = detectar_encoding(caminho)
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    with open(caminho, 'w', encoding=encoding) as f:
        f.write(conteudo)
