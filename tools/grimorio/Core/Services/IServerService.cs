namespace MCR.Grimorio.Core.Services;

public interface IServerService
{
    event Action<string>? OnLogLine;
    event Action<ServerStatus>? OnStatusChanged;
    IReadOnlyList<string> LogLines { get; }
    string ServerPath { get; }
    ServerStatus GetStatus();
    Task<bool> StartAsync();
    Task StopAsync();
    Task RestartAsync();
}
