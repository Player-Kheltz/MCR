/**
 * Projeto MCR – GlobalMonsterMap v7.4.1
 * Mapa cognitivo partilhado por todos os monstros.
 */
#pragma once
#include <unordered_map>
#include <vector>
#include <cstdint>
#include <deque>
#include <atomic>
#include <shared_mutex>
#include <tuple>
#include "game/movement/position.hpp"
#include "creatures/players/player.hpp"


struct StairTransition;

struct TileInfo {
    bool walkable = true;
    bool dynamic = false;
    uint64_t lastUpdated = 0;
};

struct TemporaryObstacle {
    uint64_t expiryTime;
};

class GlobalMonsterMap {
public:
    static GlobalMonsterMap& getInstance();

    void addTile(const Position& pos, bool walkable, bool dynamic = false);
    bool isWalkable(const Position& pos) const;
    size_t scanArea(const Position& origin, int radius, int maxZUp = 1, int maxZDown = 1,
                    size_t maxTiles = 2000,
                    const std::deque<StairTransition>& playerStairs = {},
                    bool force = false);
    std::vector<Position> findPath(const Position& start, const Position& goal);
    void markTilePermanentlyBlocked(const Position& pos);
    std::vector<Position> findNearestApproachTo(const Position& start, const Position& goal);
    void notifyTileChange(const Position& pos);
    void addTemporaryObstacle(const Position& pos, uint64_t durationMs);
    void cleanupTemporaryObstacles();
    void saveToFile(const std::string& filename);
    void loadFromFile(const std::string& filename);
    void addStairTransition(const Position& from, const Position& to);
    void validateTransitions();
    std::vector<Position> getDestinations(const Position& pos) const;
    std::vector<std::pair<Position, Position>> getAllTransitions() const;

    const std::unordered_map<Position, TileInfo>& getTiles() const { return m_tiles; }

    size_t scanPlayerTrail(const Position& center, int radius = 5);

private:
    GlobalMonsterMap() = default;
    void addTileUnlocked(const Position& pos, bool walkable, bool dynamic);
    bool isWalkableUnlocked(const Position& pos) const;
    bool isReachableForPathUnlocked(const Position& pos, const Position& goal) const;
    void registerDiscoveredTileUnlocked(const Position& pos, const Position& goal);
    size_t bridgeCorridorUnlocked(const Position& from, const Position& to, size_t maxSteps = 64);
    std::vector<Position> findPathUnlocked(const Position& start, const Position& goal);
    std::vector<Position> findNearestApproachToUnlocked(const Position& start, const Position& goal);
    std::vector<Position> getDestinationsUnlocked(const Position& pos) const;

    std::unordered_map<Position, TileInfo> m_tiles;
    std::unordered_map<Position, std::vector<Position>> m_transitions;
    std::unordered_map<Position, TemporaryObstacle> m_temporaryObstacles;
    mutable std::shared_mutex m_mutex;
};

inline GlobalMonsterMap& g_globalMonsterMap() {
    return GlobalMonsterMap::getInstance();
}

extern std::atomic<int> g_activeScans;
constexpr int MAX_ACTIVE_SCANS = 40;

inline bool mcrTryScanArea(const Position& origin, int radius, int maxZUp, int maxZDown,
                           size_t maxTiles,
                           const std::deque<StairTransition>& playerStairs = {},
                           size_t* outAdded = nullptr,
                           bool force = false) {
    if (!force && g_activeScans >= MAX_ACTIVE_SCANS) {
        if (outAdded) *outAdded = 0;
        return false;
    }
    size_t added = g_globalMonsterMap().scanArea(origin, radius, maxZUp, maxZDown, maxTiles, playerStairs, force);
    if (outAdded) *outAdded = added;
    return true;
}