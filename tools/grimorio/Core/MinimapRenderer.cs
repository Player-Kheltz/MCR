using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using MCR.Grimorio.Data;
using MCR.Grimorio.Models;

namespace MCR.Grimorio.Core;

public class MinimapRenderer
{
    private static readonly Color[] _palette;

    private OtbmMapData? _mapData;
    private WriteableBitmap? _cached;
    private int _cachedZoom = -1;
    private int _cachedFloor = -1;
    private bool _cachedGrid;

    static MinimapRenderer()
    {
        _palette = GeneratePalette();
    }

    public WriteableBitmap? Render(OtbmMapData map, int floor, int zoom, bool gridLines)
    {
        if (map == null) return null;
        if (map == _mapData && zoom == _cachedZoom && floor == _cachedFloor && gridLines == _cachedGrid)
            return _cached;

        if (!map.Floors.TryGetValue(floor, out var tiles) || tiles.Count == 0)
            return CreateEmpty(map.Width, map.Height, zoom);

        var pixelSize = Math.Max(1, zoom);
        var w = map.Width * pixelSize;
        var h = map.Height * pixelSize;

        var bmp = new WriteableBitmap(w, h, 96, 96, PixelFormats.Bgra32, null);

        bmp.Lock();
        unsafe
        {
            var buf = (byte*)bmp.BackBuffer;
            var stride = bmp.BackBufferStride;

            var lookup = new Dictionary<(int x, int y), TileData>();
            foreach (var t in tiles)
                lookup[(t.X, t.Y)] = t;

            for (var ty = 0; ty < map.Height; ty++)
            {
                for (var tx = 0; tx < map.Width; tx++)
                {
                    var color = GetTileColor(lookup, tx, ty, map);

                    for (var py = 0; py < pixelSize; py++)
                    for (var px = 0; px < pixelSize; px++)
                    {
                        var dx = tx * pixelSize + px;
                        var dy = ty * pixelSize + py;

                        if (gridLines && pixelSize >= 6 && (px == pixelSize - 1 || py == pixelSize - 1))
                        {
                            var o = dy * stride + dx * 4;
                            buf[o + 0] = 60;
                            buf[o + 1] = 60;
                            buf[o + 2] = 60;
                            buf[o + 3] = 255;
                        }
                        else
                        {
                            var o = dy * stride + dx * 4;
                            buf[o + 0] = color.B;
                            buf[o + 1] = color.G;
                            buf[o + 2] = color.R;
                            buf[o + 3] = 255;
                        }
                    }
                }
            }
        }
        bmp.AddDirtyRect(new Int32Rect(0, 0, w, h));
        bmp.Unlock();

        _mapData = map;
        _cachedZoom = zoom;
        _cachedFloor = floor;
        _cachedGrid = gridLines;
        _cached = bmp;

        return bmp;
    }

    public void DrawPlayers(WriteableBitmap bmp, OtbmMapData map, int floor, int zoom, List<PlayerPosition> players)
    {
        if (bmp == null || map == null || players == null || players.Count == 0) return;
        var pixelSize = Math.Max(1, zoom);
        var halfSize = Math.Max(3, pixelSize);

        bmp.Lock();
        unsafe
        {
            var buf = (byte*)bmp.BackBuffer;
            var stride = bmp.BackBufferStride;
            var bmpW = bmp.PixelWidth;
            var bmpH = bmp.PixelHeight;

            foreach (var p in players)
            {
                if (p.Z != floor) continue;

                var cx = p.X * pixelSize;
                var cy = p.Y * pixelSize;

                var r = halfSize;
                for (var dy = -r; dy <= r; dy++)
                for (var dx = -r; dx <= r; dx++)
                {
                    if (dx * dx + dy * dy > r * r) continue;
                    var px = cx + dx;
                    var py = cy + dy;
                    if (px < 0 || px >= bmp.PixelWidth || py < 0 || py >= bmp.PixelHeight) continue;

                    var o = py * stride + px * 4;
                    buf[o + 0] = 80;
                    buf[o + 1] = 200;
                    buf[o + 2] = 255;
                    buf[o + 3] = 255;
                }
            }
        }
        bmp.AddDirtyRect(new Int32Rect(0, 0, bmp.PixelWidth, bmp.PixelHeight));
        bmp.Unlock();
    }

