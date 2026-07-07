"""Analisa encoding no networkmessage.cpp usando MCR-DevIA com contexto real."""
import sys, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import _llm

# Le o codigo real
path = r'E:\Projeto MCR\Canary\src\server\network\message\networkmessage.cpp'
with open(path, 'r', encoding='utf-8') as f:
    codigo = f.read()

# Le tambem a funcao toLatin1
tools = r'E:\Projeto MCR\Canary\src\utils\tools.cpp'
with open(tools, 'r', encoding='utf-8') as f:
    tools_code = f.read()

# Encontra a funcao toLatin1 no tools
import re
match = re.search(r'std::string\s+toLatin1[\s\S]{0,500}', tools_code)
to_latin1_code = match.group(0) if match else ''

# Dados de uso real de toLatin1 no projeto
uso_real = [
    "player.cpp:2091 - client->sendTextMessage(TextMessage(MESSAGE_FAILURE, toLatin1(msg)))",
    "monster.cpp:45 - m_lowerName(asLowerCaseString(toLatin1(mType->name)))",
    "monster.cpp:104 - this->name = toLatin1(name)",
    "iologindata.cpp:278 - return toLatin1(result->getString(\"name\"))",
    "game.cpp:1028 - asLowerCaseString(toLatin1(creatureName))",
]

prompt = (
    "ANALISE DE ENCODING NO PROJETO MCR (Canary Server)\n\n"
    "Regras:\n"
    "- Strings C++: UTF-8 literal com /utf-8 no MSVC\n"
    "- Strings do protocolo DEVEM estar em Latin-1 (ISO-8859-1)\n"
    "- Deve-se usar toLatin1() na string ANTES de passar para msg.addString()\n\n"
    "OBSERVACOES DO CODIGO:\n"
    "1. A funcao NetworkMessage::addString() nao chama toLatin1() internamente.\n"
    "   Ela espera que a string ja esteja em Latin-1.\n"
    "2. toLatin1() e usado em 20+ lugares no codigo (nomes, mensagens).\n\n"
    "=== CODIGO: NetworkMessage::addString ===\n"
    + codigo[100:300] + '\n...\n'
    + '\n=== FUNCAO toLatin1() ===\n'
    + to_latin1_code[:500] + '\n\n'
    + "=== EXEMPLOS DE USO CORRETO ===\n"
    + '\n'.join(uso_real) + '\n\n'
    + "PERGUNTA: Com base na analise, o encoding do Canary esta correto?\n"
    + "Ha riscos de vazamento de UTF-8 no protocolo? "
    + "Os 20+ usos de toLatin1() sao suficientes ou faltam lugares?"
)

t0 = time.time()
resp = _llm.gerar(prompt, modelo='qwen2.5-coder:7b', temp=0.2)
t = time.time() - t0

print(f'Tempo: {t:.1f}s')
print(resp[:2000])
