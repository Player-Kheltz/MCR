using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using SevenZip.Compression.LZMA;

namespace MCR.Grimorio.Core.Services;

public class SpriteSheetService
{
    private readonly Dictionary<int, BitmapSource> _cache = new();
    private readonly List<BitmapSource> _sheets = new();
    private readonly List<string> _errors = new();
    private const int SheetSize = 384;
    private const int TileSize = 32;
    private const int TilesPerRow = SheetSize / TileSize;
    private const int SpritesPerSheet = TilesPerRow * TilesPerRow;
    private const int BytePerSheet = SheetSize * SheetSize * 4;

    public SpriteSheetService(string thingsDir)
    {
        if (!Directory.Exists(thingsDir))
        {
            Status = $"Dir não existe: {thingsDir}";
            return;
        }

        // Procura arquivos .bmp.lzma
        var files = Directory.GetFiles(thingsDir, "sprites-*.bmp.lzma")
            .OrderBy(f => f).Take(200).ToArray();

        if (files.Length == 0)
        {
            files = Directory.GetFiles(thingsDir, "*.spr")
                .OrderBy(f => f).Take(200).ToArray();
        }

        if (files.Length == 0)
        {
            Status = "Nenhum sprite encontrado em " + thingsDir;
            Debug.WriteLine("[SpriteSheet] Procurou em: " + thingsDir);
            GeneratePlaceholder();
            return;
        }

        int ok = 0, fail = 0;
        foreach (var file in files)
        {
            try
            {
                if (LoadSheet(file)) ok++;
                else fail++;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[SpriteSheet] {Path.GetFileName(file)}: {ex.Message}");
                fail++;
            }
        }

        if (_sheets.Count == 0)
        {
            GeneratePlaceholder();
            Status = $"{ok}/{ok+fail} sheets — placeholder";
        }
        else
        {
            Status = $"{_sheets.Count} sheets, ~{_sheets.Count * SpritesPerSheet} sprites";
        }
    }

    public string Status { get; private set; } = "Inicializando...";
    public bool HasSheets => _sheets.Count > 0;

    public BitmapSource? GetSprite(int id)
    {
        if (id <= 0 || !HasSheets) return null;
        if (_cache.TryGetValue(id, out var cached)) return cached;

        var idx = id - 1;
        var sheetIdx = idx / SpritesPerSheet;
        var localIdx = idx % SpritesPerSheet;

        if (sheetIdx >= _sheets.Count)
        {
            sheetIdx %= _sheets.Count;
            if (sheetIdx < 0) sheetIdx = 0;
        }

        var sheet = _sheets[sheetIdx];
        var tx = (localIdx % TilesPerRow) * TileSize;
        var ty = (localIdx / TilesPerRow) * TileSize;

        try
        {
            var cb = new CroppedBitmap(sheet, new Int32Rect(tx, ty, TileSize, TileSize));
            cb.Freeze();
            _cache[id] = cb;
            return cb;
        }
        catch { return null; }
    }

    public BitmapSource? GetSpriteScaled(int id, int size)
    {
        var src = GetSprite(id);
        if (src == null) return null;
        try
        {
            var scaled = new TransformedBitmap(src,
                new ScaleTransform((double)size / TileSize, (double)size / TileSize));
            scaled.Freeze();
            return scaled;
        }
        catch { return src; }
    }

    private void GeneratePlaceholder()
    {
        var pixels = new byte[BytePerSheet];
        for (int i = 0; i < pixels.Length; i += 4)
        {
            byte shade = (byte)(((i / 4) % SheetSize + (i / 4) / SheetSize) % 2 == 0 ? 80 : 40);
            pixels[i] = shade;
            pixels[i + 1] = shade;
            pixels[i + 2] = shade;
            pixels[i + 3] = 255;
        }
        var bs = BitmapSource.Create(SheetSize, SheetSize, 96, 96,
            PixelFormats.Bgra32, null, pixels, SheetSize * 4);
        bs.Freeze();
        _sheets.Add(bs);
    }

