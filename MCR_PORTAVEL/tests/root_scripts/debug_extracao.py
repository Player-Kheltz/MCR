"""Debug extraction."""
import lzma, io, pathlib, json, os
from PIL import Image

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

ASSETS_DIR = pathlib.Path(os.path.join(_BASE, 'tools', 'map-editor', 'Tibia', 'assets'))
MAGENTA = (255, 0, 255, 255)

# Load catalog
with open(ASSETS_DIR / 'catalog-content.json') as f:
    catalog = json.load(f)

# Find first sprite entry
for entry in catalog:
    if entry.get('type') != 'sprite': continue
    filepath = ASSETS_DIR / entry['file']
    print(f'Trying: {entry["file"]} ({filepath.stat().st_size} bytes)')
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    sig = bytes([0x70, 0x0A, 0xFA, 0x80, 0x24])
    idx = data.find(sig)
    if idx < 0:
        print('  No CIP signature')
        continue
    
    pos = idx + len(sig)
    sz = 0; shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        sz |= (b & 0x7F) << shift
        if (b & 0x80) == 0: break; shift += 7
    
    lzma_data = data[pos:pos+sz]
    print(f'  CIP at {idx}, LZMA size={sz}, available={len(lzma_data)}')
    
    # Method 1: props(5) + bogus(8) + stream(13+)
    props = lzma_data[:5]
    bogus = lzma_data[5:13]
    stream = lzma_data[13:]
    print(f'  Props: {props.hex()}, Bogus: {bogus.hex()}')
    
    hdr = props + bytes([0xFF]*8)
    try:
        dec = lzma.decompress(hdr + stream, format=lzma.FORMAT_ALONE)
        img = Image.open(io.BytesIO(dec))
        print(f'  Method 1 OK: {img.size[0]}x{img.size[1]}')
        
        # Count non-magenta sprites
        total = 0
        for r in range(12):
            for c in range(12):
                sp = img.crop((c*32, r*32, (c+1)*32, (r+1)*32))
                px = sp.load()
                nm = sum(1 for y in range(32) for x in range(32) if px[x,y] != MAGENTA)
                if nm > 10: total += 1
        print(f'  Non-empty sprites: {total}/144')
        
        # Save first sprite
        first = img.crop((0, 0, 32, 32))
        first.save(os.path.join(_BASE, 'poc_output', 'test_first_sprite.png'))
        print(f'  First sprite saved')
        break
        
    except Exception as e:
        print(f'  Method 1 FAIL: {e}')
        
        # Method 2: without bogus skip
        try:
            hdr2 = props + bytes([0xFF]*8)
            dec2 = lzma.decompress(hdr2 + lzma_data[5:], format=lzma.FORMAT_ALONE)
            img = Image.open(io.BytesIO(dec2))
            print(f'  Method 2 OK: {img.size}')
            break
        except Exception as e2:
            print(f'  Method 2 FAIL: {e2}')
