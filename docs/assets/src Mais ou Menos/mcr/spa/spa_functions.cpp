#include "spa_functions.hpp"
#include "spa_manager.hpp"

#include "creatures/players/player.hpp"
#include "creatures/monsters/monster.hpp"
#include "global_monster_map.hpp"   // <-- novo include

void SPAFunctions::init(lua_State* L) {

    // --- Pets ---
    Lua::registerMethod(L, "Player", "getPets",           SPAFunctions::luaPlayerGetPets);
    Lua::registerMethod(L, "Player", "getPetCount",       SPAFunctions::luaPlayerGetPetCount);
    Lua::registerMethod(L, "Player", "getPetMax",         SPAFunctions::luaPlayerGetPetMax);
    Lua::registerMethod(L, "Creature", "setCustomName",   SPAFunctions::luaCreatureSetCustomName);
    Lua::registerMethod(L, "Creature", "setPetBehavior",  SPAFunctions::luaCreatureSetPetBehavior);
    Lua::registerMethod(L, "Creature", "getPetBehavior",  SPAFunctions::luaCreatureGetPetBehavior);
    Lua::registerMethod(L, "Player", "addPet",    SPAFunctions::luaPlayerAddPet);
    Lua::registerMethod(L, "Player", "removePet", SPAFunctions::luaPlayerRemovePet);
    Lua::registerMethod(L, "Player", "getSurfaceWaypoints",      SPAFunctions::luaPlayerGetSurfaceWaypoints);
    Lua::registerMethod(L, "Player", "touchSurfaceWaypoint",     SPAFunctions::luaPlayerTouchSurfaceWaypoint);
    Lua::registerMethod(L, "Player", "getStairTransitions",      SPAFunctions::luaPlayerGetStairTransitions);

    // --- GlobalMonsterMap (novo) ---
    Lua::registerMethod(L, "Monster", "scanGlobalArea", SPAFunctions::luaMonsterScanGlobalArea);
    Lua::registerMethod(L, "Monster", "findGlobalPath", SPAFunctions::luaMonsterFindGlobalPath);
    Lua::registerMethod(L, "Monster", "getGlobalMapInfo", SPAFunctions::luaMonsterGetGlobalMapInfo);

    Lua::registerMethod(L, "Monster", "getEngagement", SPAFunctions::luaMonsterGetEngagement);
    Lua::registerMethod(L, "Monster", "getPursuitDeadline", SPAFunctions::luaMonsterGetPursuitDeadline);

    lua_newtable(L);
    lua_setglobal(L, "GlobalMap");
    Lua::registerMethod(L, "GlobalMap", "addTile",               SPAFunctions::luaGlobalMapAddTile);
    Lua::registerMethod(L, "GlobalMap", "addTemporaryObstacle",  SPAFunctions::luaGlobalMapAddTempObstacle);
    Lua::registerMethod(L, "GlobalMap", "getDestinations",       SPAFunctions::luaGlobalMapGetDestinations);
    Lua::registerMethod(L, "GlobalMap", "isWalkable",            SPAFunctions::luaGlobalMapIsWalkable);
    Lua::registerMethod(L, "GlobalMap", "scanArea",              SPAFunctions::luaGlobalMapScanArea);
    Lua::registerMethod(L, "GlobalMap", "findPath",              SPAFunctions::luaGlobalMapFindPath);
    Lua::registerMethod(L, "GlobalMap", "getAllTransitions",     SPAFunctions::luaGlobalMapGetAllTransitions);
    Lua::registerMethod(L, "GlobalMap", "getTileCount",          SPAFunctions::luaGlobalMapGetTileCount);
    Lua::registerMethod(L, "Monster", "isPursuingStairs",      SPAFunctions::luaMonsterIsPursuingStairs);
    Lua::registerMethod(L, "Monster", "isUsingGlobalPath",     SPAFunctions::luaMonsterIsUsingGlobalPath);
    Lua::registerMethod(L, "Monster", "getStairOrigin",        SPAFunctions::luaMonsterGetStairOrigin);
    Lua::registerMethod(L, "Monster", "getStairDestination",   SPAFunctions::luaMonsterGetStairDestination);
    Lua::registerMethod(L, "Monster", "getFlankingFailCount",  SPAFunctions::luaMonsterGetFlankingFailCount);
    Lua::registerMethod(L, "Monster", "getProactiveFailCount", SPAFunctions::luaMonsterGetProactiveFailCount);
    Lua::registerMethod(L, "Monster", "getIdleFailCount",      SPAFunctions::luaMonsterGetIdleFailCount);
    Lua::registerMethod(L, "Monster", "getLastExplorationScan",SPAFunctions::luaMonsterGetLastExplorationScan);
    Lua::registerMethod(L, "Monster", "getLastGlobalScanAttempt", SPAFunctions::luaMonsterGetLastGlobalScanAttempt);
    Lua::registerMethod(L, "Monster", "getLastFlankingAttempt",  SPAFunctions::luaMonsterGetLastFlankingAttempt);
    Lua::registerMethod(L, "Monster", "getLastStairCheck",       SPAFunctions::luaMonsterGetLastStairCheck);
    Lua::registerMethod(L, "Monster", "getWaypoints",        SPAFunctions::luaMonsterGetWaypoints);
    Lua::registerMethod(L, "Monster", "getWaypointIndex",    SPAFunctions::luaMonsterGetWaypointIndex);
    Lua::registerMethod(L, "Monster", "isFollowingWaypoints",SPAFunctions::luaMonsterIsFollowingWaypoints);
    Lua::registerMethod(L, "Monster", "getStairQueueSize",   SPAFunctions::luaMonsterGetStairQueueSize);
    Lua::registerMethod(L, "Monster", "getStairQueueFront",  SPAFunctions::luaMonsterGetStairQueueFront);
    Lua::registerMethod(L, "Monster", "getStairQueueBack",   SPAFunctions::luaMonsterGetStairQueueBack);
    Lua::registerMethod(L, "Monster", "canStairBeUsed", SPAFunctions::luaMonsterCanStairBeUsed);


    // --- Tabela global SPA ---
    lua_newtable(L);
    lua_setglobal(L, "SPA");
    lua_pushcfunction(L, SPAFunctions::luaGlobalIsWalkable);
    lua_setglobal(L, "isWalkableGlobal");

    Lua::registerMethod(L, "SPA", "registerDomain", [](lua_State* L) {
        int32_t id = Lua::getNumber<int32_t>(L, 1);
        std::string name = Lua::getString(L, 2);
        int32_t parentId = Lua::getNumber<int32_t>(L, 3, 0);
        bool ok = SPAManager::getInstance().registerDomain(id, name, parentId);
        Lua::pushBoolean(L, ok);
        return 1;
    });

    Lua::registerMethod(L, "SPA", "getDomain", [](lua_State* L) {
        int32_t id = Lua::getNumber<int32_t>(L, 1);
        auto* def = SPAManager::getInstance().getDomain(id);
        if (def) {
            lua_newtable(L);
            Lua::setField(L, "id", def->id);
            Lua::setField(L, "name", def->name);
            Lua::setField(L, "parentId", def->parentId);
        } else {
            lua_pushnil(L);
        }
        return 1;
    });

    Lua::registerMethod(L, "SPA", "getAllDomainIds", [](lua_State* L) {
        auto ids = SPAManager::getInstance().getAllDomainIds();
        lua_newtable(L);
        for (size_t i = 0; i < ids.size(); ++i) {
            Lua::pushNumber(L, ids[i]);
            lua_rawseti(L, -2, i + 1);
        }
        return 1;
    });

    Lua::registerMethod(L, "SPA", "onEvent", [](lua_State* L) {
        std::string eventName = Lua::getString(L, 1);
        lua_pushvalue(L, 2);
        int ref = luaL_ref(L, LUA_REGISTRYINDEX);
        SPAManager::getInstance().registerEvent(eventName, [ref](lua_State* L, int nargs) {
            lua_rawgeti(L, LUA_REGISTRYINDEX, ref);
            lua_insert(L, 1);
            lua_remove(L, 2);
            lua_call(L, nargs, 0);
        });
        return 0;
    });

    Lua::registerMethod(L, "SPA", "dispatchEvent", [](lua_State* L) {
        std::string eventName = Lua::getString(L, 1);
        int nargs = lua_gettop(L) - 1;
        SPAManager::getInstance().dispatchEvent(eventName, L, nargs);
        return 0;
    });
    
    Lua::registerMethod(L, "Monster", "getGlobalDestinations", [](lua_State* L) -> int {
        auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
        if (!monster) { lua_newtable(L); return 1; }
        Position pos = Lua::getPosition(L, 2);
        auto dests = monster->getGlobalDestinations(pos);
        lua_newtable(L);
        int idx = 1;
        for (const auto& dest : dests) {
            lua_newtable(L);
            Lua::setField(L, "x", dest.x);
            Lua::setField(L, "y", dest.y);
            Lua::setField(L, "z", dest.z);
            lua_rawseti(L, -2, idx++);
        }
        return 1;
    });
}

