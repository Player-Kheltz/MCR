"""mcr.encoding — Leitura e escrita de arquivos com encoding correto por extensao.
Regra: .lua = ISO-8859-1 (Latin-1); .py, .cpp, .h, .xml, .md, .json = UTF-8."""
import sys
from pathlib import Path

# Cache de encoding por extensao (evita re-descobrir)
_ENCODING_MAP = {
    '.lua': 'latin-1',
    '.py':  'utf-8',
    '.cpp': 'utf-8',
    '.h':   'utf-8',
    '.hpp': 'utf-8',
    '.cs':  'utf-8',
    '.go':  'utf-8',
    '.xml': 'utf-8',
    '.md':  'utf-8',
    '.json':'utf-8',
    '.txt': 'utf-8',
    '.yaml':'utf-8',
    '.yml': 'utf-8',
    '.cfg': 'utf-8',
    '.conf':'utf-8',
    '.sql': 'utf-8',
    '.css': 'utf-8',
    '.html':'utf-8',
    '.sh':  'utf-8',
    '.bat': 'utf-8',
    '.ps1': 'utf-8',
}


def _encoding_para(extensao: str) -> str:
    """Retorna o encoding apropriado para uma extensao de arquivo."""
    return _ENCODING_MAP.get(extensao.lower(), 'utf-8')


def _reparar_latin1(conteudo: str) -> str:
    """Tenta reparar string Latin-1 mal decodificada como UTF-8.
    
    Ex: 'Jo\\xe3o' (Latin-1 bruto) -> 'Jo\\xe3o' (ja esta correto).
    Se o texto foi acidentalmente decodificado como UTF-8 a partir de bytes Latin-1,
    pode gerar caracteres como '\\xe3\\x80\\x93' — este metodo tenta reverter.
    """
    try:
        # Re-codifica como Latin-1 e re-decodifica como UTF-8
        return conteudo.encode('latin-1', errors='replace').decode('utf-8', errors='replace')
    except Exception:
        return conteudo


def read_file(path, reparar_latin1=False):
    """Le um arquivo com o encoding correto baseado na extensao.
    
    Args:
        path: caminho (str ou Path) para o arquivo.
        reparar_latin1: se True e o arquivo for .lua, tenta reparar
                       caracteres mal decodificados.
    
    Returns:
        Conteudo do arquivo como string.
    
    Raises:
        FileNotFoundError: se o arquivo nao existir.
        IOError: se falhar na leitura mesmo apos fallback.
    """
    path = Path(path)
    ext = path.suffix
    encoding = _encoding_para(ext)
    
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    
    # Tentativa 1: encoding esperado
    try:
        with open(path, 'r', encoding=encoding, errors='strict') as f:
            conteudo = f.read()
        if reparar_latin1 and encoding == 'latin-1':
            conteudo = _reparar_latin1(conteudo)
        return conteudo
    except (UnicodeDecodeError, UnicodeError):
        # Fallback 1: tenta UTF-8 (para .lua que pode estar em UTF-8)
        if encoding == 'latin-1':
            try:
                with open(path, 'r', encoding='utf-8', errors='strict') as f:
                    conteudo = f.read()
                print(f"[encoding] Aviso: {path} lido como UTF-8 em vez de Latin-1")
                return conteudo
            except (UnicodeDecodeError, UnicodeError):
                pass
        
        # Fallback 2: tenta utf-8 com substituicao (qualquer coisa)
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read()
            print(f"[encoding] Aviso: {path} lido com utf-8 errors=replace")
            return conteudo
        except Exception as e:
            raise IOError(f"Nao foi possivel ler {path}: {e}")


def write_file(path, content, language=None):
    """Escreve um arquivo com o encoding correto baseado na extensao.
    
    Args:
        path: caminho (str ou Path) para o arquivo.
        content: string com o conteudo a escrever.
        language: forca um encoding especifico ('lua', 'python', etc.).
                 Se None, detecta pela extensao.
    
    Raises:
        IOError: se falhar na escrita.
    """
    path = Path(path)
    
    if language:
        ext_map = {'lua': 'latin-1', 'python': 'utf-8', 'cpp': 'utf-8', 'csharp': 'utf-8'}
        encoding = ext_map.get(language.lower(), 'utf-8')
    else:
        encoding = _encoding_para(path.suffix)
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
    except UnicodeEncodeError:
        with open(path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Nao foi possivel escrever {path}: {e}")


def read_lines(path):
    """Le um arquivo e retorna uma lista de linhas."""
    conteudo = read_file(path)
    return conteudo.splitlines()


def write_lines(path, lines, language=None):
    """Escreve uma lista de linhas em um arquivo."""
    conteudo = '\n'.join(lines)
    write_file(path, conteudo, language=language)
