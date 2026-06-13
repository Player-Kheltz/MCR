/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#pragma once
#include "creatures/creature.hpp"
#include "lua/lua_definitions.hpp"
#include "mcr/spa/global_monster_map.hpp"
#include "creatures/players/player.hpp"

struct spellBlock_t;
class MonsterType;
class Tile;
class Creature;
class Game;
class SpawnMonster;

struct StairTransition;
class Player;

using CreatureVector = std::vector<std::shared_ptr<Creature>>;

class Monster final : public Creature {
public:
	static std::shared_ptr<Monster> createMonster(const std::string &name);
	static int32_t despawnRange;
	static int32_t despawnRadius;

	explicit Monster(const std::shared_ptr<MonsterType> &mType);

	// non-copyable
	Monster(const Monster &) = delete;
	Monster &operator=(const Monster &) = delete;

	std::shared_ptr<Monster> getMonster() override;
	std::shared_ptr<const Monster> getMonster() const override;

	void setID() override;

	void addList() override;
	void removeList() override;

	const std::string &getName() const override;
	void setName(const std::string &name);

	// Permitir que scripts Lua definam um nome customizado para summons/pets
    void setCustomName(const std::string& name);
    std::string getCustomName() const override;  // <-- override

	// MCR Public - Perseguição multi‑piso Public
	bool canStairBeUsed(const Position& origin, int deltaZ) const;
	Position findFreeTileNear(const Position& center, int maxRadius = 4) const;
	void mcrSafeTeleport(const Position& target);
    Position findFreeTileNear(const Position& center);
	void onWalkComplete() override;
	Player* getTargetPlayer();
	int getEngagement() const { return m_engagement; }
	void setEngagement(int value) { m_engagement = std::clamp(value, 0, 100); }
	uint64_t getPursuitDeadline() const { return m_pursuitDeadline; }
	std::vector<Position> getGlobalDestinations(const Position& pos);
	uint64_t m_lastSuccessfulTeleport = 0;  // timestamp do último teleporte bem‑sucedido

	const std::vector<Position>& getWaypoints() const { return m_waypoints; }
	size_t getWaypointIndex() const { return m_waypointIndex; }
	bool isFollowingWaypoints() const { return m_followingWaypoints; }
	size_t getStairQueueSize() const { return m_stairQueue.size(); }
	const StairTransition* getStairQueueFront() const { return m_stairQueue.empty() ? nullptr : &m_stairQueue.front(); }
	const StairTransition* getStairQueueBack() const { return m_stairQueue.empty() ? nullptr : &m_stairQueue.back(); }

	
	int getFlankingFailCount() const { return m_flankingFailCount; }
	int getProactiveFailCount() const { return m_proactiveFailCount; }
	int getIdleFailCount() const { return m_idleFailCount; }
	uint64_t getLastExplorationScan() const { return m_lastExplorationScan; }
	uint64_t getLastGlobalScanAttempt() const { return m_lastGlobalScanAttempt; }
	uint64_t getLastFlankingAttempt() const { return m_lastFlankingAttempt; }
	uint64_t getLastStairCheck() const { return m_lastStairCheck; }

    bool isPursuingStairs() const { return m_pursuingStairs; }
	bool isUsingGlobalPath() const { return m_followingWaypoints; }
	bool isInOnThinkMCR() const { return m_inOnThinkMCR; }
    const Position& getStairOrigin() const { return m_stairOrigin; }
    const Position& getStairDestination() const { return m_stairDestination; }

	// Real monster name, set on monster creation "createMonsterType(typeName)"
	const std::string &getTypeName() const override;
	const std::string &getNameDescription() const override;
	void setNameDescription(std::string_view nameDescription);
	std::string getDescription(int32_t) override;

	const std::string &getLowerName() const {
		return m_lowerName;
	}

	CreatureType_t getType() const override;

	const Position &getMasterPos() const;
	void setMasterPos(Position pos);

	RaceType_t getRace() const override;
	float getMitigation() const override;
	int32_t getArmor() const override;
	int32_t getDefense(bool = false) const override;

	void addDefense(int32_t defense);

	Faction_t getFaction() const override;

	bool isEnemyFaction(Faction_t faction) const;

	bool isPushable() override;
	bool isAttackable() const override;
	bool canPushItems() const;
	bool canPushCreatures() const;
	bool isRewardBoss() const;
	bool isHostile() const;
	bool isFamiliar() const;
	bool canSeeInvisibility() const override;
	uint32_t getManaCost() const;
	RespawnType getRespawnType() const;
	void setSpawnMonster(const std::shared_ptr<SpawnMonster> &newSpawnMonster);