// ============================================================
// PETS (inalterado)
// ============================================================
int SPAFunctions::luaPlayerGetPets(lua_State* L) {
    auto player = Lua::getUserdataShared<Player>(L, 1, "Player");
    if (!player) { lua_newtable(L); return 1; }
    auto petIds = SPAManager::getInstance().getPets(player->getID());
    lua_newtable(L);
    for (size_t i = 0; i < petIds.size(); ++i) {
        Lua::pushNumber(L, petIds[i]);
        lua_rawseti(L, -2, i + 1);
    }
    return 1;
}

int SPAFunctions::luaPlayerGetPetCount(lua_State* L) {
    auto player = Lua::getUserdataShared<Player>(L, 1, "Player");
    if (!player) { Lua::pushNumber(L, 0); return 1; }
    Lua::pushNumber(L, SPAManager::getInstance().getPetCount(player->getID()));
    return 1;
}

int SPAFunctions::luaPlayerGetPetMax(lua_State* L) {
    auto player = Lua::getUserdataShared<Player>(L, 1, "Player");
    if (!player) { Lua::pushNumber(L, 1); return 1; }
    Lua::pushNumber(L, SPAManager::getInstance().getPetMax(player->getID()));
    return 1;
}

int SPAFunctions::luaCreatureSetCustomName(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (!monster) {
        lua_pushnil(L);
        return 1;
    }
    std::string name = Lua::getString(L, 2);
    monster->setCustomName(name);
    lua_pushboolean(L, true);
    return 1;
}

