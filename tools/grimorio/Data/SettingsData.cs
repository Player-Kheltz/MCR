using System.IO;

namespace MCR.Grimorio.Data;

public class AppSettings
{
    public string ServerPath { get; set; } = "";
    public string ServerExeName { get; set; } = "";
    public string OtclientPath { get; set; } = "";
    public string OtbmPath { get; set; } = "";
    public MySqlSettings MySql { get; set; } = new();
    public bool IsValid => !string.IsNullOrEmpty(ServerPath) && Directory.Exists(ServerPath);
}

public class MySqlSettings
{
    public string Host { get; set; } = "localhost";
    public int Port { get; set; } = 3306;
    public string User { get; set; } = "root";
    public string Password { get; set; } = "";
    public string Database { get; set; } = "mcr";
}
