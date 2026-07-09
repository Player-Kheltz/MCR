using System.Diagnostics;
using System.IO;
using System.Text.RegularExpressions;

namespace MCR.Grimorio.Core.Services;

public class ServerStatus
{
    public bool IsRunning { get; set; }
    public int Pid { get; set; }
    public int PlayersOnline { get; set; }
    public long UptimeMs { get; set; }
    public DateTime StartedAt { get; set; }
    public string LastLogLine { get; set; } = "";
}

public class ServerService : IServerService
{
    private readonly string _serverPath;
    private string _executableName;
    private Process? _serverProcess;
    private readonly List<string> _logBuffer = new();
    private const int MaxLogLines = 500;
    private FileSystemWatcher? _logWatcher;
    private string? _logFilePath;

    public event Action<string>? OnLogLine;
    public event Action<ServerStatus>? OnStatusChanged;

    public IReadOnlyList<string> LogLines => _logBuffer.AsReadOnly();

    public ServerService()
    {
        _serverPath = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));
        _executableName = "canary.exe";
    }

    public ServerService(string serverPath, string executableName = "canary.exe")
    {
        _serverPath = serverPath;
        _executableName = executableName;
    }

    public string ExecutableName => _executableName;

    public void SetExecutableName(string name)
    {
        _executableName = name;
    }

    public string ServerPath => _serverPath;

    public ServerStatus GetStatus()
    {
        var status = new ServerStatus();

        if (_serverProcess != null && !_serverProcess.HasExited)
        {
            status.IsRunning = true;
            status.Pid = _serverProcess.Id;

            if (_serverProcess.StartTime != default)
            {
                status.StartedAt = _serverProcess.StartTime;
                status.UptimeMs = (long)(DateTime.Now - _serverProcess.StartTime).TotalMilliseconds;
            }
        }
        else
        {
            var processes = Process.GetProcessesByName(
                Path.GetFileNameWithoutExtension(_executableName));
            status.IsRunning = processes.Length > 0;
            if (processes.Length > 0)
            {
                status.Pid = processes[0].Id;
                try { status.StartedAt = processes[0].StartTime; } catch { }
            }
        }

        var serverLog = FindServerLog();
        if (serverLog != null)
        {
            var lastLines = ReadLastLines(serverLog, 50);
            foreach (var line in lastLines)
            {
                var playerMatch = Regex.Match(line,
                    @"Players online:\s*(\d+)", RegexOptions.IgnoreCase);
                if (playerMatch.Success)
                    status.PlayersOnline = int.Parse(playerMatch.Groups[1].Value);
            }
            status.LastLogLine = lastLines.Count > 0 ? lastLines[^1] : "";
        }

        return status;
    }

    public Task<bool> StartAsync()
    {
        if (GetStatus().IsRunning) return Task.FromResult(false);

        var executable = Path.Combine(_serverPath, _executableName);
        if (!File.Exists(executable))
        {
            AddLog($"ERRO: {executable} não encontrado");
            return Task.FromResult(false);
        }

        try
        {
            _serverProcess = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = executable,
                    WorkingDirectory = _serverPath,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                }
            };

            _serverProcess.OutputDataReceived += (s, e) =>
            {
                if (e.Data != null) AddLog(e.Data);
            };
            _serverProcess.ErrorDataReceived += (s, e) =>
            {
                if (e.Data != null) AddLog($"[ERRO] {e.Data}");
            };

            _serverProcess.Start();
            _serverProcess.BeginOutputReadLine();
            _serverProcess.BeginErrorReadLine();

            AddLog($"Servidor iniciado (PID: {_serverProcess.Id})");
            StartLogWatcher();
            NotifyStatus();
            return Task.FromResult(true);
        }
        catch (Exception ex)
        {
            AddLog($"ERRO ao iniciar: {ex.Message}");
            return Task.FromResult(false);
        }
    }

    public async Task StopAsync()
    {
        if (_serverProcess != null && !_serverProcess.HasExited)
        {
            _serverProcess.CloseMainWindow();
            if (!_serverProcess.WaitForExit(5000))
                _serverProcess.Kill();
            _serverProcess.Dispose();
            _serverProcess = null;

            AddLog("Servidor parado");
            StopLogWatcher();
            NotifyStatus();
        }
    }

    public async Task RestartAsync()
    {
        await StopAsync();
        await Task.Delay(1000);
        await StartAsync();
    }

    private void AddLog(string line)
    {
        var timestamp = DateTime.Now.ToString("HH:mm:ss");
        var formatted = $"[{timestamp}] {line}";
        _logBuffer.Add(formatted);
        if (_logBuffer.Count > MaxLogLines)
            _logBuffer.RemoveAt(0);
        OnLogLine?.Invoke(formatted);
    }

    private void NotifyStatus()
    {
        OnStatusChanged?.Invoke(GetStatus());
    }

    private void StartLogWatcher()
    {
        var logFile = FindServerLog();
        if (logFile == null) return;

        _logFilePath = logFile;
        _logWatcher = new FileSystemWatcher(
            Path.GetDirectoryName(logFile)!,
            Path.GetFileName(logFile))
        {
            EnableRaisingEvents = true,
            NotifyFilter = NotifyFilters.Size
        };

        long lastLength = new FileInfo(logFile).Length;
        _logWatcher.Changed += (s, e) =>
        {
            try
            {
                var fi = new FileInfo(logFile);
                if (fi.Length > lastLength)
                {
                    using var fs = new FileStream(logFile,
                        FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
                    fs.Seek(lastLength, SeekOrigin.Begin);
                    using var reader = new StreamReader(fs);
                    string? line;
                    while ((line = reader.ReadLine()) != null)
                    {
                        if (!string.IsNullOrWhiteSpace(line))
                            AddLog(line);
                    }
                    lastLength = fi.Length;
                }
                else if (fi.Length < lastLength)
                {
                    // Log foi truncado/rotacionado — reinicia leitura
                    lastLength = 0;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"LogWatcher Error: {ex.Message}");
            }
        };
    }

    private void StopLogWatcher()
    {
        _logWatcher?.Dispose();
        _logWatcher = null;
    }

    private static List<string> ReadLastLines(string path, int count)
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
            System.Diagnostics.Debug.WriteLine($"ReadLastLines Error: {ex.Message}");
        }
        return lines;
    }

    private string? FindServerLog()
    {
        var candidates = new[]
        {
            Path.Combine(_serverPath, "logs", "server.log"),
            Path.Combine(_serverPath, "data", "logs", "server.log"),
            Path.Combine(_serverPath, "log", "server.log"),
            Path.Combine(_serverPath, "server.log")
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
}
