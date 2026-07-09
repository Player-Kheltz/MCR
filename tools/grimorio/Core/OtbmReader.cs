using System.IO;
using System.Text;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Core;

// OTBM parser baseado no Remere's Map Editor (RME)
// Estratégia: primeiro lê toda a árvore de nodes, depois interpreta cada node
public class OtbmReader
{
    private const byte NODE_START = 0xFE;
    private const byte NODE_END = 0xFF;
    private const byte ESCAPE = 0xFD;

    // Node types
    private const byte ROOTV1 = 1;
    private const byte MAP_DATA = 2;
    private const byte TILE_AREA = 4;
    private const byte TILE = 5;
    private const byte ITEM = 6;
    private const byte TOWNS = 12;
    private const byte TOWN = 13;
    private const byte HOUSE_TILE = 14;
    private const byte WAYPOINTS = 15;
    private const byte WAYPOINT = 16;

    // Attributes
    private const byte ATTR_TILE_FLAGS = 3;
    private const byte ATTR_ITEM = 9;
    private const byte ATTR_COUNT = 15;
    private const byte ATTR_ACTION_ID = 4;
    private const byte ATTR_UNIQUE_ID = 5;
    private const byte ATTR_CHARGES = 22;
    private const byte ATTR_TEXT = 6;
    private const byte ATTR_DESC = 7;
    private const byte ATTR_TELE_DEST = 8;
    private const byte ATTR_DEPOT_ID = 10;
    private const byte ATTR_HOUSE_DOOR_ID = 14;
    private const byte ATTR_ATTRIBUTE_MAP = 128;

    private class OtbmNode
    {
        public byte Type;
        public byte[] Data = Array.Empty<byte>();  // Raw data of this node
        public int Offset;  // Read position within Data
        public List<OtbmNode> Children = new();
    }

    private OtbmNode _root = null!;
    private OtbmMapData _map = null!;

    private OtbmReader() { }

    public static OtbmMapData? Load(string path)
    {
        try
        {
            var reader = new OtbmReader();
            reader.ParseTree(path);
            return reader.BuildMap();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[OtbmReader] Erro: {ex.Message}");
            return null;
        }
    }

    // ============================================================
    // FASE 1: Ler arquivo OTBM e construir árvore de nodes
    // ============================================================
    private void ParseTree(string path)
    {
        var raw = File.ReadAllBytes(path);

        // Skip 4-byte identifier (Canary: "OTBM" ou "0000" do MCR)
        if (raw.Length < 4)
            throw new InvalidDataException("Arquivo muito pequeno");

        int pos = 4;
        // Consume initial NODE_START (0xFE) before the root node
        if (pos < raw.Length && raw[pos] == NODE_START) pos++;
        _root = ReadNode(raw, ref pos);
    }

    private OtbmNode ReadNode(byte[] raw, ref int pos)
    {
        var node = new OtbmNode();

        // Read node type
        if (pos >= raw.Length) throw new EndOfStreamException("Fim inesperado do arquivo");
        node.Type = raw[pos++];

        // Read node data until we hit NODE_START or NODE_END
        var dataStream = new MemoryStream();
        while (pos < raw.Length)
        {
            byte b = raw[pos++];
            if (b == NODE_START)
            {
                // Child node follows
                node.Children.Add(ReadNode(raw, ref pos));
            }
            else if (b == NODE_END)
            {
                // End of this node
                break;
            }
            else if (b == ESCAPE)
            {
                // Escaped byte: next byte is literal
                if (pos >= raw.Length) throw new EndOfStreamException();
                dataStream.WriteByte(raw[pos++]);
            }
            else
            {
                dataStream.WriteByte(b);
            }
        }

        node.Data = dataStream.ToArray();
        return node;
    }

    // ============================================================
    // FASE 2: Interpretar a árvore de nodes → OtbmMapData
    // ============================================================
    private OtbmMapData BuildMap()
    {
        _map = new OtbmMapData();

        if (_root.Type != ROOTV1 && _root.Type != 0)
            throw new InvalidDataException($"Root type inesperado {_root.Type}");

        var r = new NodeDataReader(_root.Data);
        _map.Version = r.ReadU32();
        _map.Width = r.ReadU16();
        _map.Height = r.ReadU16();

        foreach (var child in _root.Children)
            Dispatch(child);

        // Build floors for the renderer
        BuildFloors();

        return _map;
    }

