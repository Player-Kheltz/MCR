namespace MCR.Grimorio.Data;

public class MonsterData
{
    public string Name { get; set; } = "";
    public string FilePath { get; set; } = "";
    public string Category { get; set; } = "";
    public string Description { get; set; } = "";
    public int Experience { get; set; }
    public int Health { get; set; }
    public int MaxHealth { get; set; }
    public int Speed { get; set; }
    public int ManaCost { get; set; }
    public int Armor { get; set; }
    public int Defense { get; set; }
    public int LookType { get; set; }
    public int RaceId { get; set; }
    public string Race { get; set; } = "blood";
    public int Corpse { get; set; }
    public int TargetDistance { get; set; } = 1;
    public bool Summonable { get; set; }
    public bool Attackable { get; set; }
    public bool Hostile { get; set; }
    public bool Convinceable { get; set; }
    public bool Pushable { get; set; }
    public List<MonsterLoot> Loot { get; set; } = new();
    public List<MonsterAttack> Attacks { get; set; } = new();
    public MonsterDefense Defenses { get; set; } = new();
    public MonsterElements Elements { get; set; } = new();

    public double GetXpPerHp() => Health > 0 ? (double)Experience / Health : 0;
    public int GetTotalLootChance() => Loot.Sum(l => l.Chance);
    public int GetMaxDamage() => Attacks.Count > 0 ? Attacks.Max(a => Math.Abs(a.MaxDamage)) : 0;
}

public class MonsterLoot
{
    public int Id { get; set; }
    public int Chance { get; set; }
    public int MaxCount { get; set; } = 1;
}

public class MonsterAttack
{
    public string Name { get; set; } = "melee";
    public int Interval { get; set; } = 2000;
    public int Chance { get; set; } = 100;
    public int MinDamage { get; set; }
    public int MaxDamage { get; set; }
    public string Effect { get; set; } = "";
}

public class MonsterDefense
{
    public int Defense { get; set; }
    public int Armor { get; set; }
}

public class MonsterElements
{
    public int Physical { get; set; }
    public int Energy { get; set; }
    public int Earth { get; set; }
    public int Fire { get; set; }
    public int Ice { get; set; }
    public int Holy { get; set; }
    public int Death { get; set; }
    public int LifeDrain { get; set; }
    public int ManaDrain { get; set; }
    public int Drown { get; set; }
}
