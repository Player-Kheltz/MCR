#include "global_monster_map.hpp"
#include "game/game.hpp"
#include "items/tile.hpp"
#include "items/item.hpp"
#include "utils/tools.hpp"
#include <queue>
#include <algorithm>
#include <fstream>
#include <thread>
#include <filesystem>

std::atomic<int> g_activeScans(0);

GlobalMonsterMap& GlobalMonsterMap::getInstance() {
    static GlobalMonsterMap instance;
    return instance;
}

void GlobalMonsterMap::addTileUnlocked(const Position& pos, bool walkable, bool dynamic) {
    auto& info = m_tiles[pos];
    info.walkable = walkable;
    info.dynamic = dynamic;
    info.lastUpdated = getCurrentTimeMs();
}

void GlobalMonsterMap::addTile(const Position& pos, bool walkable, bool dynamic) {
    std::unique_lock lock(m_mutex);
    addTileUnlocked(pos, walkable, dynamic);
}

bool GlobalMonsterMap::isWalkableUnlocked(const Position& pos) const {
    auto it = m_tiles.find(pos);
    if (it == m_tiles.end()) return false;

    // Tiles dinâmicos: SEMPRE consultar o estado real do jogo
    if (it->second.dynamic) {
        auto tile = g_game().map.getTile(pos);
        if (!tile) return false;
        // Bloqueios por itens OU criaturas tornam o tile intransitável
        if (tile->hasFlag(TILESTATE_BLOCKPATH) || tile->hasFlag(TILESTATE_BLOCKSOLID))
            return false;
        if (tile->getTopCreature())
            return false;
        return true;
    }

    // Tiles estáticos: confia no valor armazenado
    return it->second.walkable;
}

bool GlobalMonsterMap::isReachableForPathUnlocked(const Position& pos, const Position& goal) const {
    if (pos == goal) {
        return true;
    }

    // Pathfinding usa SEMPRE o mapa real — o cache do grafo não decide walkability.
    auto tile = g_game().map.getTile(pos);
    if (!tile) {
        return false;
    }

    if (tile->hasFlag(TILESTATE_BLOCKSOLID)) {
        return false;
    }

    // Buracos, rampas activas e escadas: não se caminha sobre o tile (só via aresta de transição Z).
    if (tile->hasFlag(TILESTATE_BLOCKPATH)) {
        return false;
    }

    if (tile->getTopCreature()) {
        return false;
    }

    return true;
}

void GlobalMonsterMap::registerDiscoveredTileUnlocked(const Position& pos, const Position& goal) {
    auto tile = g_game().map.getTile(pos);
    if (!tile) {
        addTileUnlocked(pos, false, false);
        return;
    }

    const bool blocked = tile->hasFlag(TILESTATE_BLOCKPATH) || tile->hasFlag(TILESTATE_BLOCKSOLID);
    const bool occupied = tile->getTopCreature() != nullptr && pos != goal;
    addTileUnlocked(pos, !blocked && !occupied, occupied);
}

size_t GlobalMonsterMap::bridgeCorridorUnlocked(const Position& from, const Position& to, size_t maxSteps) {
    if (from.z != to.z) {
        return 0;
    }

    size_t added = 0;
    Position current = from;
    registerDiscoveredTileUnlocked(current, to);

    for (size_t step = 0; step < maxSteps && current != to; ++step) {
        if (m_tiles.find(current) == m_tiles.end()) {
            ++added;
        }
        registerDiscoveredTileUnlocked(current, to);

        if (current.x != to.x) {
            current.x += (to.x > current.x) ? 1 : -1;
        } else if (current.y != to.y) {
            current.y += (to.y > current.y) ? 1 : -1;
        } else {
            break;
        }
    }

    registerDiscoveredTileUnlocked(to, to);
    if (m_tiles.find(to) != m_tiles.end()) {
        ++added;
    }

    if (added > 0) {
        g_logger().info("[MCR-COGNI] bridgeCorridor {} -> {} registou {} tiles novos.",
            from.toString(), to.toString(), added);
    }
    return added;
}

void GlobalMonsterMap::markTilePermanentlyBlocked(const Position& pos) {
    std::unique_lock lock(m_mutex);
    addTileUnlocked(pos, false, false);
}

