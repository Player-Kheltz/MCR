"""Test streaming LZMA decompression."""
import lzma, io, os
from PIL import Image

import pathlib as _pl
_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
_first = sorted(_pl.Path(os.path.join(_BASE, 'tools', 'map-editor', 'Tibia', 'assets')).glob('sprites-*.bmp.lzma'))[0]
path = str(_first)

with open(path, 'rb') as f:
    data = f.read()

sig = bytes([0x70, 0x0A, 0xFA, 0x80, 0x24])
idx = data.find(sig)
pos = idx + len(sig)
sz = 0; shift = 0
while pos < len(data):
    b = data[pos]; pos += 1
    sz |= (b & 0x7F) << shift
    if (b & 0x80) == 0: break; shift += 7

lzma_data = data[pos:pos+sz]
props = lzma_data[:5]
stream = lzma_data[13:]
header = props + bytes([0xFF]*8)

# Method: LZMADecompressor (streaming, tolera falta de marcador)
try:
    decomp = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
    result = decomp.decompress(header + stream)
    img = Image.open(io.BytesIO(result))
    print(f'LZMADecompressor OK! {img.size[0]}x{img.size[1]}')
    
    # Count all non-magenta sprites
    MAGENTA = (255, 0, 255, 255)
    total = 0
    for r in range(12):
        for c in range(12):
            sp = img.crop((c*32, r*32, (c+1)*32, (r+1)*32))
            px = sp.load()
            nm = sum(1 for y in range(32) for x in range(32) if px[x,y] != MAGENTA)
            if nm > 10: total += 1
    print(f'Non-empty sprites: {total}/144')
    
except Exception as e:
    print(f'LZMADecompressor FAIL: {e}')
    
    # Try without bogus skip
    try:
        header2 = props + bytes([0xFF]*8)
        decomp2 = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        result2 = decomp2.decompress(header2 + lzma_data[5:])
        img2 = Image.open(io.BytesIO(result2))
        print(f'Without bogus skip OK! {img2.size}')
    except Exception as e2:
        print(f'Without bogus FAIL: {e2}')