int SPAFunctions::luaCreatureSetPetBehavior(lua_State* L) {
    auto creature = Lua::getUserdataShared<Creature>(L, 1, "Creature");
    if (!creature) { lua_pushnil(L); return 1; }
    uint32_t behavior = Lua::getNumber<uint32_t>(L, 2);
    SPAManager::getInstance().setPetBehavior(creature->getID(), behavior);
    lua_pushboolean(L, true);
    return 1;
}

int SPAFunctions::luaCreatureGetPetBehavior(lua_State* L) {
    auto creature = Lua::getUserdataShared<Creature>(L, 1, "Creature");
    if (!creature) { lua_pushnil(L); return 1; }
    Lua::pushNumber(L, SPAManager::getInstance().getPetBehavior(creature->getID()));
    return 1;
}

int SPAFunctions::luaPlayerAddPet(lua_State* L) {
    auto player = Lua::getUserdataShared<Player>(L, 1, "Player");
    if (!player) { lua_pushnil(L); return 1; }
    uint32_t petId = Lua::getNumber<uint32_t>(L, 2);
    bool ok = SPAManager::getInstance().registerPet(player->getID(), petId);
    lua_pushboolean(L, ok);
    return 1;
}

int SPAFunctions::luaPlayerRemovePet(lua_State* L) {
    auto player = Lua::getUserdataShared<Player>(L, 1, "Player");
    if (!player) { lua_pushnil(L); return 1; }
    uint32_t petId = Lua::getNumber<uint32_t>(L, 2);
    SPAManager::getInstance().unregisterPet(player->getID(), petId);
    lua_pushboolean(L, true);
    return 1;
}