bool GlobalMonsterMap::isWalkable(const Position& pos) const {
    std::shared_lock lock(m_mutex);
    return isWalkableUnlocked(pos);
}

std::vector<Position> GlobalMonsterMap::getDestinationsUnlocked(const Position& pos) const {
    auto it = m_transitions.find(pos);
    if (it != m_transitions.end()) return it->second;
    return {};
}

std::vector<Position> GlobalMonsterMap::getDestinations(const Position& pos) const {
    std::shared_lock lock(m_mutex);
    return getDestinationsUnlocked(pos);
}

void GlobalMonsterMap::addStairTransition(const Position& from, const Position& to) {
    std::unique_lock lock(m_mutex);
    auto& vec = m_transitions[from];
    if (std::find(vec.begin(), vec.end(), to) != vec.end()) {
        return; // já existe
    }
    vec.push_back(to);

    // Apenas garante que o tile de origem existe no grafo (sem forçar walkable)
    auto& infoFrom = m_tiles[from];
    infoFrom.lastUpdated = getCurrentTimeMs();

    // Idem para o destino
    auto& infoTo = m_tiles[to];
    infoTo.lastUpdated = getCurrentTimeMs();
}

size_t GlobalMonsterMap::scanArea(const Position& origin, int radius,
                                  int maxZUp, int maxZDown, size_t maxTiles,
                                  const std::deque<StairTransition>& playerStairs,
                                  bool force) {
    if (!force && g_activeScans >= MAX_ACTIVE_SCANS) return 0;
    if (!force) g_activeScans++;

    std::unique_lock lock(m_mutex);
    static const int dx[] = {-1, 1, 0, 0, -1, -1, 1, 1};
    static const int dy[] = {0, 0, -1, 1, -1, 1, -1, 1};

    std::queue<Position> queue;
    std::unordered_set<Position> visited;
    size_t added = 0;

    auto addOrUpdatePos = [&](const Position& pos) {
        if (visited.find(pos) != visited.end()) return;
        visited.insert(pos);

        auto tile = g_game().map.getTile(pos);
        if (!tile) return;

        bool blockedByItem = tile->hasFlag(TILESTATE_BLOCKPATH) || tile->hasFlag(TILESTATE_BLOCKSOLID);
        auto topCreature = tile->getTopCreature();
        bool blockedByCreature = (topCreature != nullptr);

        auto existing = m_tiles.find(pos);
        if (existing != m_tiles.end()) {
            // Atualiza o estado se necessário
            if (blockedByCreature) {
                // Tile já existe: mantém o estado actual (evita sobrescrever
                // com bloqueio temporário causado pelo próprio monstro)
                queue.push(pos);
                return;
            } else if (blockedByItem) {
                existing->second.walkable = false;
                existing->second.dynamic = false;
                existing->second.lastUpdated = getCurrentTimeMs();
            } else {
                existing->second.walkable = true;
                existing->second.dynamic = false;
                existing->second.lastUpdated = getCurrentTimeMs();
            }
            queue.push(pos);
            return;
        }

        // Tile novo
        if (blockedByCreature) {
            addTileUnlocked(pos, false, true);
            m_temporaryObstacles[pos] = {getCurrentTimeMs() + 2000};
            return; // não expande
        } else if (blockedByItem) {
            addTileUnlocked(pos, false, false);
        } else {
            addTileUnlocked(pos, true, false);
            added++;
        }
        queue.push(pos);
    };

    // 1. Transições do jogador
    for (const auto& trans : playerStairs) {
        addOrUpdatePos(trans.origin);
        addOrUpdatePos(trans.destination);
        auto& transVec = m_transitions[trans.origin];
        if (std::find(transVec.begin(), transVec.end(), trans.destination) == transVec.end())
            transVec.push_back(trans.destination);
    }

    // 2. Começa na origem
    addOrUpdatePos(origin);

    // 3. Flood‑fill controlado
    while (!queue.empty() && added < maxTiles) {
        Position current = queue.front(); queue.pop();

        if (std::abs(current.x - origin.x) > radius || std::abs(current.y - origin.y) > radius) continue;
        if (current.z < origin.z - maxZDown || current.z > origin.z + maxZUp) continue;

        for (int i = 0; i < 8; ++i) {
            Position next(current.x + dx[i], current.y + dy[i], current.z);
            if (visited.find(next) != visited.end()) continue;

            if (i >= 4) {
                Position adj1(current.x + dx[i], current.y, current.z);
                Position adj2(current.x, current.y + dy[i], current.z);
                auto tile1 = g_game().map.getTile(adj1);
                auto tile2 = g_game().map.getTile(adj2);
                bool blocked1 = tile1 && (tile1->hasFlag(TILESTATE_BLOCKPATH) || tile1->hasFlag(TILESTATE_BLOCKSOLID));
                bool blocked2 = tile2 && (tile2->hasFlag(TILESTATE_BLOCKPATH) || tile2->hasFlag(TILESTATE_BLOCKSOLID));
                if (blocked1 && blocked2) continue;
            }
            addOrUpdatePos(next);
        }

        auto dests = getDestinationsUnlocked(current);
        for (const auto& dest : dests) {
            addOrUpdatePos(dest);
        }

        // Descoberta automática de escadas
        auto tile = g_game().map.getTile(current);
        if (tile && tile->hasFlag(TILESTATE_FLOORCHANGE)) {
            Position dest = tile->getDestination();
            if (dest.x != 0 || dest.y != 0 || dest.z != 0) {
                auto& trans = m_transitions[current];
                if (std::find(trans.begin(), trans.end(), dest) == trans.end()) {
                    trans.push_back(dest);
                }
                addOrUpdatePos(dest);
                for (int n = 0; n < 8; ++n) {
                    addOrUpdatePos(Position(dest.x + dx[n], dest.y + dy[n], dest.z));
                }
            } else {
                for (int newZ : {current.z + 1, current.z - 1}) {
                    if (newZ >= 0 && newZ <= 15) {
                        Position destSimple(current.x, current.y, newZ);
                        auto& trans = m_transitions[current];
                        if (std::find(trans.begin(), trans.end(), destSimple) == trans.end()) {
                            trans.push_back(destSimple);
                        }
                        addOrUpdatePos(destSimple);
                        for (int n = 0; n < 8; ++n) {
                            addOrUpdatePos(Position(destSimple.x + dx[n], destSimple.y + dy[n], destSimple.z));
                        }
                    }
                }
            }
        }
    }

    if (!force) g_activeScans--;
    return added;
}