    private void Dispatch(OtbmNode node)
    {
        switch (node.Type)
        {
            case MAP_DATA:
                foreach (var c in node.Children) Dispatch(c);
                break;
            case TILE_AREA:
                ReadTileArea(node);
                break;
            case TOWNS:
                foreach (var c in node.Children) Dispatch(c);
                break;
            case TOWN:
                ReadTown(node);
                break;
            case WAYPOINTS:
                foreach (var c in node.Children) Dispatch(c);
                break;
            case WAYPOINT:
                ReadWaypoint(node);
                break;
        }
    }

    private void ReadTileArea(OtbmNode node)
    {
        var r = new NodeDataReader(node.Data);
        int baseX = r.ReadU16();
        int baseY = r.ReadU16();
        int baseZ = r.ReadByte();

        foreach (var child in node.Children)
        {
            var tr = new NodeDataReader(child.Data);
            int x = baseX + tr.ReadByte();
            int y = baseY + tr.ReadByte();
            int z = baseZ;

            var tile = new OtbmTile { X = x, Y = y, Z = z };
            tile.Items = new List<OtbmItem>();

            if (child.Type == HOUSE_TILE)
                tile.HouseId = tr.ReadU32();

            // Parse tile attributes from remaining data
            while (tr.HasData())
            {
                byte attr = tr.ReadByte();
                switch (attr)
                {
                    case ATTR_TILE_FLAGS:
                        tile.Flags = (uint)tr.ReadU32();
                        break;
                    case ATTR_ITEM:
                        // Inline item: just id and optional count
                        ushort itemId = tr.ReadU16();
                        byte count = 1;
                        // Only for OTBMv1 with stackables
                        tile.Items.Add(new OtbmItem { Id = itemId, Count = count });
                        break;
                    default:
                        tr.Skip(GetAttrSize(attr, tr));
                        break;
                }
            }

            // Read item children
            foreach (var itemNode in child.Children)
            {
                if (itemNode.Type == ITEM)
                    ReadItemNode(tile, itemNode);
            }

            var key = (x, y, z);
            if (!_map.Tiles.ContainsKey(key))
                _map.Tiles[key] = tile;
        }
    }

    private void ReadItemNode(OtbmTile tile, OtbmNode node)
    {
        var r = new NodeDataReader(node.Data);
        ushort id = r.ReadU16();
        var item = new OtbmItem { Id = id, Count = 1 };

        // Parse item attributes
        while (r.HasData())
        {
            byte attr = r.ReadByte();
            switch (attr)
            {
                case ATTR_COUNT:
                    item.Count = r.ReadByte();
                    break;
                case ATTR_CHARGES:
                    item.Count = (byte)r.ReadU16();
                    break;
                default:
                    r.Skip(GetAttrSize(attr, r));
                    break;
            }
        }

        tile.Items.Add(item);
    }

    private int GetAttrSize(byte attr, NodeDataReader r)
    {
        // Some attributes have fixed size, others use skip
        switch (attr)
        {
            case ATTR_COUNT: return 1;
            case ATTR_ACTION_ID: return 2;
            case ATTR_UNIQUE_ID: return 2;
            case ATTR_CHARGES: return 2;
            case ATTR_TEXT: case ATTR_DESC: return r.ReadU16();
            case ATTR_TELE_DEST: return 5; // u16 x + u16 y + u8 z
            case ATTR_DEPOT_ID: return 2;
            case ATTR_HOUSE_DOOR_ID: return 1;
            case ATTR_ATTRIBUTE_MAP:
                // Key-value pairs: skip all
                return SkipAttributeMap(r);
            default:
                return 1; // skip at least 1
        }
    }