// ============================================================
// WAYPOINTS DE SUPERFÍCIE (inalterado)
// ============================================================
int SPAFunctions::luaPlayerGetSurfaceWaypoints(lua_State* L) {
    auto player = Lua::getUserdataShared<Player>(L, 1, "Player");
    if (!player) {
        lua_newtable(L);
        return 1;
    }
    const auto& waypoints = player->getSurfaceWaypoints();
    lua_newtable(L);
    int index = 1;
    for (const auto& wp : waypoints) {
        lua_newtable(L);
        Lua::setField(L, "x", wp.pos.x);
        Lua::setField(L, "y", wp.pos.y);
        Lua::setField(L, "z", wp.pos.z);
        Lua::setField(L, "timestamp", static_cast<lua_Number>(wp.timestamp));
        lua_rawseti(L, -2, index++);
    }
    return 1;
}

int SPAFunctions::luaPlayerTouchSurfaceWaypoint(lua_State* L) {
    auto player = Lua::getUserdataShared<Player>(L, 1, "Player");
    if (!player) {
        lua_pushnil(L);
        return 1;
    }
    uint32_t index = Lua::getNumber<uint32_t>(L, 2);
    player->touchSurfaceWaypoint(index);
    lua_pushboolean(L, true);
    return 1;
}

// ============================================================
// TRANSIÇÕES DE ESCADA (inalterado)
// ============================================================
int SPAFunctions::luaPlayerGetStairTransitions(lua_State* L) {
    auto player = Lua::getUserdataShared<Player>(L, 1, "Player");
    if (!player) {
        lua_newtable(L);
        return 1;
    }
    const auto& transitions = player->getStairTransitions();
    lua_newtable(L);
    int index = 1;
    for (const auto& trans : transitions) {
        lua_newtable(L);
        Lua::setField(L, "originX", trans.origin.x);
        Lua::setField(L, "originY", trans.origin.y);
        Lua::setField(L, "originZ", trans.origin.z);
        Lua::setField(L, "destX", trans.destination.x);
        Lua::setField(L, "destY", trans.destination.y);
        Lua::setField(L, "destZ", trans.destination.z);
        Lua::setField(L, "isActive", trans.isActive);
        Lua::setField(L, "timestamp", static_cast<lua_Number>(trans.timestamp));
        lua_rawseti(L, -2, index++);
    }
    return 1;
}

// ============================================================
// GLOBAL MONSTER MAP (NOVOS MÉTODOS)
// ============================================================
int SPAFunctions::luaMonsterScanGlobalArea(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (!monster) {
        lua_pushnil(L);
        return 1;
    }
    int radius = Lua::getNumber<int>(L, 2, 10);
    int maxZ = Lua::getNumber<int>(L, 3, 1);
    size_t added = g_globalMonsterMap().scanArea(monster->getPosition(), radius, maxZ, maxZ);
    Lua::pushNumber(L, added);
    return 1;
}

int SPAFunctions::luaMonsterFindGlobalPath(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (!monster) {
        lua_pushnil(L);
        return 1;
    }
    Position target = Lua::getPosition(L, 2);
    auto path = g_globalMonsterMap().findPath(monster->getPosition(), target);
    lua_newtable(L);
    for (size_t i = 0; i < path.size(); ++i) {
        Lua::pushPosition(L, path[i]);
        lua_rawseti(L, -2, i + 1);
    }
    return 1;
}

int SPAFunctions::luaMonsterGetGlobalMapInfo(lua_State* L) {
    // Debug: retorna o número de tiles e se a posição do monstro é caminhável
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (!monster) {
        lua_pushnil(L);
        return 1;
    }
    auto pos = monster->getPosition();
    lua_newtable(L);
    Lua::setField(L, "totalTiles", (lua_Number)g_globalMonsterMap().getTiles().size());
    Lua::setField(L, "myPosWalkable", g_globalMonsterMap().isWalkable(pos));
    return 1;
}

int SPAFunctions::luaMonsterGetEngagement(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (monster) {
        lua_pushnumber(L, monster->getEngagement());
    } else {
        lua_pushnumber(L, 0);
    }
    return 1;
}

int SPAFunctions::luaMonsterGetPursuitDeadline(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (monster) {
        lua_pushnumber(L, static_cast<lua_Number>(monster->getPursuitDeadline()));
    } else {
        lua_pushnumber(L, 0);
    }
    return 1;
}