std::vector<Position> GlobalMonsterMap::findPath(const Position& start, const Position& goal) {
    std::unique_lock lock(m_mutex);
    return findPathUnlocked(start, goal);
}

std::vector<Position> GlobalMonsterMap::findPathUnlocked(const Position& start, const Position& goal) {
    if (start == goal) {
        return {start};
    }

    registerDiscoveredTileUnlocked(start, goal);
    registerDiscoveredTileUnlocked(goal, goal);

    // ═══════════════════════════════════════════════════
    // CORREÇÃO MCR: O tile onde a criatura está é SEMPRE
    // caminhável para ela. O registerDiscovered pode tê‑lo
    // marcado como bloqueado (dynamic), revertemos isso.
    addTileUnlocked(start, true, false);
    // ═══════════════════════════════════════════════════

    const auto runBfs = [this, &start, &goal]() -> std::vector<Position> {
        bool goalIsStair = false;
        if (auto goalTile = g_game().map.getTile(goal)) {
            goalIsStair = goalTile->hasFlag(TILESTATE_FLOORCHANGE);
        }

        // ──────── CORREÇÃO: ignora criatura no tile inicial ────────
        auto isReachable = [&](const Position& pos) {
            if (pos == start) return true;   // sempre permite a origem
            return isReachableForPathUnlocked(pos, goal);
        };
        // ────────────────────────────────────────────────────────────

        std::unordered_map<Position, Position> cameFrom;
        std::queue<Position> queue;
        queue.push(start);
        cameFrom[start] = start;

        size_t nodes = 0;
        const size_t maxNodes = 2000;

        auto tryEnqueue = [&](const Position& current, const Position& next) -> bool {
            if (cameFrom.find(next) != cameFrom.end()) {
                return false;
            }

            if (!isReachable(next)) {
                return false;
            }

            registerDiscoveredTileUnlocked(next, goal);
            cameFrom[next] = current;
            queue.push(next);
            ++nodes;
            return true;
        };

        while (!queue.empty() && nodes < maxNodes) {
            Position current = queue.front();
            queue.pop();

            if (current == goal) {
                std::vector<Position> path;
                constexpr size_t maxPathSteps = 500;
                size_t steps = 0;
                while (current != start && steps < maxPathSteps) {
                    path.push_back(current);
                    const auto parentIt = cameFrom.find(current);
                    if (parentIt == cameFrom.end()) {
                        path.clear();
                        break;
                    }
                    current = parentIt->second;
                    ++steps;
                }
                if (!path.empty()) {
                    std::reverse(path.begin(), path.end());
                    g_logger().info("[MCR-COGNI] findPath OK: {} -> {} ({} passos, {} nós expandidos).",
                        start.toString(), goal.toString(), path.size(), nodes);
                    return path;
                }
            }

            static const int dx[] = {-1, 1, 0, 0, -1, -1, 1, 1};
            static const int dy[] = {0, 0, -1, 1, -1, 1, -1, 1};
            for (int i = 0; i < 8; ++i) {
                Position next(current.x + dx[i], current.y + dy[i], current.z);

                if (i >= 4) {
                    Position adj1(current.x + dx[i], current.y, current.z);
                    Position adj2(current.x, current.y + dy[i], current.z);
                    if (!isReachable(adj1) && !isReachable(adj2)) {
                        continue;
                    }
                }

                tryEnqueue(current, next);
            }

            for (const auto& dest : getDestinationsUnlocked(current)) {
                tryEnqueue(current, dest);
            }
        }

        if (goalIsStair || !m_transitions.empty()) {
            // ═══ BFS BIDIRECIONAL (fallback) ═══
            // ── mesma correção: usa isReachable também ──
            auto isReachableGoal = [&](const Position& pos) {
                if (pos == goal) return true;
                return isReachableForPathUnlocked(pos, goal);
            };

            std::unordered_map<Position, Position> cameFromGoal;
            std::queue<Position> queueGoal;
            queueGoal.push(goal);
            cameFromGoal[goal] = goal;
            size_t nodesGoal = 0;
            const size_t maxNodesGoal = 1500;

            while (!queueGoal.empty() && nodesGoal < maxNodesGoal) {
                Position current = queueGoal.front();
                queueGoal.pop();

                if (cameFrom.find(current) != cameFrom.end()) {
                    std::vector<Position> path;
                    Position node = current;
                    while (node != start) {
                        path.push_back(node);
                        node = cameFrom[node];
                    }
                    std::reverse(path.begin(), path.end());
                    node = current;
                    while (node != goal) {
                        node = cameFromGoal[node];
                        path.push_back(node);
                    }
                    g_logger().info("[MCR-COGNI] findPath OK (bidirecional): {} -> {} ({} passos, {}+{} nós).",
                        start.toString(), goal.toString(), path.size(), nodes, nodesGoal);
                    return path;
                }

                static const int dx[] = {-1, 1, 0, 0, -1, -1, 1, 1};
                static const int dy[] = {0, 0, -1, 1, -1, 1, -1, 1};
                for (int i = 0; i < 8; ++i) {
                    Position next(current.x + dx[i], current.y + dy[i], current.z);

                    if (i >= 4) {
                        Position adj1(current.x + dx[i], current.y, current.z);
                        Position adj2(current.x, current.y + dy[i], current.z);
                        if (!isReachableGoal(adj1) && !isReachableGoal(adj2)) {
                            continue;
                        }
                    }

                    if (cameFromGoal.find(next) != cameFromGoal.end()) {
                        continue;
                    }
                    if (!isReachableGoal(next)) {
                        continue;
                    }

                    registerDiscoveredTileUnlocked(next, goal);
                    cameFromGoal[next] = current;
                    queueGoal.push(next);
                    ++nodesGoal;
                }

                for (const auto& dest : getDestinationsUnlocked(current)) {
                    if (cameFromGoal.find(dest) != cameFromGoal.end()) {
                        continue;
                    }
                    if (!isReachableGoal(dest)) {
                        continue;
                    }

                    registerDiscoveredTileUnlocked(dest, goal);
                    cameFromGoal[dest] = current;
                    queueGoal.push(dest);
                    ++nodesGoal;
                }
            }
        }

        return {};
    };

    auto path = runBfs();
    if (!path.empty()) {
        return path;
    }

    if (start.z == goal.z) {
        bridgeCorridorUnlocked(start, goal, 64);
        path = runBfs();
        if (!path.empty()) {
            return path;
        }

        auto approach = findNearestApproachToUnlocked(start, goal);
        if (!approach.empty()) {
            g_logger().info("[MCR-COGNI] findPath aproximação: {} -> {} ({} passos).",
                start.toString(), goal.toString(), approach.size());
            return approach;
        }
    }

    const bool startWalkable = true; // já garantido pela correção anterior
    const bool goalWalkable = isReachableForPathUnlocked(goal, goal);

    g_logger().info(
        "[MCR-COGNI] findPath FALHOU: start={} goal={} startWalkable={} goalWalkable={} tilesGrafo={} transicoes={}",
        start.toString(),
        goal.toString(),
        startWalkable,
        goalWalkable,
        m_tiles.size(),
        m_transitions.size()
    );

    return {};
}

