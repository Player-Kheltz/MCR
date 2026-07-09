using System.Data;
using MySql.Data.MySqlClient;

namespace MCR.Grimorio.Core.Services;

public interface IDatabaseService
{
    bool IsConnected { get; }
    event Action<bool>? OnConnectionChanged;
    void Configure(string host, int port, string user, string password, string database);
    Task<bool> ConnectAsync();
    void Disconnect();
    Task<List<string>> GetTablesAsync();
    [Obsolete("Use parametrized overloads. Raw SQL is a security risk.")]
    Task<DataTable> QueryAsync(string sql);
    Task<DataTable> QueryAsync(string sql, params MySqlParameter[] parameters);
    [Obsolete("Use parametrized overloads. Raw SQL is a security risk.")]
    Task<int> ExecuteAsync(string sql);
    Task<int> ExecuteAsync(string sql, params MySqlParameter[] parameters);
    Task<List<Dictionary<string, object>>> GetRowsAsync(string table, int limit = 100);
    Task<List<Dictionary<string, object>>> SearchPlayersAsync(string search);
    string GetPlayerTableName();
}
