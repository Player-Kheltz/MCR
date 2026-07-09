using System.Collections.Generic;
using System.Threading.Tasks;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Core.Services;

public interface IMapService
{
    Task<OtbmMapData?> LoadOtbmAsync(string path);
    OtbmMapData? CurrentMap { get; }
    List<PlayerPosition> GetPlayerPositions();
}