std::vector<Position> GlobalMonsterMap::findNearestApproachTo(const Position& start, const Position& goal) {
    std::unique_lock lock(m_mutex);
    return findNearestApproachToUnlocked(start, goal);
}

std::vector<Position> GlobalMonsterMap::findNearestApproachToUnlocked(const Position& start, const Position& goal) {
    if (start == goal) {
        return {};
    }

    // Garante que o tile do monstro não está bloqueado por ele próprio
    addTileUnlocked(start, true, false);

    // ──────── CORREÇÃO: ignora criatura no tile inicial ────────
    auto isReachable = [&](const Position& pos) {
        if (pos == start) return true;
        return isReachableForPathUnlocked(pos, goal);
    };
    // ────────────────────────────────────────────────────────────

    std::unordered_map<Position, Position> cameFrom;
    std::queue<Position> queue;
    queue.push(start);
    cameFrom[start] = start;

    Position bestTile = start;
    int bestDist = std::abs(start.x - goal.x) + std::abs(start.y - goal.y);

    size_t nodes = 0;
    const size_t maxNodes = 3000;

    while (!queue.empty() && nodes < maxNodes) {
        Position current = queue.front();
        queue.pop();

        int dist = std::abs(current.x - goal.x) + std::abs(current.y - goal.y);
        if (dist < bestDist && isReachable(current)) {
            bestDist = dist;
            bestTile = current;
        }

        static const int dx[] = {-1, 1, 0, 0, -1, -1, 1, 1};
        static const int dy[] = {0, 0, -1, 1, -1, 1, -1, 1};
        for (int i = 0; i < 8; ++i) {
            Position next(current.x + dx[i], current.y + dy[i], current.z);
            if (cameFrom.find(next) != cameFrom.end()) {
                continue;
            }

            if (i >= 4) {
                Position adj1(current.x + dx[i], current.y, current.z);
                Position adj2(current.x, current.y + dy[i], current.z);
                if (!isReachable(adj1) && !isReachable(adj2)) {
                    continue;
                }
            }

            if (!isReachable(next)) {
                continue;
            }

            registerDiscoveredTileUnlocked(next, goal);
            cameFrom[next] = current;
            queue.push(next);
            ++nodes;
        }
    }

    if (bestTile == start) {
        return {};
    }

    std::vector<Position> path;
    Position cur = bestTile;
    while (cur != start) {
        path.push_back(cur);
        auto it = cameFrom.find(cur);
        if (it == cameFrom.end() || it->second == cur) {
            path.clear();
            break;
        }
        cur = it->second;
    }
    if (path.empty()) {
        return {};
    }
    std::reverse(path.begin(), path.end());
    return path;
}

