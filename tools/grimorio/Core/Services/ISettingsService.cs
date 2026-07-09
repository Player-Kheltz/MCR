using MCR.Grimorio.Data;

namespace MCR.Grimorio.Core.Services;

public interface ISettingsService
{
    AppSettings Settings { get; }
    event Action? OnSettingsChanged;
    AppSettings Load();
    void Save(AppSettings settings);
    string GetServerPath();
    string GetMonsterPath();
    string GetNpcPath();
    string GetConfigPath();
    string GetItemsXmlPath();
    string GetSprPath();
    string GetLogsPath();
    string GetScriptsPath(int index = 0);
    string GetWorldPath();
}