    public void DrawEntropyGrid(WriteableBitmap bmp, OtbmMapData map, int floor, int zoom,
                                 List<EntropyPoint> grid, double entMin, double entMax)
    {
        if (bmp == null || map == null || grid == null || grid.Count == 0) return;
        var pixelSize = Math.Max(1, zoom);
        var range = Math.Max(entMax - entMin, 0.01);
        var tileSize = Math.Max(4, pixelSize);

        bmp.Lock();
        unsafe
        {
            var buf = (byte*)bmp.BackBuffer;
            var stride = bmp.BackBufferStride;
            var bmpW = bmp.PixelWidth;
            var bmpH = bmp.PixelHeight;

            foreach (var pt in grid)
            {
                if (pt.Z != floor) continue;

                var cx = pt.X * pixelSize;
                var cy = pt.Y * pixelSize;

                // Normaliza entropia para [0, 1] usando min/max da resposta
                var norm = (pt.Entropy - entMin) / range;
                norm = Math.Clamp(norm, 0.0, 1.0);

                // Interpola: 0.0 = Blue, 0.5 = Yellow, 1.0 = Red
                byte r, g, b;
                if (norm < 0.5)
                {
                    var t = norm / 0.5;
                    r = (byte)(t * 255);
                    g = (byte)(t * 255);
                    b = (byte)((1.0 - t) * 255);
                }
                else
                {
                    var t = (norm - 0.5) / 0.5;
                    r = 255;
                    g = (byte)((1.0 - t) * 255);
                    b = 0;
                }

                for (var dy = 0; dy < tileSize; dy++)
                for (var dx = 0; dx < tileSize; dx++)
                {
                    var px = cx + dx;
                    var py = cy + dy;
                    if (px < 0 || px >= bmpW || py < 0 || py >= bmpH) continue;

                    var o = py * stride + px * 4;
                    // Semi-transparent overlay
                    buf[o + 0] = (byte)(buf[o + 0] * 0.5 + b * 0.5);
                    buf[o + 1] = (byte)(buf[o + 1] * 0.5 + g * 0.5);
                    buf[o + 2] = (byte)(buf[o + 2] * 0.5 + r * 0.5);
                    buf[o + 3] = 255;
                }
            }
        }
        bmp.AddDirtyRect(new Int32Rect(0, 0, bmp.PixelWidth, bmp.PixelHeight));
        bmp.Unlock();
    }

    public void InvalidateCache()
    {
        _cached = null;
        _mapData = null;
        _cachedZoom = -1;
    }

    private static unsafe WriteableBitmap CreateEmpty(int w, int h, int zoom)
    {
        var pz = Math.Max(1, zoom);
        var bmp = new WriteableBitmap(w * pz, h * pz, 96, 96, PixelFormats.Bgra32, null);

        bmp.Lock();
        var buf = (byte*)bmp.BackBuffer;
        var stride = bmp.BackBufferStride;
        var totalH = bmp.PixelHeight;

        for (var y = 0; y < totalH; y++)
        for (var x = 0; x < w * pz; x++)
        {
            var o = y * stride + x * 4;
            buf[o + 0] = 30;
            buf[o + 1] = 30;
            buf[o + 2] = 30;
            buf[o + 3] = 255;
        }

        bmp.AddDirtyRect(new Int32Rect(0, 0, w * pz, totalH));
        bmp.Unlock();
        return bmp;
    }