void GlobalMonsterMap::notifyTileChange(const Position& pos) {
    std::unique_lock lock(m_mutex);
    auto tile = g_game().map.getTile(pos);
    if (!tile) return;
    bool blocked = tile->hasFlag(TILESTATE_BLOCKPATH) || tile->hasFlag(TILESTATE_BLOCKSOLID);
    auto it = m_tiles.find(pos);
    if (it != m_tiles.end() && it->second.walkable == !blocked) return;
    addTileUnlocked(pos, !blocked, it != m_tiles.end() && it->second.dynamic);
}

void GlobalMonsterMap::addTemporaryObstacle(const Position& pos, uint64_t durationMs) {
    std::unique_lock lock(m_mutex);
    m_temporaryObstacles[pos] = {getCurrentTimeMs() + durationMs};
    auto& info = m_tiles[pos];
    info.walkable = false;
    info.dynamic = true;
    info.lastUpdated = getCurrentTimeMs();
}

void GlobalMonsterMap::cleanupTemporaryObstacles() {
    std::unique_lock lock(m_mutex);
    uint64_t now = getCurrentTimeMs();
    for (auto it = m_temporaryObstacles.begin(); it != m_temporaryObstacles.end(); ) {
        if (now >= it->second.expiryTime) {
            auto tile = g_game().map.getTile(it->first);
            bool walkable = true;
            if (tile) {
                walkable = !(tile->hasFlag(TILESTATE_BLOCKPATH) || tile->hasFlag(TILESTATE_BLOCKSOLID));
            }
            auto tileIt = m_tiles.find(it->first);
            if (tileIt != m_tiles.end()) {
                tileIt->second.walkable = walkable;
                tileIt->second.dynamic = false;
                tileIt->second.lastUpdated = now;
            }
            it = m_temporaryObstacles.erase(it);
        } else {
            ++it;
        }
    }
}