	double_t getReflectPercent(CombatType_t combatType, bool useCharges = false) const override;
	uint32_t getHealingCombatValue(CombatType_t healingType) const;

	void addReflectElement(CombatType_t combatType, int32_t percent);

	bool canWalkOnFieldType(CombatType_t combatType) const;
	void onAttackedCreatureDisappear(bool isLogout) override;

	void onCreatureAppear(const std::shared_ptr<Creature> &creature, bool isLogin) override;
	void onRemoveCreature(const std::shared_ptr<Creature> &creature, bool isLogout) override;
	void onCreatureMove(const std::shared_ptr<Creature> &creature, const std::shared_ptr<Tile> &newTile, const Position &newPos, const std::shared_ptr<Tile> &oldTile, const Position &oldPos, bool teleport) override;
	void onCreatureSay(const std::shared_ptr<Creature> &creature, SpeakClasses type, const std::string &text) override;
	void onAttackedByPlayer(const std::shared_ptr<Player> &attackerPlayer);
	void onSpawn(const Position &position);

	void drainHealth(const std::shared_ptr<Creature> &attacker, int32_t damage) override;
	void changeHealth(int32_t healthChange, bool sendHealthChange = true) override;
	bool getNextStep(Direction &direction, uint32_t &flags) override;
	void onFollowCreatureComplete(const std::shared_ptr<Creature> &creature) override;

	void onThink(uint32_t interval) override;

	bool challengeCreature(const std::shared_ptr<Creature> &creature, int targetChangeCooldown) override;

	bool changeTargetDistance(int32_t distance, uint32_t duration = 12000);
	bool isChallenged() const;

	std::vector<CreatureIcon> getIcons() const override;

	void setNormalCreatureLight() override;
	bool getCombatValues(int32_t &min, int32_t &max) override;

	void doAttacking(uint32_t interval) override;
	bool hasExtraSwing() override;

	bool searchTarget(TargetSearchType_t searchType = TARGETSEARCH_DEFAULT);
	bool selectTarget(const std::shared_ptr<Creature> &creature);

	auto getTargetList() {
		CreatureVector list;
		list.reserve(targetList.size());

		std::erase_if(targetList, [&list](const std::weak_ptr<Creature> &ref) {
			if (const auto &creature = ref.lock()) {
				list.emplace_back(creature);
				return false;
			}

			return true;
		});

		return list;
	}

	auto getFriendList() {
		CreatureVector list;
		list.reserve(friendList.size());

		std::erase_if(friendList, [&list](const auto &it) {
			if (const auto &creature = it.second.lock()) {
				list.emplace_back(creature);
				return false;
			}

			return true;
		});

		return list;
	}

	bool isTarget(const std::shared_ptr<Creature> &creature);
	bool isFleeing() const;

	void setFatalHoldDuration(int32_t value);

	bool getDistanceStep(const Position &targetPos, Direction &direction, bool flee = false);
	bool isTargetNearby() const;
	bool isIgnoringFieldDamage() const;
	bool israndomStepping() const;
	void setIgnoreFieldDamage(bool ignore);
	bool getIgnoreFieldDamage() const;
	uint16_t getRaceId() const;

	// Hazard system
	bool getHazard() const;
	void setHazard(bool value);

	bool getHazardSystemCrit() const;
	void setHazardSystemCrit(bool value);

	bool getHazardSystemDodge() const;
	void setHazardSystemDodge(bool value);

	bool getHazardSystemDamageBoost() const;
	void setHazardSystemDamageBoost(bool value);
	bool getHazardSystemDefenseBoost() const;
	void setHazardSystemDefenseBoost(bool value);
	// Hazard end

	bool getSoulPit() const;
	void setSoulPit(bool value);
	void setSoulPitStack(uint8_t stack, bool isSummon = false);

	void updateTargetList();
	void clearTargetList();
	void clearFriendList();

	BlockType_t blockHit(const std::shared_ptr<Creature> &attacker, const CombatType_t &combatType, int32_t &damage, bool checkDefense = false, bool checkArmor = false, bool field = false) override;

	static uint32_t monsterAutoID;

	void applyStacks();

	void configureForgeSystem();

	bool canBeForgeMonster() const;

	bool isForgeCreature() const;

	void setForgeMonster(bool forge) const;

	uint16_t getForgeStack() const;

	void setForgeStack(uint16_t stack);

	ForgeClassifications_t getMonsterForgeClassification() const;

