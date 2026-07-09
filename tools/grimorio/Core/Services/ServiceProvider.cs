namespace MCR.Grimorio.Core.Services;

public static class ServiceProvider
{
    private static readonly Dictionary<Type, object> _services = new();
    private static readonly Dictionary<Type, Type> _registrations = new();

    public static void RegisterSingleton<TInterface, TImplementation>()
        where TImplementation : class, TInterface, new()
    {
        _registrations[typeof(TInterface)] = typeof(TImplementation);
    }

    public static void RegisterSingleton<TInterface>(TInterface instance)
    {
        _services[typeof(TInterface)] = instance!;
    }

    public static TInterface Resolve<TInterface>() where TInterface : class
    {
        if (_services.TryGetValue(typeof(TInterface), out var instance))
            return (TInterface)instance;

        if (_registrations.TryGetValue(typeof(TInterface), out var implType))
        {
            var newInstance = Activator.CreateInstance(implType)!;
            _services[typeof(TInterface)] = newInstance;
            return (TInterface)newInstance;
        }

        throw new InvalidOperationException($"Serviço {typeof(TInterface).Name} não registrado.");
    }
}