void GlobalMonsterMap::saveToFile(const std::string& filename) {
    validateTransitions();

    std::vector<std::tuple<uint16_t, uint16_t, uint8_t, uint16_t>> staticTiles;
    std::vector<std::tuple<uint16_t, uint16_t, uint8_t, uint16_t, uint16_t, uint8_t>> staticTransitions;
    {
        std::shared_lock lock(m_mutex);
        // Tiles estáticos
        for (const auto& [pos, info] : m_tiles) {
            if (!info.dynamic) {
                uint16_t flags = info.walkable ? 0x01 : 0x00;
                staticTiles.emplace_back(pos.x, pos.y, pos.z, flags);
            }
        }
        // Transições (apenas as que ligam tiles estáticos)
        for (const auto& [origin, dests] : m_transitions) {
            for (const auto& dest : dests) {
                staticTransitions.emplace_back(origin.x, origin.y, origin.z, dest.x, dest.y, dest.z);
            }
        }
    }

    g_logger().info("[MCR-COGNI] A guardar {} tiles e {} transições estáticos em {}.",
        staticTiles.size(), staticTransitions.size(), filename);

    std::thread([staticTiles = std::move(staticTiles),
                 staticTransitions = std::move(staticTransitions), filename]() {
        std::ofstream file(filename, std::ios::binary);
        if (!file) return;

        // Tiles
        uint32_t tileCount = static_cast<uint32_t>(staticTiles.size());
        file.write(reinterpret_cast<const char*>(&tileCount), sizeof(tileCount));
        for (const auto& [x, y, z, flags] : staticTiles) {
            file.write(reinterpret_cast<const char*>(&x), sizeof(x));
            file.write(reinterpret_cast<const char*>(&y), sizeof(y));
            file.write(reinterpret_cast<const char*>(&z), sizeof(z));
            file.write(reinterpret_cast<const char*>(&flags), sizeof(flags));
        }

        // Transições
        uint32_t transCount = static_cast<uint32_t>(staticTransitions.size());
        file.write(reinterpret_cast<const char*>(&transCount), sizeof(transCount));
        for (const auto& [ox, oy, oz, dx, dy, dz] : staticTransitions) {
            file.write(reinterpret_cast<const char*>(&ox), sizeof(ox));
            file.write(reinterpret_cast<const char*>(&oy), sizeof(oy));
            file.write(reinterpret_cast<const char*>(&oz), sizeof(oz));
            file.write(reinterpret_cast<const char*>(&dx), sizeof(dx));
            file.write(reinterpret_cast<const char*>(&dy), sizeof(dy));
            file.write(reinterpret_cast<const char*>(&dz), sizeof(dz));
        }

        g_logger().info("[MCR-COGNI] Guardados {} tiles e {} transições estáticos em {}.",
            tileCount, transCount, filename);
    }).detach();
}

