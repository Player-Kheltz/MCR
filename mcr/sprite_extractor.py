"""
mcr.sprite_extractor — Extrator universal de sprites do Tibia/Canary.
Le sprites das sheets .bmp.lzma, descomprime LZMA, corrige BGRA->RGBA,
e extrai sprites individuais por ID.

Baseado no codigo real do OTClient (spriteappearances.cpp)
e RME (sprite_appearances.cpp).
"""
import os, struct, lzma, json, pathlib
from typing import Optional, List

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

SPRITE_SHEET_SIZE = 384  # 384x384 pixels por sheet


class SpriteUniversal:
    def __init__(self, sprite_id: int, width: int, height: int,
                 pixels_rgba: bytes, offset_x: int = 0, offset_y: int = 0):
        self.id = sprite_id
        self.width = width
        self.height = height
        self.pixels = pixels_rgba
        self.offset_x = offset_x
        self.offset_y = offset_y


class SpriteExtractor:
    def __init__(self, things_dir: str = None):
        self.things_dir = pathlib.Path(
            things_dir or os.path.join(_ROOT, 'client', 'data', 'things', '1500'))
        self.catalog = self._load_catalog()
        self.sheets: dict = {}  # sheet_id -> pixels BGRA

    def _load_catalog(self) -> list:
        cp = self.things_dir / 'catalog-content.json'
        if cp.exists():
            with open(cp, 'r') as f:
                return json.load(f)
        return []

    def _find_sheet_entry(self, sprite_id: int) -> Optional[dict]:
        for entry in self.catalog:
            if entry.get('type') == 'sprite':
                first = entry.get('firstspriteid', 0)
                last = entry.get('lastspriteid', 0)
                if first <= sprite_id <= last:
                    return entry
        return None

    def _decompress_sheet(self, filepath: pathlib.Path) -> Optional[bytes]:
        """Le e descomprime .bmp.lzma.
        Formato CIP: [padding NULLs] [assinatura 70 0A FA 80 24]
        [tamanho LZMA 7-bit] [dados LZMA]
        """
        if not filepath.exists():
            return None

        with open(filepath, 'rb') as f:
            data = f.read()

        # Buscar assinatura CIP
        sig = bytes([0x70, 0x0A, 0xFA, 0x80, 0x24])
        idx = data.find(sig)
        if idx < 0:
            return None

        # Ler tamanho LZMA (7-bit encoded integer)
        pos = idx + len(sig)
        lzma_size = 0
        shift = 0
        while pos < len(data):
            byte = data[pos]
            pos += 1
            lzma_size |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7

        # LZMA: PROPS(5) + 8 bytes padding + STREAM → FORMAT_ALONE
        # Os 8 bytes após PROPS são ignorados (não são o uncompressed size real)
        # Usar 0xFF*8 (tamanho desconhecido) para o header FORMAT_ALONE
        props = data[pos:pos+5]
        stream = data[pos+13:pos + lzma_size]
        header = props + b'\xff' * 8 + stream
        try:
            decompressed = lzma.decompress(header, format=lzma.FORMAT_ALONE)
        except Exception:
            return None

        # Encontrar offset dos pixels no BMP
        # BMP header: 10 bytes -> pixel offset (4 bytes)
        pixel_offset = struct.unpack_from('<I', decompressed, 10)[0]

        # Extrair pixels (BGRA)
        expected = SPRITE_SHEET_SIZE * SPRITE_SHEET_SIZE * 4
        pixels_start = pixel_offset
        pixels_end = pixels_start + expected

        if pixels_end > len(decompressed):
            return None

        bgra_data = decompressed[pixels_start:pixels_end]

        # Swap BGR -> RGB + vertical flip (como no C# SpriteSheetService)
        result = bytearray(expected)
        row_bytes = SPRITE_SHEET_SIZE * 4
        for y in range(SPRITE_SHEET_SIZE):
            src_row = y * row_bytes
            dst_row = (SPRITE_SHEET_SIZE - 1 - y) * row_bytes  # vertical flip
            for x in range(SPRITE_SHEET_SIZE):
                si = src_row + x * 4
                di = dst_row + x * 4
                b, g, r, a = bgra_data[si:si+4]
                if r == 0xFF and g == 0x00 and b == 0xFF:
                    result[di] = 0
                    result[di+1] = 0
                    result[di+2] = 0
                    result[di+3] = 0
                else:
                    result[di] = r
                    result[di+1] = g
                    result[di+2] = b
                    result[di+3] = a

        return bytes(result)

    def _get_sheet_pixels(self, sprite_id: int) -> Optional[bytes]:
        """Retorna pixels RGBA da sheet que contem sprite_id."""
        entry = self._find_sheet_entry(sprite_id)
        if not entry:
            return None

        sheet_file = entry.get('file', '')
        sheet_path = self.things_dir / sheet_file

        if sheet_file not in self.sheets:
            self.sheets[sheet_file] = self._decompress_sheet(sheet_path)

        return self.sheets.get(sheet_file)

    def get_sprite(self, sprite_id: int,
                   width: int = 32, height: int = 32) -> Optional[SpriteUniversal]:
        """Extrai sprite individual da sheet.
        Baseado em RME sprite_appearances.cpp:361."""
        sheet_pixels = self._get_sheet_pixels(sprite_id)
        if not sheet_pixels:
            return None

        entry = self._find_sheet_entry(sprite_id)
        if not entry:
            return None

        first_id = entry.get('firstspriteid', 0)
        sprite_offset = sprite_id - first_id

        # Calcular posicao na sheet 384x384
        columns = SPRITE_SHEET_SIZE // width
        sprite_row = sprite_offset // columns
        sprite_col = sprite_offset % columns

        # Extrair pixels do sprite da sheet
        sprite_pixels = bytearray(width * height * 4)
        row_bytes = SPRITE_SHEET_SIZE * 4

        for y in range(height):
            src_y = sprite_row * height + y
            src_x_start = sprite_col * width * 4
            src_start = src_y * row_bytes + src_x_start
            src_end = src_start + width * 4
            dst_start = y * width * 4

            sprite_pixels[dst_start:dst_start + width * 4] = \
                sheet_pixels[src_start:src_end]

        return SpriteUniversal(
            sprite_id=sprite_id,
            width=width,
            height=height,
            pixels_rgba=bytes(sprite_pixels),
        )

    def list_sprites_by_type(self, spritetype: str = 'sprite',
                             limit: int = 10) -> List[int]:
        """Lista IDs de sprite disponiveis."""
        ids = []
        for entry in self.catalog:
            if entry.get('type') == spritetype:
                first = entry.get('firstspriteid', 0)
                last = entry.get('lastspriteid', 0)
                for sid in range(first, min(last + 1, first + limit)):
                    ids.append(sid)
                if len(ids) >= limit:
                    break
        return ids

    def stats(self) -> dict:
        sprite_entries = [e for e in self.catalog
                          if e.get('type') == 'sprite']
        total_sheets = len(sprite_entries)
        total_sprites = sum(
            e.get('lastspriteid', 0) - e.get('firstspriteid', 0) + 1
            for e in sprite_entries)
        return {
            'total_sheets': total_sheets,
            'total_sprites': total_sprites,
            'catalog_entries': len(self.catalog),
        }