    private bool LoadSheet(string path)
    {
        var ext = Path.GetExtension(path).ToLower();

        if (ext == ".lzma" || path.Contains(".bmp.lzma"))
        {
            return LoadLzmaSheet(path);
        }

        // Fallback: tentar como .spr se tiver extensão .spr
        return LoadSprSheet(path);
    }

    private bool LoadLzmaSheet(string path)
    {
        var allBytes = File.ReadAllBytes(path);
        if (allBytes.Length < 32) return false;

        // CIP header: 32 bytes
        int p = 0;
        // Zeros de padding
        while (p < Math.Min(32, allBytes.Length) && allBytes[p] == 0) p++;

        // Check magic: 5 bytes [0x70, 0x0A, 0xFA, 0x80, 0x24]
        if (p + 5 > allBytes.Length) return false;
        if (allBytes[p] != 0x70 || allBytes[p + 1] != 0x0A ||
            allBytes[p + 2] != 0xFA || allBytes[p + 3] != 0x80 ||
            allBytes[p + 4] != 0x24) return false;
        p += 5;

        // LZMA file size (7-bit encoded integer)
        while (p < 32 && (allBytes[p] & 0x80) != 0) p++;
        if (p < 32) p++;
        while (p < 32) p++;

        // LZMA properties
        if (p + 13 > allBytes.Length) return false;
        byte lclppb = allBytes[p++];
        uint dictSize = BitConverter.ToUInt32(allBytes, p);
        p += 12; // dictSize(4) + cipCompressedSize(8)

        // Decompress with 7-Zip LZMA SDK
        var props = new byte[5];
        props[0] = lclppb;
        for (int i = 0; i < 4; i++)
            props[1 + i] = (byte)((dictSize >> (i * 8)) & 0xFF);

        var decoder = new Decoder();
        decoder.SetDecoderProperties(props);

        int compLen = allBytes.Length - p;
        using var inStm = new MemoryStream(allBytes, p, compLen);
        using var outStm = new MemoryStream();
        decoder.Code(inStm, outStm, compLen, BytePerSheet + 512, null);
        var decompressed = outStm.ToArray();

        if (decompressed.Length < 14) return false;

        // BMP header: pixel offset at byte 10
        uint bmpOff = BitConverter.ToUInt32(decompressed, 10);
        if (bmpOff + BytePerSheet > decompressed.Length)
        {
            // Pode ser que o BMP tenha tamanho diferente, tenta ler direto
            bmpOff = 0;
        }

        // Pixel data: BMP stores BGRA (Blue, Green, Red, Alpha)
        // WPF Bgra32 expects: B at byte 0, G at 1, R at 2, A at 3
        // BMP has B at byte 0, G at 1, R at 2, A at 3 — MATCH!
        var raw = new byte[BytePerSheet];
        int srcOff = (int)bmpOff;

        for (int y = 0; y < SheetSize; y++)
        {
            int srcRow = srcOff + y * SheetSize * 4;
            int dstRow = (SheetSize - 1 - y) * SheetSize * 4; // vertical flip

            for (int x = 0; x < SheetSize; x++)
            {
                int si = srcRow + x * 4;
                int di = dstRow + x * 4;

                byte b = decompressed[si];
                byte g = decompressed[si + 1];
                byte r = decompressed[si + 2];
                byte a = decompressed[si + 3];

                // Magenta key (#FF00FF → transparent)
                if (r == 0xFF && g == 0x00 && b == 0xFF)
                {
                    raw[di] = 0;
                    raw[di + 1] = 0;
                    raw[di + 2] = 0;
                    raw[di + 3] = 0;
                }
                else
                {
                    raw[di] = b;      // B
                    raw[di + 1] = g;  // G
                    raw[di + 2] = r;  // R
                    raw[di + 3] = a;  // A
                }
            }
        }

        var bs = BitmapSource.Create(SheetSize, SheetSize, 96, 96,
            PixelFormats.Bgra32, null, raw, SheetSize * 4);
        bs.Freeze();
        _sheets.Add(bs);
        return true;
    }

    private bool LoadSprSheet(string path)
    {
        // Legacy .spr format — placeholder
        return false;
    }
}