void GlobalMonsterMap::loadFromFile(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) {
        g_logger().warn("[MCR-COGNI] Ficheiro de mapa cognitivo não encontrado: {}", filename);
        return;
    }

    // Ler tiles
    uint32_t tileCount;
    file.read(reinterpret_cast<char*>(&tileCount), sizeof(tileCount));
    g_logger().info("[MCR-COGNI] A carregar {} tiles do ficheiro {}.", tileCount, filename);
    for (uint32_t i = 0; i < tileCount; ++i) {
        uint16_t x, y, flags;
        uint8_t z;
        file.read(reinterpret_cast<char*>(&x), sizeof(x));
        file.read(reinterpret_cast<char*>(&y), sizeof(y));
        file.read(reinterpret_cast<char*>(&z), sizeof(z));
        file.read(reinterpret_cast<char*>(&flags), sizeof(flags));
        bool walkable = (flags & 0x01) != 0;
        addTile(Position(x, y, z), walkable, false);
    }

    // Ler transições (se existirem no ficheiro)
    uint32_t transCount = 0;
    if (file.peek() != EOF) {
        file.read(reinterpret_cast<char*>(&transCount), sizeof(transCount));
        g_logger().info("[MCR-COGNI] A carregar {} transições do ficheiro {}.", transCount, filename);
        for (uint32_t i = 0; i < transCount; ++i) {
            uint16_t ox, oy, dx, dy;
            uint8_t oz, dz;
            file.read(reinterpret_cast<char*>(&ox), sizeof(ox));
            file.read(reinterpret_cast<char*>(&oy), sizeof(oy));
            file.read(reinterpret_cast<char*>(&oz), sizeof(oz));
            file.read(reinterpret_cast<char*>(&dx), sizeof(dx));
            file.read(reinterpret_cast<char*>(&dy), sizeof(dy));
            file.read(reinterpret_cast<char*>(&dz), sizeof(dz));
            addStairTransition(Position(ox, oy, oz), Position(dx, dy, dz));
        }
    }

    validateTransitions();
    g_logger().info("[MCR-COGNI] Mapa cognitivo carregado com {} tiles e {} transições estáticos (validadas).",
        m_tiles.size(), m_transitions.size());
}

void GlobalMonsterMap::validateTransitions() {
    std::unique_lock lock(m_mutex);
    for (auto it = m_transitions.begin(); it != m_transitions.end(); ) {
        auto& dests = it->second;
        dests.erase(
            std::remove_if(dests.begin(), dests.end(), [this](const Position& dest) {
                auto tile = g_game().map.getTile(dest);
                // Se o tile não está carregado, assume que é válido (pode ser uma escada)
                if (!tile) return false;
                // NUNCA remove uma transição para uma escada
                if (tile->hasFlag(TILESTATE_FLOORCHANGE)) return false;
                // Remove apenas se for um bloqueio sólido permanente (parede, rocha)
                return tile->hasFlag(TILESTATE_BLOCKSOLID);
            }),
            dests.end()
        );

        if (dests.empty()) {
            it = m_transitions.erase(it);
        } else {
            ++it;
        }
    }
}

std::vector<std::pair<Position, Position>> GlobalMonsterMap::getAllTransitions() const {
    std::shared_lock lock(m_mutex);
    std::vector<std::pair<Position, Position>> result;
    for (const auto& [origin, dests] : m_transitions) {
        for (const auto& dest : dests) {
            result.emplace_back(origin, dest);
        }
    }
    return result;
}


size_t GlobalMonsterMap::scanPlayerTrail(const Position& center, int radius) {
    // Força o scan independentemente do MAX_ACTIVE_SCANS
    // e usa um raio pequeno com profundidade Z=1.
    // Reutiliza o scanArea já testado.
    size_t added = scanArea(center, radius, 1, 1, 150, {}, true);
    if (added > 0) {
        g_logger().info("[MCR-COGNI] scanPlayerTrail em {} adicionou {} tiles.", center.toString(), added);
    }
    return added;
}