	void setMonsterForgeClassification(ForgeClassifications_t classification);

	void setTimeToChangeFiendish(time_t time);

	time_t getTimeToChangeFiendish() const;

	std::shared_ptr<MonsterType> getMonsterType() const;

	void clearFiendishStatus();
	bool canDropLoot() const;

	bool isImmune(ConditionType_t conditionType) const override;
	bool isImmune(CombatType_t combatType) const override;
	void setImmune(bool immune);
	bool isImmune() const;

	float getAttackMultiplier() const;

	float getDefenseMultiplier() const;

	bool isDead() const override;

	void setDead(bool isDead);

	void setCriticalChance(uint16_t chance);
	uint16_t getCriticalChance() const;

	void setCriticalDamage(uint16_t damage);
	uint16_t getCriticalDamage() const;
	bool checkCanApplyCharm(const std::shared_ptr<Player> &player, charmRune_t charmRune) const;

	
	std::shared_ptr<Container> getInventoryContainer() const {
		return m_inventoryContainer;
	}
	void createInventoryContainer(uint16_t size);
	void dropInventoryOnDeath(const std::shared_ptr<Item> &corpse);

protected:
	void onExecuteAsyncTasks() override;

private:
	void onThink_async();
	void onThinkMCR();

	auto getTargetIterator(const std::shared_ptr<Creature> &creature) {
		return std::ranges::find_if(targetList.begin(), targetList.end(), [id = creature->getID()](const std::weak_ptr<Creature> &ref) {
			const auto &target = ref.lock();
			return target && target->getID() == id;
		});
	}

	std::shared_ptr<Container> m_inventoryContainer;

	// --------------------------- MCR Private ---------------------------

	bool m_isMCR = false;   // indica se esta criatura é gerida pelo sistema MCR

	// Perseguição multi‑piso
	bool m_pursuingStairs = false;
	bool m_clearingStairs = false; 
	Position m_stairOrigin;
	Position m_stairDestination;
	bool m_stairIsActive = false;
	int m_stairStuckCount = 0;
	int m_stairTotalCycles = 0;
	int m_stairPathfindFailCount = 0;
	uint32_t m_savedFollowId = 0;
	uint64_t m_pursuitStartTime = 0;
	uint64_t m_stairAttemptStartTime = 0;           // NOVO
	int m_minDistToStair = std::numeric_limits<int>::max();  // NOVO
	uint64_t m_lastDistImprovementTime = 0;         // NOVO
	Position m_homePosition;                // posição onde a perseguição começou
	bool m_returningHome = false;          // true quando está a voltar para casa (sem escadas) 
	bool m_followingSurfaceWaypoint = false;
	size_t m_currentSurfaceWaypointIndex = 0;
	int m_forcedMoveFailCount = 0;
	bool m_globalScanExpanded = false;
	bool m_inOnThinkMCR = false;
    uint64_t m_lastGlobalScanAttempt = 0;
	uint64_t m_lastGpsOptimization = 0;
	uint64_t m_lastFlankingAttempt = 0; 
	int m_surfaceWaypointAttempts = 0;
	uint64_t m_lastExtendedScanAttempt = 0;
	std::unordered_map<Position, uint64_t> m_recentlyFailedStairs;
	static constexpr uint64_t FAILED_STAIR_COOLDOWN = 7500; // 7,5 segundos
	uint64_t m_lastFollowPathAttempt = 0;
	uint64_t m_lastFollowRestoreTime = 0;   // v8.0
	void trySmartFlanking();
	uint64_t m_lastSmartFlankingAttempt = 0;
	void tryUseGlobalMap();
    void clearWaypoints(); 
	bool isPlayerTransition(Player* player, const Position& from, const Position& to);
	std::deque<StairTransition> m_stairQueue;
	std::vector<Position> m_waypoints;
	size_t m_waypointIndex = 0;
	bool m_followingWaypoints = false;

	// Barra de engajamento (0–100)
	int m_engagement = 0;
	// Última posição do mestre (para summons)
	Position m_lastMasterPos;
	// Ticks consecutivos sem ver o alvo
	int m_sightLostTicks = 0;
	static constexpr int SIGHT_LOST_TIMEOUT_TICKS = 5; // 5 segundos (1 tick por segundo)
	// Retaliação durante retorno
	bool m_defensiveRetaliation = false;
	uint64_t m_lastRetaliationTime = 0;
	// Deadline adaptativo da perseguição
	uint64_t m_pursuitDeadline = 0;
	int m_proactiveFailCount = 0;
	int m_returnFailCount = 0;
	int m_totalReturnFails = 0;
	int m_wrongFloorCycles = 0;
	Position m_stuckReturnTarget;
	int m_stuckReturnTargetFails = 0;
	bool m_hasReturnedToSpawn = false;
	uint64_t m_lastRouteRequestTime = 0;
	Position findStairNearReal(const Position& playerPos, int radius = 12);

