"""Gera 11 amostras sinteticas para validacao do MCR.
0 dependencias alem da stdlib Python."""
import os, struct, random, wave, array, math

BASE = os.path.dirname(__file__)
SAMPLES_DIR = os.path.join(BASE, 'amostras')
os.makedirs(SAMPLES_DIR, exist_ok=True)

def gerar_wav(nome, frequencia_hz, amplitude=0.5, duracao_s=1.0, sample_rate=44100):
    """Gera um arquivo WAV mono."""
    path = os.path.join(SAMPLES_DIR, nome)
    n_amostras = int(sample_rate * duracao_s)
    if frequencia_hz == 0:
        # Silencio
        amostras = array.array('h', [0]) * n_amostras
    elif frequencia_hz < 0:
        # Ruido branco (-1 como sinal)
        amostras = array.array('h', [
            int(random.uniform(-32767, 32767) * amplitude)
            for _ in range(n_amostras)
        ])
    else:
        # Tom puro
        amostras = array.array('h', [
            int(32767 * amplitude * math.sin(2 * math.pi * frequencia_hz * t / sample_rate))
            for t in range(n_amostras)
        ])
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(amostras.tobytes())
    return path

def gerar_png(nome, largura, altura, funcao_pixel):
    """Gera um PNG simples (sem libs externas). Formato bruto + cabecalho minimo."""
    path = os.path.join(SAMPLES_DIR, nome)
    # Usamos PPM (formato imagem texto) em vez de PNG, pois e stdlib puro
    from io import BytesIO
    cabecalho = f"P6\n{largura} {altura}\n255\n".encode()
    pixels = bytearray()
    for y in range(altura):
        for x in range(largura):
            r, g, b = funcao_pixel(x, y)
            pixels.extend([r, g, b])
    with open(path, 'wb') as f:
        f.write(cabecalho + bytes(pixels))
    return path

def main():
    import math
    random.seed(42)
    print("Gerando amostras...")

    # WAVs
    gerar_wav('audio_silencio.wav', 0)
    print("  [WAV] audio_silencio.wav - silencio")
    gerar_wav('audio_tom_440hz.wav', 440)
    print("  [WAV] audio_tom_440hz.wav - tom puro 440Hz")
    gerar_wav('audio_barulho.wav', -1)
    print("  [WAV] audio_barulho.wav - ruido branco")

    # Imagens (PPM)
    gerar_png('imagem_branca.ppm', 100, 100, lambda x, y: (255, 255, 255))
    print("  [IMG] imagem_branca.ppm - totalmente branca")
    gerar_png('imagem_preto_branco.ppm', 100, 100,
              lambda x, y: (255, 255, 255) if (x + y) % 2 == 0 else (0, 0, 0))
    print("  [IMG] imagem_preto_branco.ppm - checkerboard")
    gerar_png('imagem_gradiente.ppm', 100, 100,
              lambda x, y: (int(255 * x / 100), int(255 * y / 100), 128))
    print("  [IMG] imagem_gradiente.ppm - gradiente")

    # Texto
    texto_lorem = (
        "MCR significa Modelo Cognitivo de Reconhecimento. "
        "E um sistema que aprende padroes em qualquer nivel de abstracao. "
        "Funciona com bytes, palavras, tokens, intencoes, decisoes e acoes. "
        "Tudo e transicao entre dois estados consecutivos. "
        "O que muda e o que entra como token. "
        "O mesmo codigo aprende bytes, palavras, intencoes e filosofias. "
        "A equacao MCR combina nivel de byte, palavra e token "
        "com uma penalidade que depende do tipo de ponte encontrada. "
        "Isso permite autoavaliacao sem depender de modelos externos. "
        "O sistema e auto-suficiente e nao requer GPU ou conexao com internet."
    )
    with open(os.path.join(SAMPLES_DIR, 'texto_lorem.txt'), 'w', encoding='utf-8') as f:
        f.write(texto_lorem)
    print("  [TXT] texto_lorem.txt - texto em portugues")

    with open(os.path.join(SAMPLES_DIR, 'texto_repetitivo.txt'), 'w') as f:
        f.write(' '.join(['a'] * 1000))
    print("  [TXT] texto_repetitivo.txt - 1000 repeticoes de 'a'")

    with open(os.path.join(SAMPLES_DIR, 'texto_curto.txt'), 'w') as f:
        f.write("SPA e SHC sao sistemas do MCR")
    print("  [TXT] texto_curto.txt - frase curta")

    # Binarios
    with open(os.path.join(SAMPLES_DIR, 'binario_zeros.bin'), 'wb') as f:
        f.write(bytes(1000))
    print("  [BIN] binario_zeros.bin - 1000 bytes 0x00")

    random.seed(42)
    with open(os.path.join(SAMPLES_DIR, 'binario_aleatorio.bin'), 'wb') as f:
        f.write(bytes([random.randint(0, 255) for _ in range(1000)]))
    print("  [BIN] binario_aleatorio.bin - 1000 bytes aleatorios")

    with open(os.path.join(SAMPLES_DIR, 'binario_padrao.bin'), 'wb') as f:
        f.write(bytes([0x00, 0xFF] * 500))
    print("  [BIN] binario_padrao.bin - 500x padrao 0x00 0xFF")

    # Lista
    print()
    print(f"Amostras geradas em: {SAMPLES_DIR}")
    for f in sorted(os.listdir(SAMPLES_DIR)):
        fp = os.path.join(SAMPLES_DIR, f)
        sz = os.path.getsize(fp)
        print(f"  {f:35s} {sz:>8d} bytes")

if __name__ == '__main__':
    main()
