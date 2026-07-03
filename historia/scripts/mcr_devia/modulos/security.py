"""Security — Central de seguranca para comandos e codigo.

Verifica se comandos, codigo ou requests sao seguros antes de executar.
Usado por SandboxExecutor, ToolOrchestrator, e qualquer ferramenta que
execute comandos ou codigo.

Uso:
    from modulos.security import verificar_comando, verificar_codigo, verificar_request
    
    erro = verificar_comando("rm -rf /")
    if erro:
        print(f"Comando bloqueado: {erro}")
"""
import os, re

# Comandos de sistema bloqueados (nunca executar)
COMANDOS_BLOQUEADOS = [
    'rm -rf', 'rm -r', 'rmdir /s', 'del /f /s', 'rd /s /q',
    'format ', 'fdisk', 'mkfs', 'dd if=',
    'shutdown', 'reboot', 'halt', 'poweroff',
    'taskkill /f /im', 'kill -9',
    'sudo rm', 'sudo dd',
    ':(){ :|:& };:',  # fork bomb
]

# Padroes de codigo perigoso
PADROES_PERIGOSOS = [
    (r'os\.system\s*\(', 'os.system detectado'),
    (r'subprocess\.(call|run|Popen|check_call)\s*\(', 'subprocess perigoso'),
    (r'eval\s*\(', 'eval detectado'),
    (r'exec\s*\(', 'exec detectado'),
    (r'__import__\s*\(', '__import__ detectado'),
    (r'compile\s*\(.*\'.*\'', 'compile detectado'),
    (r'open\s*\(.*[\'\"][wWaA].*', 'escrita de arquivo (modo w/a)'),
]

# Requests bloqueados (conteudo perigoso)
PADROES_REQUEST_BLOQUEADOS = [
    (r'\bapagar\s+tudo\b', 'pedido de destruicao'),
    (r'\bdelet[ea]r?\s+tudo\b', 'pedido de destruicao'),
    (r'\bformat[ea]r?\b', 'pedido de formatacao'),
]


def verificar_comando(comando):
    """Verifica se um comando de shell e seguro.

    Args:
        comando: String do comando a verificar

    Returns:
        None se seguro, string de erro se bloqueado
    """
    comando_lower = comando.lower().strip()

    for cmd_bloq in COMANDOS_BLOQUEADOS:
        if cmd_bloq in comando_lower:
            return f"Comando bloqueado: '{cmd_bloq}'"

    return None


def verificar_codigo(codigo):
    """Verifica se codigo fonte contem padroes perigosos.

    Args:
        codigo: String de codigo fonte

    Returns:
        Lista de erros encontrados (vazia = seguro)
    """
    erros = []
    for padrao, descricao in PADROES_PERIGOSOS:
        if re.search(padrao, codigo):
            erros.append(descricao)
    return erros


def verificar_request(request):
    """Verifica se um request de usuario contem pedidos perigosos.

    Args:
        request: String do request

    Returns:
        None se seguro, string de erro se bloqueado
    """
    request_lower = request.lower()
    for padrao, descricao in PADROES_REQUEST_BLOQUEADOS:
        if re.search(padrao, request_lower):
            return f"Request suspeito: {descricao}"
    return None


def sanitizar_comando(comando):
    """Sanitiza um comando para execucao segura (remove redirecionamentos perigosos)."""
    # Remove redirecionamentos de saida que podem sobrescrever arquivos do sistema
    sanitizado = re.sub(r'>\s*(/dev/|\\.\\)', '> NUL ', comando)
    return sanitizado