	int m_leaderDistanceStuckCycles = 0;
	int m_lastDistToLeader = 0;

	// Correção falso stuck (caminhada para escada)
	int m_lastStuckDist = 0;


	// Novos métodos privados
	void mcrEnsureMyTileWalkable();  // garante que a posição actual está walkable no grafo
	void updateEngagement(bool playerVisible, bool damagedPlayer, bool tookDamage);
	uint64_t computePursuitDeadline();
	void handleSummonMasterTeleport(Player* player);
	void resetEngagement();
	void tryProactiveGlobalPursuit();
	void invalidateTileBlocked(const Position& pos);
	void forceInvalidateTileInGraph(const Position& pos);
	void tryAlternativeRouteToLeader();
	void tryExploreArea();
	void tryFlankingRoute();
	uint64_t m_lastExplorationScan = 0;
	Position m_lastUsedStairOrigin;
	Position m_lastUsedStairDest;
	int m_sameStairRepeatCount = 0;
	uint64_t m_lastGlobalPathStart = 0;
	
		// Território / Idle
	Position m_spawnPosition = Position();   // posição original de spawn (imutável)
	bool m_hasSpawnPosition = false;
	uint64_t m_lastIdleWanderTime = 0;       // throttle para deambulação
	uint64_t m_returnWalkStartTime = 0;      // timeout caminhada retorno

	void tryReturnToSpawn();                 // inicia regresso ao spawn
	void tryIdleWander();                    // movimento aleatório perto do spawn
	
	// Throttles para debounce (v9.0)
	uint64_t m_lastCombatCheck = 0;
	uint64_t m_lastStairCheck = 0;
	uint64_t m_lastProactiveCheck = 0;
	uint64_t m_lastIdleCheck = 0;
	uint64_t m_lastGlobalPathStep = 0;

	// Controle de estado
	bool m_wasPursuingStairs = false;
	int m_stairFailStreak = 0;

	int m_flankingFailCount = 0;
	int m_idleFailCount = 0;

	void checkStairPursuit();
	void walkToWaypoint(const Position& target);
	void clearStairPursuit();
	void iniciarRetornoSpawn();
	void processarRetornoSpawn();
	bool isPlayerNearby(int radius = 8);
	void processarRetornoSimples();


	size_t m_nextStairIndex = std::numeric_limits<size_t>::max();
	size_t m_currentTransitionIndex = 0;
	bool m_returningToSpawn = false;
	std::vector<StairTransition> m_returnPath;
	int m_pursuitTimeout = 45;
	bool m_walkingForReturn = false;
	std::shared_ptr<Player> m_persistentTargetPlayer;  // jogador que o hostil está a perseguir


	// --------------------------- Fim do Bloco MCR ---------------------------


	std::unordered_map<uint32_t, std::weak_ptr<Creature>> friendList;
	std::deque<std::weak_ptr<Creature>> targetList;

	time_t timeToChangeFiendish = 0;

	// Forge System
	uint16_t forgeStack = 0;
	ForgeClassifications_t monsterForgeClassification = ForgeClassifications_t::FORGE_NORMAL_MONSTER;

	std::string name;
	std::string m_lowerName;
	std::string nameDescription;

	std::shared_ptr<MonsterType> m_monsterType;
	std::shared_ptr<SpawnMonster> spawnMonster = nullptr;

	int64_t lastMeleeAttack = 0;

	uint16_t totalPlayersOnScreen = 0;

	uint16_t criticalChance = 0;
	uint16_t criticalDamage = 0;

	uint32_t attackTicks = 0;
	uint32_t targetChangeTicks = 0;
	uint32_t defenseTicks = 0;
	uint32_t yellTicks = 0;
	uint32_t soundTicks = 0;

	int32_t minCombatValue = 0;
	int32_t maxCombatValue = 0;
	int32_t m_targetChangeCooldown = 0;
	int32_t fatalHoldDuration = 0;
	int32_t challengeFocusDuration = 0;
	int32_t stepDuration = 0;
	int32_t targetDistance = 1;
	int32_t challengeMeleeDuration = 0;
	int32_t runAwayHealth = 0;
	int32_t m_defense = 0;

