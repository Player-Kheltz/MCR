namespace MCR.Grimorio.Core;

public static class ViewModelLocator
{
    private static readonly Dictionary<Type, object> _cache = new();

    public static T GetOrCreate<T>() where T : new()
    {
        if (!_cache.ContainsKey(typeof(T)))
            _cache[typeof(T)] = new T();
        return (T)_cache[typeof(T)];
    }

    public static T? Get<T>() where T : class
    {
        return _cache.TryGetValue(typeof(T), out var instance) ? instance as T : null;
    }

    public static void Clear() => _cache.Clear();
}