    private int SkipAttributeMap(NodeDataReader r)
    {
        int skipped = 0;
        while (r.HasData())
        {
            byte key = r.ReadByte();
            if (key == 0) break; // end marker
            skipped++;
            var type = r.PeekByte();
            if (type == 1) // string
            {
                int len = r.ReadU16();
                r.Skip(len);
                skipped += 2 + len;
            }
            else // integer
            {
                r.Skip(4);
                skipped += 4;
            }
        }
        return skipped;
    }

    private void ReadTown(OtbmNode node)
    {
        var r = new NodeDataReader(node.Data);
        _map.Towns.Add(new OtbmTown
        {
            Id = r.ReadU32(),
            Name = r.ReadString(),
            TemplePos = (r.ReadU16(), r.ReadU16(), r.ReadByte())
        });
    }

    private void ReadWaypoint(OtbmNode node)
    {
        var r = new NodeDataReader(node.Data);
        _map.Waypoints.Add(new OtbmWaypoint
        {
            Name = r.ReadString(),
            Position = (r.ReadU16(), r.ReadU16(), r.ReadByte())
        });
    }

    private void BuildFloors()
    {
        foreach (var ((x, y, z), tile) in _map.Tiles)
        {
            if (!_map.Floors.TryGetValue(z, out var list))
            {
                list = new List<TileData>();
                _map.Floors[z] = list;
            }

            list.Add(new TileData
            {
                X = x, Y = y, Z = z,
                IsWalkable = (tile.Flags & 8) == 0,
                MinimapColor = 0,
                Type = (tile.Flags & 0x20) != 0 ? TileType.ProtectZone
                     : (tile.Flags & 0x08) != 0 ? TileType.Wall
                     : TileType.Ground
            });
        }
    }

    // ============================================================
    // NodeDataReader: lê dados de um node (little-endian, sem escape)
    // ============================================================
    private class NodeDataReader
    {
        private readonly byte[] _data;
        private int _pos;

        public NodeDataReader(byte[] data) { _data = data; _pos = 0; }

        public bool HasData() => _pos < _data.Length;

        public byte PeekByte() => _pos < _data.Length ? _data[_pos] : (byte)0;

        public byte ReadByte()
        {
            if (_pos >= _data.Length) throw new EndOfStreamException();
            return _data[_pos++];
        }

        public ushort ReadU16()
        {
            if (_pos + 2 > _data.Length) throw new EndOfStreamException();
            ushort val = (ushort)(_data[_pos] | (_data[_pos + 1] << 8));
            _pos += 2;
            return val;
        }

        public int ReadU32()
        {
            if (_pos + 4 > _data.Length) throw new EndOfStreamException();
            int val = _data[_pos] | (_data[_pos + 1] << 8) | (_data[_pos + 2] << 16) | (_data[_pos + 3] << 24);
            _pos += 4;
            return val;
        }

        public string ReadString()
        {
            ushort len = ReadU16();
            if (_pos + len > _data.Length) throw new EndOfStreamException();
            var s = Encoding.UTF8.GetString(_data, _pos, len);
            _pos += len;
            return s;
        }

        public void Skip(int count)
        {
            _pos += count;
            if (_pos > _data.Length) _pos = _data.Length;
        }
    }

    public static bool RunSelfTest()
    {
        try
        {
            // Test 1: NodeDataReader basic operations
            var data = new byte[] { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06 };
            var r = new NodeDataReader(data);
            if (r.ReadByte() != 0x01) return false;
            if (r.ReadU16() != 0x0302) return false;
            if (r.ReadU32() != 0x060504) return false;
            if (r.HasData()) return false;

            // Test 2: ReadString
            var strData = new byte[] { 0x05, 0x00, (byte)'H', (byte)'e', (byte)'l', (byte)'l', (byte)'o' };
            var sr = new NodeDataReader(strData);
            if (sr.ReadString() != "Hello") return false;

            // Test 3: Skip
            var skipData = new byte[] { 0x01, 0x02, 0x03, 0x04 };
            var sk = new NodeDataReader(skipData);
            sk.Skip(2);
            if (sk.ReadByte() != 0x03) return false;

            System.Diagnostics.Debug.WriteLine("[OtbmReader] RunSelfTest: All 3 tests passed");
            return true;
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[OtbmReader] RunSelfTest FAILED: {ex.Message}");
            return false;
        }
    }
}