	std::unordered_map<CombatType_t, int32_t> m_reflectElementMap;

	std::vector<spellBlock_t> attackSpells;
	std::vector<spellBlock_t> defenseSpells;

	Position masterPos;

	bool canFlee = false;
	bool isWalkingBack = false;
	bool isIdle = true;
	bool extraMeleeAttack = false;
	bool randomStepping = false;
	bool ignoreFieldDamage = false;

	bool hazard = false;
	bool hazardCrit = false;
	bool hazardDodge = false;
	bool hazardDamageBoost = false;
	bool hazardDefenseBoost = false;

	bool soulPit = false;

	bool m_isDead = false;
	bool m_isImmune = false;

	std::string m_customName;

	void onCreatureEnter(const std::shared_ptr<Creature> &creature);
	void onCreatureLeave(const std::shared_ptr<Creature> &creature);
	void onCreatureFound(const std::shared_ptr<Creature> &creature, bool pushFront = false);

	void updateLookDirection();

	void addFriend(const std::shared_ptr<Creature> &creature);
	void removeFriend(const std::shared_ptr<Creature> &creature);
	bool addTarget(const std::shared_ptr<Creature> &creature, bool pushFront = false);
	bool removeTarget(const std::shared_ptr<Creature> &creature);

	void death(const std::shared_ptr<Creature> &lastHitCreature) override;
	std::shared_ptr<Item> getCorpse(const std::shared_ptr<Creature> &lastHitCreature, const std::shared_ptr<Creature> &mostDamageCreature) override;

	void setIdle(bool idle);
	void updateIdleStatus();
	bool getIdleStatus() const;

	void onAddCondition(ConditionType_t type) override;
	void onEndCondition(ConditionType_t type) override;

	bool canUseAttack(const Position &pos, const std::shared_ptr<Creature> &target) const;
	bool canUseSpell(const Position &pos, const Position &targetPos, const spellBlock_t &sb, uint32_t interval, bool &inRange, bool &resetTicks);
	bool getRandomStep(const Position &creaturePos, Direction &direction);
	bool getDanceStep(const Position &creaturePos, Direction &direction, bool keepAttack = true, bool keepDistance = true);
	bool isInSpawnLocation() const;
	bool isInSpawnRange(const Position &pos) const;
	bool canWalkTo(Position pos, Direction direction);

	static bool pushItem(const std::shared_ptr<Item> &item, const Direction &nextDirection);
	/**
	 * @brief Attempts to push or remove movable blocking items stacked on a tile in a given direction.
	 *
	 * Processes the tile's "down" items (bottom-to-top) and, for each movable item that blocks pathing or is solid,
	 * attempts to push it into the adjacent tile in nextDirection or, failing that, removes the item.
	 * Will not operate on house tiles or when the tile has no items. When one or more items are removed, a puff
	 * visual effect is produced at the tile position.
	 *
	 * Behavior specifics:
	 * - Only items that are movable, can be moved, and currently reside on the provided tile are considered.
	 * - Stops after successfully pushing up to 20 items and removing up to 10 items (these counters are independent).
	 *
	 * @param tile Shared pointer to the tile whose items should be processed.
	 * @param nextDirection Direction in which items should be pushed.
	 */
	static void pushItems(const std::shared_ptr<Tile> &tile, const Direction &nextDirection);
	static bool pushCreature(const std::shared_ptr<Creature> &creature);
	static void pushCreatures(const std::shared_ptr<Tile> &tile);

	void onThinkTarget(uint32_t interval);
	void onThinkYell(uint32_t interval);
	void onThinkDefense(uint32_t interval);
	void onThinkSound(uint32_t interval);

	bool isFriend(const std::shared_ptr<Creature> &creature) const;
	bool isOpponent(const std::shared_ptr<Creature> &creature) const;

	uint64_t getLostExperience() const override;
	uint16_t getLookCorpse() const override;
	void dropLoot(const std::shared_ptr<Container> &corpse, const std::shared_ptr<Creature> &lastHitCreature) override;
	void getPathSearchParams(const std::shared_ptr<Creature> &creature, FindPathParams &fpp) override;

	friend class MonsterFunctions;
	friend class Map;

	static std::vector<std::pair<int8_t, int8_t>> getPushItemLocationOptions(const Direction &direction);

	void doWalkBack(uint32_t &flags, Direction &nextDirection, bool &result);
	void doFollowCreature(uint32_t &flags, Direction &nextDirection, bool &result);
	void doRandomStep(Direction &nextDirection, bool &result);

	void onConditionStatusChange(ConditionType_t type);
};
