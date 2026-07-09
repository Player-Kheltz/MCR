using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;

namespace MCR.Grimorio.Core.Services;

public class ServerMetrics
{
    public double CpuPercent { get; set; }
    public long MemoryMb { get; set; }
    public int TickTimeMs { get; set; }
    public int SlowQueries { get; set; }
    public int ActiveThreads { get; set; }
    public int ActiveConnections { get; set; }
}

public class ServerMetricsService
{
    private readonly IServerService _serverService;
    private DateTime _lastCpuTime = DateTime.MinValue;
    private TimeSpan _lastCpuTotal = TimeSpan.Zero;

    public ServerMetricsService(IServerService serverService)
    {
        _serverService = serverService;
    }

    public ServerMetrics GetMetrics()
    {
        var metrics = new ServerMetrics();

        try
        {
            var processes = Process.GetProcessesByName("canary");
            if (processes.Length == 0)
                return metrics;

            // Usa o primeiro processo, depois descarta o array completo
            using var process = processes[0];

            metrics.MemoryMb = process.WorkingSet64 / 1024 / 1024;
            metrics.ActiveThreads = process.Threads.Count;

            var now = DateTime.UtcNow;
            var cpuNow = process.TotalProcessorTime;
            if (_lastCpuTime != DateTime.MinValue)
            {
                var cpuDelta = (cpuNow - _lastCpuTotal).TotalMilliseconds;
                var timeDelta = (now - _lastCpuTime).TotalMilliseconds;
                if (timeDelta > 0)
                {
                    metrics.CpuPercent = Math.Round((cpuDelta / timeDelta) * 100 / Environment.ProcessorCount, 1);
                }
            }
            _lastCpuTime = now;
            _lastCpuTotal = cpuNow;

            var serverLog = FindServerLog();
            if (serverLog != null)
            {
                var lastLines = ReadTailLines(serverLog, 200);
                int tickSum = 0, tickCount = 0;

                foreach (var line in lastLines)
                {
                    if (line.Contains("[TICK]") && line.Contains("ms"))
                    {
                        var match = System.Text.RegularExpressions.Regex.Match(line, @"(\d+)\s*ms");
                        if (match.Success && int.TryParse(match.Groups[1].Value, out var ms))
                        {
                            tickSum += ms;
                            tickCount++;
                            if (ms > metrics.TickTimeMs)
                                metrics.TickTimeMs = ms;
                        }
                    }

                    if (line.Contains("SLOW QUERY") || line.Contains("Query time"))
                    {
                        metrics.SlowQueries++;
                    }
                }

                if (tickCount > 0)
                {
                    metrics.TickTimeMs = tickSum / tickCount;
                }
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Metrics Error: {ex.Message}");
        }

        return metrics;
    }

    private static string? FindServerLog()
    {
        var candidates = new[]
        {
            Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary", "logs", "server.log"),
            Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary", "data", "logs", "server.log"),
        };

        foreach (var c in candidates)
        {
            var dir = Path.GetDirectoryName(c);
            if (dir != null && Directory.Exists(dir))
            {
                var files = Directory.GetFiles(dir, "*.log")
                    .OrderByDescending(f => new FileInfo(f).LastWriteTime)
                    .ToArray();
                if (files.Length > 0) return files[0];
            }
        }
        return null;
    }

    private static List<string> ReadTailLines(string path, int count)
    {
        var lines = new List<string>();
        try
        {
            using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            using var reader = new StreamReader(fs);
            var buffer = new Queue<string>();
            string? line;
            while ((line = reader.ReadLine()) != null)
            {
                buffer.Enqueue(line);
                if (buffer.Count > count)
                    buffer.Dequeue();
            }
            lines.AddRange(buffer);
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"ReadTailLines Error: {ex.Message}");
        }
        return lines;
    }
}
