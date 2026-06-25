"""Ensinar o toquinho a dar dicas especificas"""
with open(r'E:\Projeto MCR\sandbox\mcr_autoconsciencia.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add more specific advice based on the type of problem
old = """        if len(falhas) >= 2:
            self.toques.append({
                'nivel': 'atencao',
                'mensagem': f'Atencao: {len(falhas)} reparos falharam consecutivamente. '
                           f'O ultimo foi em {falhas[-1].get("tipo","?")}. '
                           f'Motivo: {falhas[-1].get("motivo","desconhecido")}. '
                           f'Talvez o arquivo alvo tenha mudado de formato.',
                'sugestao': 'Tente verificar o formato atual do arquivo antes de tentar o reparo.',
            })"""

new = """        if len(falhas) >= 2:
            # Analisa o motivo da falha e da dica especifica
            ultima_falha = falhas[-1]
            motivo = ultima_falha.get('motivo', 'desconhecido')
            tipo = ultima_falha.get('tipo', '?')
            
            dicas = {
                'formato do arquivo diferente': f'O arquivo que contem o template de {tipo} pode ter mudado de formato. '
                                               f'Tente ler o arquivo primeiro para ver como ele esta estruturado agora, '
                                               f'antes de tentar editar.',
                'nao encontrou template': f'O template de {tipo} nao foi encontrado no formato esperado. '
                                        f'Pode ser que ele esteja em outro arquivo ou em outro formato '
                                        f'(f-string ao inves de string simples).',
                'desconhecido': f'O reparo de {tipo} falhou sem motivo registrado. '
                              f'Pode ser que a IA local nao tenha respondido, '
                              f'ou o reparo foi pulado silenciosamente.',
            }
            
            dica = dicas.get('desconhecido')
            for chave, texto in dicas.items():
                if chave in motivo.lower():
                    dica = texto
                    break
            
            self.toques.append({
                'nivel': 'atencao',
                'mensagem': f'Atencao: {len(falhas)} reparos falharam em {tipo}. Motivo: {motivo}.',
                'sugestao': dica,
            })"""

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_autoconsciencia.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'consciencia.py', 'exec')
    print('OK! Toquinho agora da DICAS ESPECIFICAS!')
except SyntaxError as e:
    print(f'Error: {e}')
