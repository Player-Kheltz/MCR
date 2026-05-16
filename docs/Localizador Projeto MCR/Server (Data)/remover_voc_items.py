import re
import sys

# Caminho do ficheiro items.xml (pode ser passado como argumento ou assumir o padrão)
file_path = sys.argv[1] if len(sys.argv) > 1 else "items.xml"
backup_path = file_path + ".bak"

# 1. Fazer backup
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)

# 2. Remover TODAS as linhas que contenham <attribute key="vocation" .../>
#    (mantém a indentação limpa, apagando a linha por completo)
content = re.sub(
    r'^[ \t]*<attribute key="vocation" value="[^"]*"[ \t]*/>[ \t]*\n',
    '',
    content,
    flags=re.MULTILINE
)

# 3. Gravar o ficheiro modificado
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Restrições de vocação removidas com sucesso!")
print("📁 Backup guardado em:", backup_path)