using MySql.Data.MySqlClient;
using System.Data;

namespace MCR.Grimorio.Core.Services;

public class DatabaseService : IDatabaseService
{
    private MySqlConnection? _connection;
    private string _connectionString = "";

    public bool IsConnected =>
        _connection != null && _connection.State == ConnectionState.Open;

    public event Action<bool>? OnConnectionChanged;

    public void Configure(string host, int port, string user, string password, string database)
    {
        _connectionString = $"Server={host};Port={port};" +
            $"User Id={user};Password={password};Database={database};" +
            "Allow User Variables=True;Default Command Timeout=30";
    }

    public async Task<bool> ConnectAsync()
    {
        try
        {
            if (string.IsNullOrEmpty(_connectionString))
                return false;

            _connection = new MySqlConnection(_connectionString);
            await _connection.OpenAsync();
            OnConnectionChanged?.Invoke(true);
            return true;
        }
        catch (Exception ex)
        {
            OnConnectionChanged?.Invoke(false);
            System.Diagnostics.Debug.WriteLine($"DB Connect Error: {ex.Message}");
            return false;
        }
    }

    public void Disconnect()
    {
        if (_connection != null)
        {
            _connection.Close();
            _connection.Dispose();
            _connection = null;
            OnConnectionChanged?.Invoke(false);
        }
    }

    public async Task<List<string>> GetTablesAsync()
    {
        var tables = new List<string>();
        if (!IsConnected) return tables;

        try
        {
            using var cmd = new MySqlCommand("SHOW TABLES", _connection);
            using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
                tables.Add(reader.GetString(0));
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"GetTables Error: {ex.Message}");
        }
        return tables;
    }

    [Obsolete("Use parametrized overloads. Raw SQL is a security risk.")]
    public async Task<DataTable> QueryAsync(string sql)
    {
        System.Diagnostics.Debug.WriteLine($"[MCR-SECURITY] QueryAsync raw SQL chamado: {sql[..Math.Min(sql.Length, 100)]}");
        var dt = new DataTable();
        if (!IsConnected) return dt;

        try
        {
            using var cmd = new MySqlCommand(sql, _connection);
            cmd.CommandType = CommandType.Text;
            using var adapter = new MySqlDataAdapter(cmd);
            adapter.Fill(dt);
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Query Error: {ex.Message}");
        }
        return dt;
    }

    [Obsolete("Use parametrized overloads. Raw SQL is a security risk.")]
    public async Task<int> ExecuteAsync(string sql)
    {
        System.Diagnostics.Debug.WriteLine($"[MCR-SECURITY] ExecuteAsync raw SQL chamado: {sql[..Math.Min(sql.Length, 100)]}");
        if (!IsConnected) return -1;
        try
        {
            using var cmd = new MySqlCommand(sql, _connection);
            return await cmd.ExecuteNonQueryAsync();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Execute Error: {ex.Message}");
            return -1;
        }
    }

    public async Task<DataTable> QueryAsync(string sql, params MySqlParameter[] parameters)
    {
        var dt = new DataTable();
        if (!IsConnected) return dt;

        try
        {
            using var cmd = new MySqlCommand(sql, _connection);
            cmd.CommandType = CommandType.Text;
            if (parameters != null && parameters.Length > 0)
                cmd.Parameters.AddRange(parameters);
            using var adapter = new MySqlDataAdapter(cmd);
            await adapter.FillAsync(dt).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Query Error: {ex.Message}");
        }
        return dt;
    }

    public async Task<int> ExecuteAsync(string sql, params MySqlParameter[] parameters)
    {
        if (!IsConnected) return -1;
        try
        {
            using var cmd = new MySqlCommand(sql, _connection);
            if (parameters != null && parameters.Length > 0)
                cmd.Parameters.AddRange(parameters);
            return await cmd.ExecuteNonQueryAsync();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Execute Error: {ex.Message}");
            return -1;
        }
    }

    public async Task<List<Dictionary<string, object>>> GetRowsAsync(
        string table, int limit = 100)
    {
        var rows = new List<Dictionary<string, object>>();
        if (!IsConnected) return rows;

        try
        {
            var sanitized = SanitizeTableName(table);
            using var cmd = new MySqlCommand(
                $"SELECT * FROM `{sanitized}` LIMIT @limit", _connection);
            cmd.Parameters.AddWithValue("@limit", limit);
            using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                var row = new Dictionary<string, object>();
                for (int i = 0; i < reader.FieldCount; i++)
                    row[reader.GetName(i)] = reader.IsDBNull(i) ? "" : reader.GetValue(i);
                rows.Add(row);
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"GetRows Error: {ex.Message}");
        }
        return rows;
    }

    private static string SanitizeTableName(string table)
    {
        var allowed = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "players", "accounts", "guilds", "guild_members", "guild_ranks",
            "player_items", "player_depotitems", "player_inboxitems", "player_storage",
            "player_spells", "player_deaths", "player_outfits",
            "houses", "house_lists", "market_history", "market_offers",
            "global_storage", "server_config", "bans", "ip_bans",
            "account_bans", "account_viplist", "account_vipgrouplist",
            "account_sessions", "store_history", "player_rewards",
            "player_stash", "player_titles", "player_wheeldata",
            "player_namelocks", "player_cyclopedia", "player_forge_history",
            "player_bosstiary", "player_prey", "player_task",
            "dominios_def", "player_dominios", "player_habilidades",
            "mounts", "mount_taming", "imbuements", "imbuement_stats"
        };
        if (!allowed.Contains(table))
            throw new ArgumentException($"Tabela não autorizada: {table}");
        return table;
    }

    public async Task<List<Dictionary<string, object>>> SearchPlayersAsync(string search)
    {
        var results = new List<Dictionary<string, object>>();

        if (!IsConnected) return results;

        try
        {
            var sql = @"SELECT p.id, p.name, p.level, p.vocation, p.health, p.mana,
                               p.capacity, p.experience, p.maglevel, p.soul,
                               p.lastlogin, p.onlinetime, a.name AS account_name,
                               g.name AS guild_name
                        FROM players p
                        LEFT JOIN accounts a ON p.account_id = a.id
                        LEFT JOIN guild_membership gm ON p.id = gm.player_id
                        LEFT JOIN guilds g ON gm.guild_id = g.id
                        WHERE p.name LIKE @search
                           OR p.id = @idSearch
                        LIMIT 50";

            using var cmd = new MySqlCommand(sql, _connection);
            cmd.Parameters.AddWithValue("@search", $"%{search}%");

            if (int.TryParse(search, out var id))
                cmd.Parameters.AddWithValue("@idSearch", id);
            else
                cmd.Parameters.AddWithValue("@idSearch", -1);

            using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                var row = new Dictionary<string, object>();
                for (int i = 0; i < reader.FieldCount; i++)
                    row[reader.GetName(i)] = reader.IsDBNull(i) ? "" : reader.GetValue(i);
                results.Add(row);
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"SearchPlayers Error: {ex.Message}");
        }
        return results;
    }

    public string GetPlayerTableName()
    {
        return "players";
    }
}
