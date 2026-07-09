using System.Collections.Generic;

namespace MCR.Grimorio.Data;

public enum TileType
{
    Ground,
    Water,
    Wall,
    ProtectZone,
    Walkable,
    Unwalkable,
    Unknown
}

public class TileData
{
    public int X { get; set; }
    public int Y { get; set; }
    public int Z { get; set; }
    public TileType Type { get; set; } = TileType.Unknown;
    public bool IsWalkable { get; set; }
    public int Speed { get; set; }
    public int MinimapColor { get; set; }
}

public class OtbmMapData
{
    public string Name { get; set; } = "";
    public int Width { get; set; }
    public int Height { get; set; }
    public int Version { get; set; }
    public Dictionary<int, List<TileData>> Floors { get; set; } = new();
    public Dictionary<(int x, int y, int z), OtbmTile> Tiles { get; set; } = new();
    public List<OtbmTown> Towns { get; set; } = new();
    public List<OtbmWaypoint> Waypoints { get; set; } = new();
}

public class OtbmTile
{
    public int X, Y, Z;
    public uint Flags;
    public List<OtbmItem> Items { get; set; } = new();
    public int? HouseId;
}

public class OtbmItem
{
    public ushort Id;
    public byte Count = 1;
}

public class OtbmTown
{
    public int Id;
    public string Name = "";
    public (int x, int y, int z) TemplePos;
}

public class OtbmWaypoint
{
    public string Name = "";
    public (int x, int y, int z) Position;
}

public class PlayerPosition
{
    public string Name { get; set; } = "";
    public int X { get; set; }
    public int Y { get; set; }
    public int Z { get; set; }
    public int OutfitId { get; set; }
}
