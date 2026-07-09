using System.IO;

namespace MCR.Grimorio.Core.Detection;

public class MCRDetectionResult
{
    public bool HasSkillsSpa { get; set; }
    public bool HasMultiPiso { get; set; }
    public bool HasMountSummon { get; set; }
    public bool HasNpcDialogue { get; set; }
    public bool IsMcrServer => HasSkillsSpa || HasMountSummon;

    public int DetectedModules =>
        (HasSkillsSpa ? 1 : 0) + (HasMultiPiso ? 1 : 0) +
        (HasMountSummon ? 1 : 0) + (HasNpcDialogue ? 1 : 0);
}

public class MCRDetector
{
    private readonly string _canaryDir;
    private MCRDetectionResult? _cache;

    public MCRDetector()
    {
        _canaryDir = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));
    }

    public MCRDetectionResult Detect()
    {
        if (_cache != null) return _cache;
        _cache = new MCRDetectionResult();

        if (!Directory.Exists(_canaryDir)) return _cache;

        var mcrDir = Path.Combine(_canaryDir, "data", "scripts", "MCR");
        var mcrDir2 = Path.Combine(_canaryDir, "data-canary", "scripts", "MCR");

        var dirs = new[] { mcrDir, mcrDir2 };

        foreach (var dir in dirs)
        {
            if (!Directory.Exists(dir)) continue;

            _cache.HasSkillsSpa = Directory.Exists(Path.Combine(dir, "SPA"))
                || File.Exists(Path.Combine(dir, "SPA", "core", "constantes.lua"));

            _cache.HasMountSummon = File.Exists(Path.Combine(dir, "mount_summon.lua"))
                || Directory.Exists(Path.Combine(dir, "MountSummon"));

            _cache.HasNpcDialogue = File.Exists(Path.Combine(dir, "npc_utils.lua"))
                || File.Exists(Path.Combine(dir, "Geral", "npc_utils.lua"))
                || File.Exists(Path.Combine(dir, "oraculo.lua"));
        }

        var srcMcrDir = Path.Combine(_canaryDir, "src", "mcr");
        if (Directory.Exists(srcMcrDir))
        {
            _cache.HasMultiPiso = File.Exists(Path.Combine(srcMcrDir, "core", "monster_ai.cpp"))
                || File.Exists(Path.Combine(srcMcrDir, "monster_ai.cpp"))
                || Directory.GetFiles(srcMcrDir, "*multi*", SearchOption.AllDirectories).Length > 0;
        }

        return _cache;
    }

    public string GetDetectionSummary()
    {
        var r = Detect();
        if (!r.IsMcrServer) return "Servidor OTServ padrão (sem módulos MCR detectados)";

        var parts = new List<string> { "Módulos MCR detectados:" };
        if (r.HasSkillsSpa) parts.Add("  ✓ Skills SPA");
        if (r.HasMultiPiso) parts.Add("  ✓ Multi-Piso");
        if (r.HasMountSummon) parts.Add("  ✓ MountSummon");
        if (r.HasNpcDialogue) parts.Add("  ✓ NPC Dialogue");
        return string.Join("\n", parts);
    }
}