int SPAFunctions::luaGlobalIsWalkable(lua_State* L) {
    Position pos = Lua::getPosition(L, 1);
    bool walkable = g_globalMonsterMap().isWalkable(pos);
    Lua::pushBoolean(L, walkable);
    return 1;
}

int SPAFunctions::luaGlobalMapAddTile(lua_State* L) {
    auto pos = Lua::getPosition(L, 1);
    bool walkable = Lua::getBoolean(L, 2, true);
    bool dynamic = Lua::getBoolean(L, 3, false);
    g_globalMonsterMap().addTile(pos, walkable, dynamic);
    return 0;
}

int SPAFunctions::luaGlobalMapAddTempObstacle(lua_State* L) {
    auto pos = Lua::getPosition(L, 1);
    uint64_t duration = Lua::getNumber<uint64_t>(L, 2);
    g_globalMonsterMap().addTemporaryObstacle(pos, duration);
    return 0;
}

int SPAFunctions::luaGlobalMapGetDestinations(lua_State* L) {
    Position pos = Lua::getPosition(L, 1);
    auto dests = g_globalMonsterMap().getDestinations(pos);
    lua_newtable(L);
    for (size_t i = 0; i < dests.size(); ++i) {
        Lua::pushPosition(L, dests[i]);   // esta função recebe lua_State* e const Position&
        lua_rawseti(L, -2, i + 1);
    }
    return 1;
}

int SPAFunctions::luaGlobalMapIsWalkable(lua_State* L) {
    Position pos = Lua::getPosition(L, 2);  // índice 2 porque o 1 é a tabela GlobalMap
    lua_pushboolean(L, g_globalMonsterMap().isWalkable(pos));
    return 1;
}

int SPAFunctions::luaGlobalMapScanArea(lua_State* L) {
    Position origin = Lua::getPosition(L, 2);
    int radius      = Lua::getNumber<int>(L, 3, 15);
    int maxZUp      = Lua::getNumber<int>(L, 4, 2);
    int maxZDown    = Lua::getNumber<int>(L, 5, 2);
    int maxTiles    = Lua::getNumber<int>(L, 6, 2000);
    size_t added = g_globalMonsterMap().scanArea(origin, radius, maxZUp, maxZDown,
                                                  static_cast<size_t>(maxTiles), {});
    lua_pushnumber(L, static_cast<lua_Number>(added));
    return 1;
}

int SPAFunctions::luaGlobalMapFindPath(lua_State* L) {
    Position start = Lua::getPosition(L, 2);
    Position goal  = Lua::getPosition(L, 3);
    auto path = g_globalMonsterMap().findPath(start, goal);
    lua_newtable(L);
    int index = 1;
    for (const auto& pos : path) {
        lua_newtable(L);
        Lua::setField(L, "x", pos.x);
        Lua::setField(L, "y", pos.y);
        Lua::setField(L, "z", pos.z);
        lua_rawseti(L, -2, index++);
    }
    return 1;
}

int SPAFunctions::luaGlobalMapGetAllTransitions(lua_State* L) {
    auto trans = g_globalMonsterMap().getAllTransitions();
    lua_newtable(L);
    int index = 1;
    for (size_t i = 0; i < trans.size(); ++i) {
        lua_newtable(L);
        const auto& pair = trans[i];
        lua_newtable(L);
        Lua::setField(L, "x", pair.first.x);
        Lua::setField(L, "y", pair.first.y);
        Lua::setField(L, "z", pair.first.z);
        lua_setfield(L, -2, "first");
        lua_newtable(L);
        Lua::setField(L, "x", pair.second.x);
        Lua::setField(L, "y", pair.second.y);
        Lua::setField(L, "z", pair.second.z);
        lua_setfield(L, -2, "second");
        lua_rawseti(L, -2, index++);
    }
    return 1;
}

int SPAFunctions::luaGlobalMapGetTileCount(lua_State* L) {
    lua_pushnumber(L, static_cast<lua_Number>(g_globalMonsterMap().getTiles().size()));
    return 1;
}

// ═══════════════════════════════════════════════════════════
// ESTADO DO MONSTRO (DIAGNÓSTICO MCR)
// ═══════════════════════════════════════════════════════════

int SPAFunctions::luaMonsterIsPursuingStairs(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    lua_pushboolean(L, monster && monster->isPursuingStairs());
    return 1;
}

