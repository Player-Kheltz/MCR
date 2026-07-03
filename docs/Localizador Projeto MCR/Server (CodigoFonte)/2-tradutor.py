#!/usr/bin/env python3
import re
import sys
import time
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='en', target='pt')

def protect_placeholders(text):
    placeholders = []
    def repl(m):
        placeholders.append(m.group(0))
        # Usa «id» para não colar palavras (ex.: "{} logged in" → "«0» logged in")
        return f"«{len(placeholders)-1}»"
    # Protege \n, \t, %d, %s, { } etc.
    protected = re.sub(r'(\\[ntr]|%0?\d*[a-zA-Z]|\{[^\}]*\})', repl, text)
    return protected, placeholders

def restore_placeholders(text, placeholders):
    # Restaura «id» → placeholder original, sem mexer em espaços
    return re.sub(r'«(\d+)»', lambda m: placeholders[int(m.group(1))], text)

def translate_safe(original_text):
    clean_text = original_text.strip()
    if not clean_text:
        return original_text

    protected_text, placeholders = protect_placeholders(clean_text)

    for attempt in range(3):
        try:
            translated = translator.translate(protected_text)
            if translated:
                return restore_placeholders(translated, placeholders)
        except Exception:
            time.sleep(1.5 ** attempt)

    print(f"⚠️ Falha ao traduzir: '{original_text}'. Mantendo original.")
    return clean_text

def main():
    if len(sys.argv) < 3:
        print("Uso: python 2_tradutor.py extraido.txt traduzido.txt")
        return

    in_file, out_file = sys.argv[1], sys.argv[2]

    with open(in_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    total = sum(1 for line in lines if '=' in line and not line.startswith('['))
    count = 0

    print(f"🚀 Iniciando tradução de {total} strings...")

    for line in lines:
        linha_limpa = line.strip('\n')
        if not linha_limpa or linha_limpa.startswith('['):
            output_lines.append(linha_limpa + '\n')
            continue

        if '=' in linha_limpa:
            key, original_text = linha_limpa.split('=', 1)
            translated_text = translate_safe(original_text)
            output_lines.append(f"{key}={translated_text}\n")

            count += 1
            if count % 20 == 0:
                print(f"Progresso: {count}/{total}...")
            time.sleep(0.1)

    with open(out_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"✅ Tradução concluída: {out_file}")

if __name__ == '__main__':
    main()