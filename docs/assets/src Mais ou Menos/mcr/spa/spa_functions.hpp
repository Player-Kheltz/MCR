#pragma once
#include "lua/scripts/luascript.hpp"

class SPAFunctions {
public:
    static void init(lua_State* L);

    // Performance
    static int luaPlayerProcessDamageAffinity(lua_State* L);

    // Pets
    static int luaPlayerGetPets(lua_State* L);
    static int luaPlayerGetPetCount(lua_State* L);
    static int luaPlayerGetPetMax(lua_State* L);
    static int luaCreatureSetPetBehavior(lua_State* L);
    static int luaCreatureGetPetBehavior(lua_State* L);
    static int luaCreatureSetCustomName(lua_State* L);
    static int luaMonsterSetCompanionInventory(lua_State* L);
    static int luaPlayerAddPet(lua_State* L);
    static int luaPlayerRemovePet(lua_State* L);
    static int luaPlayerGetSurfaceWaypoints(lua_State* L);
    static int luaPlayerTouchSurfaceWaypoint(lua_State* L);
    static int luaPlayerGetStairTransitions(lua_State* L);
    static int luaMonsterScanGlobalArea(lua_State* L);
    static int luaMonsterFindGlobalPath(lua_State* L);
    static int luaMonsterGetGlobalMapInfo(lua_State* L);
    static int luaMonsterGetEngagement(lua_State* L);
    static int luaMonsterGetPursuitDeadline(lua_State* L);
    static int luaGlobalIsWalkable(lua_State* L);
    static int luaGlobalMapAddTile(lua_State* L);
    static int luaGlobalMapAddTempObstacle(lua_State* L);
    static int luaGlobalMapGetDestinations(lua_State* L);
    static int luaGlobalMapIsWalkable(lua_State* L);
    static int luaGlobalMapScanArea(lua_State* L);
    static int luaGlobalMapFindPath(lua_State* L);
    static int luaGlobalMapGetAllTransitions(lua_State* L);
    static int luaGlobalMapGetTileCount(lua_State* L);
    static int luaMonsterIsPursuingStairs(lua_State* L);
    static int luaMonsterIsUsingGlobalPath(lua_State* L);
    static int luaMonsterGetStairOrigin(lua_State* L);
    static int luaMonsterGetStairDestination(lua_State* L);
    static int luaMonsterGetFlankingFailCount(lua_State* L);
    static int luaMonsterGetProactiveFailCount(lua_State* L);
    static int luaMonsterGetIdleFailCount(lua_State* L);
    static int luaMonsterGetLastExplorationScan(lua_State* L);
    static int luaMonsterGetLastGlobalScanAttempt(lua_State* L);
    static int luaMonsterGetLastFlankingAttempt(lua_State* L);
    static int luaMonsterGetLastStairCheck(lua_State* L);
    static int luaMonsterGetWaypoints(lua_State* L);
    static int luaMonsterGetWaypointIndex(lua_State* L);
    static int luaMonsterIsFollowingWaypoints(lua_State* L);
    static int luaMonsterGetStairQueueSize(lua_State* L);
    static int luaMonsterGetStairQueueFront(lua_State* L);
    static int luaMonsterGetStairQueueBack(lua_State* L);
    static int luaMonsterCanStairBeUsed(lua_State* L);
};