    private static Color GetTileColor(Dictionary<(int x, int y), TileData> lookup, int tx, int ty, OtbmMapData map)
    {
        if (!lookup.TryGetValue((tx, ty), out var tile))
            return Color.FromRgb(30, 30, 30);

        if (tile.MinimapColor > 0 && tile.MinimapColor < 256)
        {
            var c = _palette[tile.MinimapColor];
            if (tile.Type == TileType.ProtectZone)
                return Blend(c, Color.FromRgb(100, 255, 100), 0.3f);
            if (!tile.IsWalkable)
                return Darken(c, 0.5f);
            return c;
        }

        return tile.Type switch
        {
            TileType.Ground => tile.IsWalkable
                ? Color.FromRgb(90, 140, 60)
                : Color.FromRgb(60, 90, 40),
            TileType.Water => Color.FromRgb(40, 90, 160),
            TileType.Wall => Color.FromRgb(60, 60, 60),
            TileType.ProtectZone => Color.FromRgb(80, 180, 80),
            TileType.Walkable => Color.FromRgb(100, 150, 70),
            TileType.Unwalkable => Color.FromRgb(50, 50, 55),
            _ => Color.FromRgb(40, 40, 50)
        };
    }

    private static Color Blend(Color a, Color b, float t)
    {
        return Color.FromRgb(
            (byte)(a.R + (b.R - a.R) * t),
            (byte)(a.G + (b.G - a.G) * t),
            (byte)(a.B + (b.B - a.B) * t));
    }

    private static Color Darken(Color c, float factor)
    {
        return Color.FromRgb(
            (byte)(c.R * factor),
            (byte)(c.G * factor),
            (byte)(c.B * factor));
    }

    private static Color[] GeneratePalette()
    {
        var p = new Color[256];
        p[0] = Color.FromRgb(0, 0, 0);

        for (var i = 0; i < 256; i++)
        {
            if (i == 0) continue;

            var h = (i * 137.5f) % 360f;
            var s = 0.3f + (i % 7) * 0.05f;
            var l = 0.25f + (i % 5) * 0.08f;

            if (i < 20) { s = 0.5f; l = 0.35f; h = 100 + i * 3; }
            else if (i < 50) { s = 0.4f; l = 0.30f; h = 30 + (i - 20) * 2; }
            else if (i < 80) { s = 0.1f; l = 0.35f; h = 0; }
            else if (i < 100) { s = 0.3f; l = 0.45f; h = 50 + (i - 80) * 2; }
            else if (i < 120) { s = 0.05f; l = 0.55f; h = 0; }
            else if (i < 140) { s = 0.5f; l = 0.25f; h = 210 + (i - 120) * 2; }
            else if (i < 160) { s = 0.4f; l = 0.20f; h = 120 + (i - 140) * 2; }
            else if (i < 180) { s = 0.4f; l = 0.20f; h = 20 + (i - 160) * 2; }
            else if (i < 200) { s = 0.6f; l = 0.30f; h = 0 + (i - 180) * 2; }
            else { s = 0.5f; l = 0.30f; h = 280 + (i - 200) * 2; }

            p[i] = HslToRgb(h, s, l);
        }
        return p;
    }

    private static Color HslToRgb(float h, float s, float l)
    {
        var c = (1f - Math.Abs(2f * l - 1f)) * s;
        var x = c * (1f - Math.Abs(h / 60f % 2f - 1f));
        var m = l - c / 2f;

        float r, g, b;
        if (h < 60) { r = c; g = x; b = 0; }
        else if (h < 120) { r = x; g = c; b = 0; }
        else if (h < 180) { r = 0; g = c; b = x; }
        else if (h < 240) { r = 0; g = x; b = c; }
        else if (h < 300) { r = x; g = 0; b = c; }
        else { r = c; g = 0; b = x; }

        return Color.FromRgb(
            (byte)((r + m) * 255),
            (byte)((g + m) * 255),
            (byte)((b + m) * 255));
    }
}