int SPAFunctions::luaMonsterIsUsingGlobalPath(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    lua_pushboolean(L, monster && monster->isUsingGlobalPath());
    return 1;
}

int SPAFunctions::luaMonsterGetStairOrigin(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (monster) {
        Lua::pushPosition(L, monster->getStairOrigin());
    } else {
        lua_pushnil(L);
    }
    return 1;
}

int SPAFunctions::luaMonsterGetStairDestination(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (monster) {
        Lua::pushPosition(L, monster->getStairDestination());
    } else {
        lua_pushnil(L);
    }
    return 1;
}

int SPAFunctions::luaMonsterGetFlankingFailCount(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getFlankingFailCount()) : -1);
    return 1;
}

int SPAFunctions::luaMonsterGetProactiveFailCount(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getProactiveFailCount()) : -1);
    return 1;
}

int SPAFunctions::luaMonsterGetIdleFailCount(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getIdleFailCount()) : -1);
    return 1;
}

int SPAFunctions::luaMonsterGetLastExplorationScan(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getLastExplorationScan()) : 0);
    return 1;
}

int SPAFunctions::luaMonsterGetLastGlobalScanAttempt(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getLastGlobalScanAttempt()) : 0);
    return 1;
}

int SPAFunctions::luaMonsterGetLastFlankingAttempt(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getLastFlankingAttempt()) : 0);
    return 1;
}

int SPAFunctions::luaMonsterGetLastStairCheck(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getLastStairCheck()) : 0);
    return 1;
}

int SPAFunctions::luaMonsterGetWaypoints(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (!monster) { lua_newtable(L); return 1; }
    const auto& wps = monster->getWaypoints();
    lua_newtable(L);
    for (size_t i = 0; i < wps.size(); ++i) {
        Lua::pushPosition(L, wps[i]);
        lua_rawseti(L, -2, i + 1);
    }
    return 1;
}

int SPAFunctions::luaMonsterGetWaypointIndex(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getWaypointIndex()) : -1);
    return 1;
}

int SPAFunctions::luaMonsterIsFollowingWaypoints(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    lua_pushboolean(L, monster && monster->isFollowingWaypoints());
    return 1;
}

int SPAFunctions::luaMonsterGetStairQueueSize(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    Lua::pushNumber(L, monster ? static_cast<lua_Number>(monster->getStairQueueSize()) : 0);
    return 1;
}

int SPAFunctions::luaMonsterGetStairQueueFront(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (monster) {
        auto front = monster->getStairQueueFront();
        if (front) {
            lua_newtable(L);
            Lua::setField(L, "originX", front->origin.x);
            Lua::setField(L, "originY", front->origin.y);
            Lua::setField(L, "originZ", front->origin.z);
            Lua::setField(L, "destX", front->destination.x);
            Lua::setField(L, "destY", front->destination.y);
            Lua::setField(L, "destZ", front->destination.z);
            Lua::setField(L, "isActive", front->isActive);
            return 1;
        }
    }
    lua_pushnil(L);
    return 1;
}

int SPAFunctions::luaMonsterGetStairQueueBack(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (monster) {
        auto back = monster->getStairQueueBack();
        if (back) {
            lua_newtable(L);
            Lua::setField(L, "originX", back->origin.x);
            Lua::setField(L, "originY", back->origin.y);
            Lua::setField(L, "originZ", back->origin.z);
            Lua::setField(L, "destX", back->destination.x);
            Lua::setField(L, "destY", back->destination.y);
            Lua::setField(L, "destZ", back->destination.z);
            Lua::setField(L, "isActive", back->isActive);
            return 1;
        }
    }
    lua_pushnil(L);
    return 1;
}

int SPAFunctions::luaMonsterCanStairBeUsed(lua_State* L) {
    auto monster = Lua::getUserdataShared<Monster>(L, 1, "Monster");
    if (!monster) {
        lua_pushboolean(L, false);
        return 1;
    }
    Position origin = Lua::getPosition(L, 2);
    int deltaZ = Lua::getNumber<int>(L, 3);
    lua_pushboolean(L, monster->canStairBeUsed(origin, deltaZ));
    return 1;
}