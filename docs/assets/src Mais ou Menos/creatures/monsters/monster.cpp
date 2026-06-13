/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (\251) 2019?present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "creatures/monsters/monster.hpp"

#include "config/configmanager.hpp"
#include "creatures/combat/spells.hpp"
#include "creatures/monsters/monsters.hpp"
#include "creatures/players/player.hpp"
#include "game/game.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "items/tile.hpp"
#include "lua/callbacks/events_callbacks.hpp"
#include "map/spectators.hpp"
#include "io/iobestiary.hpp"
#include "game/movement/teleport.hpp"
#include "mcr/spa/global_monster_map.hpp"
#include "utils/tools.hpp"              // getCurrentTimeMs()

int32_t Monster::despawnRange;
int32_t Monster::despawnRadius;

uint32_t Monster::monsterAutoID = 0x50000001;

std::shared_ptr<Monster> Monster::createMonster(const std::string &name) {
	const auto &mType = g_monsters().getMonsterType(name);
	if (!mType) {
		return nullptr;
	}
	return std::make_shared<Monster>(mType);
}

Monster::Monster(const std::shared_ptr<MonsterType> &mType) :
    m_lowerName(asLowerCaseString(toLatin1(mType->name))),
    nameDescription(asLowerCaseString(toLatin1(mType->nameDescription))),
    m_monsterType(mType) {
	defaultOutfit = mType->info.outfit;
	currentOutfit = mType->info.outfit;
	skull = mType->info.skull;
	health = mType->info.health * mType->getHealthMultiplier();
	healthMax = mType->info.healthMax * mType->getHealthMultiplier();
	runAwayHealth = mType->info.runAwayHealth * mType->getHealthMultiplier();
	baseSpeed = mType->getBaseSpeed();
	internalLight = mType->info.light;
	hiddenHealth = mType->info.hiddenHealth;
	targetDistance = mType->info.targetDistance;
	attackSpells = mType->info.attackSpells;
	defenseSpells = mType->info.defenseSpells;

	// Register creature events
	for (const std::string &scriptName : mType->info.scripts) {
		if (!registerCreatureEvent(scriptName)) {
			g_logger().warn("[Monster::Monster] - "
			                "Nome do evento desconhecido: {}",
			                scriptName);
		}
	}
}

std::shared_ptr<Monster> Monster::getMonster() {
	return static_self_cast<Monster>();
}

std::shared_ptr<const Monster> Monster::getMonster() const {
	return static_self_cast<Monster>();
}

void Monster::setID() {
	if (id == 0) {
		id = monsterAutoID++;
	}
}

void Monster::addList() {
	g_game().addMonster(static_self_cast<Monster>());
}

void Monster::removeList() {
	g_game().removeMonster(static_self_cast<Monster>());
}

const std::string &Monster::getName() const {
	if (name.empty()) {
		return m_monsterType->name;
	}
	return name;
}

void Monster::setName(const std::string &name) {
    if (getName() == name) {
        return;
    }
    this->name = toLatin1(name); // <-- Garantir que o nome fica em Latin‑1

	// NOTE: Due to how client caches known creatures,
	// it is not feasible to send creature update to everyone that has ever met it
	auto spectators = Spectators().find<Player>(position, true);
	for (const auto &spectator : spectators) {
		if (const auto &tmpPlayer = spectator->getPlayer()) {
			tmpPlayer->sendUpdateTileCreature(static_self_cast<Monster>());
		}
	}
}

// Real monster name, set on monster creation "createMonsterType(typeName)"

const std::string &Monster::getTypeName() const {
	return m_monsterType->typeName;
}

const std::string &Monster::getNameDescription() const {
	if (nameDescription.empty()) {
		return m_monsterType->nameDescription;
	}
	return nameDescription;
}

void Monster::setNameDescription(std::string_view newNameDescription) {
	this->nameDescription = newNameDescription;
}

std::string Monster::getDescription(int32_t) {
	return nameDescription + '.';
}

CreatureType_t Monster::getType() const {
	return CREATURETYPE_MONSTER;
}

const Position &Monster::getMasterPos() const {
	return masterPos;
}

void Monster::setMasterPos(Position pos) {
	masterPos = pos;
}

bool Monster::canWalkOnFieldType(CombatType_t combatType) const {
	switch (combatType) {
		case COMBAT_ENERGYDAMAGE:
			return m_monsterType->info.canWalkOnEnergy;
		case COMBAT_FIREDAMAGE:
			return m_monsterType->info.canWalkOnFire;
		case COMBAT_EARTHDAMAGE:
			return m_monsterType->info.canWalkOnPoison;
		default:
			return true;
	}
}

double_t Monster::getReflectPercent(CombatType_t reflectType, bool useCharges) const {
	// Monster type reflect
	auto result = Creature::getReflectPercent(reflectType, useCharges);
	if (result != 0) {
		g_logger().debug("[{}] antes do mtype reflete o elemento {}, porcentagem {}", __FUNCTION__, fmt::underlying(reflectType), result);
	}
	auto it = m_monsterType->info.reflectMap.find(reflectType);
	if (it != m_monsterType->info.reflectMap.end()) {
		result += it->second;
	}

	if (result != 0) {
		g_logger().debug("[{}] ap\363s mtype refletir elemento {}, porcentagem {}", __FUNCTION__, fmt::underlying(reflectType), result);
	}

	// Monster reflect
	auto monsterReflectIt = m_reflectElementMap.find(reflectType);
	if (monsterReflectIt != m_reflectElementMap.end()) {
		result += monsterReflectIt->second;
	}

	if (result != 0) {
		g_logger().debug("[{}] (final) ap\363s o monstro refletir o elemento {}, porcentagem {}", __FUNCTION__, fmt::underlying(reflectType), result);
	}

	return result;
}

void Monster::addReflectElement(CombatType_t combatType, int32_t percent) {
	g_logger().debug("[{}] adicionado elemento de reflex\343o {}, porcentagem {}", __FUNCTION__, fmt::underlying(combatType), percent);
	m_reflectElementMap[combatType] += percent;
}

int32_t Monster::getDefense(bool) const {
	auto mtypeDefense = m_monsterType->info.defense;
	if (mtypeDefense != 0) {
		g_logger().trace("[{}] defesa antiga {}", __FUNCTION__, mtypeDefense);
	}
	mtypeDefense += m_defense;
	if (mtypeDefense != 0) {
		g_logger().trace("[{}] nova defesa {}", __FUNCTION__, mtypeDefense);
	}
	return mtypeDefense * getDefenseMultiplier();
}

void Monster::addDefense(int32_t defense) {
	g_logger().trace("[{}] adicionando defesa {}", __FUNCTION__, defense);
	m_defense += defense;
	g_logger().trace("[{}] nova defesa {}", __FUNCTION__, m_defense);
}

Faction_t Monster::getFaction() const {
	if (const auto &master = getMaster()) {
		return master->getFaction();
	}
	return m_monsterType->info.faction;
}

bool Monster::isEnemyFaction(Faction_t faction) const {
	const auto &master = getMaster();
	if (master && master->getMonster()) {
		return master->getMonster()->isEnemyFaction(faction);
	}
	return m_monsterType->info.enemyFactions.empty() ? false : m_monsterType->info.enemyFactions.contains(faction);
}

bool Monster::isPushable() {
	return m_monsterType->info.pushable && baseSpeed != 0;
}

bool Monster::isAttackable() const {
	return m_monsterType->info.isAttackable;
}

bool Monster::canPushItems() const {
	return m_monsterType->info.canPushItems;
}

bool Monster::canPushCreatures() const {
	return m_monsterType->info.canPushCreatures;
}

bool Monster::isRewardBoss() const {
	return m_monsterType->info.isRewardBoss;
}

bool Monster::isHostile() const {
	return m_monsterType->info.isHostile;
}

bool Monster::isFamiliar() const {
	return m_monsterType->info.isFamiliar;
}

bool Monster::canSeeInvisibility() const {
	return isImmune(CONDITION_INVISIBLE);
}

void Monster::setCriticalDamage(uint16_t damage) {
	criticalDamage = damage;
}

uint16_t Monster::getCriticalDamage() const {
	return criticalDamage;
}

void Monster::setCriticalChance(uint16_t chance) {
	criticalChance = chance;
}

uint16_t Monster::getCriticalChance() const {
	return m_monsterType->info.critChance + criticalChance;
}

uint32_t Monster::getManaCost() const {
	return m_monsterType->info.manaCost;
}

RespawnType Monster::getRespawnType() const {
	return m_monsterType->info.respawnType;
}

void Monster::setSpawnMonster(const std::shared_ptr<SpawnMonster> &newSpawnMonster) {
	this->spawnMonster = newSpawnMonster;
}

uint32_t Monster::getHealingCombatValue(CombatType_t healingType) const {
	auto it = m_monsterType->info.healingMap.find(healingType);
	if (it != m_monsterType->info.healingMap.end()) {
		return it->second;
	}
	return 0;
}

void Monster::onAttackedCreatureDisappear(bool) {
	attackTicks = 0;
	extraMeleeAttack = true;
}

void Monster::onCreatureAppear(const std::shared_ptr<Creature> &creature, bool isLogin) {
	Creature::onCreatureAppear(creature, isLogin);

	if (m_monsterType->info.creatureAppearEvent != -1) {
		// onCreatureAppear(self, creature)
		LuaScriptInterface* scriptInterface = m_monsterType->info.scriptInterface;
		if (!LuaScriptInterface::reserveScriptEnv()) {
			g_logger().error("[Monster::onCreatureAppear - Monster {} creature {}] "
			                 "Estouro de pilha de chamadas. Muitas chamadas de script lua sendo aninhadas.",
			                 getName(), creature->getName());
			return;
		}

		ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
		env->setScriptId(m_monsterType->info.creatureAppearEvent, scriptInterface);

		lua_State* L = scriptInterface->getLuaState();
		scriptInterface->pushFunction(m_monsterType->info.creatureAppearEvent);

		LuaScriptInterface::pushUserdata<Monster>(L, getMonster());
		LuaScriptInterface::setMetatable(L, -1, "Monster");

		LuaScriptInterface::pushUserdata<Creature>(L, creature);
		LuaScriptInterface::setCreatureMetatable(L, -1, creature);

		if (scriptInterface->callFunction(2)) {
			return;
		}
	}

	if (creature.get() == this) {
		updateTargetList();
		updateIdleStatus();
	} else {
		addAsyncTask([this, creature] {
			onCreatureEnter(creature);
		});
	}
}

void Monster::onRemoveCreature(const std::shared_ptr<Creature> &creature, bool isLogout) {
	Creature::onRemoveCreature(creature, isLogout);

	if (m_monsterType->info.creatureDisappearEvent != -1) {
		// onCreatureDisappear(self, creature)
		LuaScriptInterface* scriptInterface = m_monsterType->info.scriptInterface;
		if (!LuaScriptInterface::reserveScriptEnv()) {
			g_logger().error("[Monster::onCreatureDisappear - Monster {} creature {}] "
			                 "Estouro de pilha de chamadas. Muitas chamadas de script lua sendo aninhadas.",
			                 getName(), creature->getName());
			return;
		}

		ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
		env->setScriptId(m_monsterType->info.creatureDisappearEvent, scriptInterface);

		lua_State* L = scriptInterface->getLuaState();
		scriptInterface->pushFunction(m_monsterType->info.creatureDisappearEvent);

		LuaScriptInterface::pushUserdata<Monster>(L, getMonster());
		LuaScriptInterface::setMetatable(L, -1, "Monster");

		LuaScriptInterface::pushUserdata<Creature>(L, creature);
		LuaScriptInterface::setCreatureMetatable(L, -1, creature);

		if (scriptInterface->callFunction(2)) {
			return;
		}
	}

	if (creature.get() == this) {
		if (spawnMonster) {
			spawnMonster->startSpawnMonsterCheck();
		}

		setIdle(true);
	} else {
		addAsyncTask([this, creature] {
			onCreatureLeave(creature);
		});
	}
}

void Monster::onCreatureMove(const std::shared_ptr<Creature> &creature, const std::shared_ptr<Tile> &newTile, const Position &newPos, const std::shared_ptr<Tile> &oldTile, const Position &oldPos, bool teleport) {
    Creature::onCreatureMove(creature, newTile, newPos, oldTile, oldPos, teleport);

    // ============================================================
    // MCR: detetar conclusão da perseguição multi-piso e consumir transição
    // ============================================================
	if (m_pursuingStairs) {
		Position myPos = getPosition();
		int dist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
		m_stairTotalCycles++;

		// Resumo periódico a cada 5 segundos (apenas aqui, com dist definido)
		uint64_t deadlineRemaining = (m_pursuitDeadline > 0) ? (m_pursuitDeadline - getCurrentTimeMs()) : 0;
        if (newPos.z != oldPos.z) {
            if (!isSummon()) {
                m_returnPath.push_back({m_stairOrigin, m_stairDestination, static_cast<uint64_t>(getCurrentTimeMs()), m_stairIsActive});
            }
            m_nextStairIndex = m_currentTransitionIndex + 1;
            g_logger().info("[MCR-STAIR] {} transição atingida, índice avançado para {}.", getName(), m_nextStairIndex);
            g_logger().info("[MCR-STAIR] {} alterou o piso! A concluir perseguição.", getName());
            clearStairPursuit();
        }
    }

    // Código original do evento de script (mantido na íntegra)
    if (m_monsterType->info.creatureMoveEvent != -1) {
        // onCreatureMove(self, creature, oldPosition, newPosition)
        LuaScriptInterface* scriptInterface = m_monsterType->info.scriptInterface;
        if (!LuaScriptInterface::reserveScriptEnv()) {
            g_logger().error("[Monster::onCreatureMove - Monster {} creature {}] "
                             "Estouro de pilha de chamadas. Muitas chamadas de script lua sendo aninhadas.",
                             getName(), creature->getName());
            return;
        }

        ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
        env->setScriptId(m_monsterType->info.creatureMoveEvent, scriptInterface);

        lua_State* L = scriptInterface->getLuaState();
        scriptInterface->pushFunction(m_monsterType->info.creatureMoveEvent);

        LuaScriptInterface::pushUserdata<Monster>(L, getMonster());
        LuaScriptInterface::setMetatable(L, -1, "Monster");

        LuaScriptInterface::pushUserdata<Creature>(L, creature);
        LuaScriptInterface::setCreatureMetatable(L, -1, creature);

        LuaScriptInterface::pushPosition(L, oldPos);
        LuaScriptInterface::pushPosition(L, newPos);

        if (scriptInterface->callFunction(4)) {
            return;
        }
    }

    if (creature.get() == this) {
        updateTargetList();
        updateIdleStatus();
    } else {
        auto action = [this, newPos, oldPos, creature] {
            bool canSeeNewPos = canSee(newPos);
            bool canSeeOldPos = canSee(oldPos);

            if (canSeeNewPos && !canSeeOldPos) {
                onCreatureEnter(creature);
            } else if (!canSeeNewPos && canSeeOldPos) {
                onCreatureLeave(creature);
            }

            updateIdleStatus();

            if (!isSummon()) {
                if (const auto &followCreature = getFollowCreature()) {
                    const Position &followPosition = followCreature->getPosition();
                    const Position &pos = getPosition();

                    int32_t offset_x = Position::getDistanceX(followPosition, pos);
                    int32_t offset_y = Position::getDistanceY(followPosition, pos);
                    if ((offset_x > 1 || offset_y > 1) && m_monsterType->info.changeTargetChance > 0) {
                        Direction dir = getDirectionTo(pos, followPosition);
                        const auto &checkPosition = getNextPosition(dir, pos);

                        if (const auto &nextTile = g_game().map.getTile(checkPosition)) {
                            const auto &topCreature = nextTile->getTopCreature();
                            if (followCreature != topCreature && isOpponent(topCreature)) {
                                selectTarget(topCreature);
                            }
                        }
                    }
                } else if (isOpponent(creature)) {
                    selectTarget(creature);
                }
            }
        };

        if (g_dispatcher().context().getGroup() == TaskGroup::Walk) {
            addAsyncTask(std::move(action));
        } else {
            action();
        }
    }
}

void Monster::onCreatureSay(const std::shared_ptr<Creature> &creature, SpeakClasses type, const std::string &text) {
	Creature::onCreatureSay(creature, type, text);

	if (m_monsterType->info.creatureSayEvent != -1) {
		// onCreatureSay(self, creature, type, message)
		LuaScriptInterface* scriptInterface = m_monsterType->info.scriptInterface;
		if (!LuaScriptInterface::reserveScriptEnv()) {
			g_logger().error("Monstro {} criatura {}] Chama o estouro de pilha. Muitas luas"
			                 "chamadas de script sendo aninhadas.",
			                 getName(), creature->getName());
			return;
		}

		ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
		env->setScriptId(m_monsterType->info.creatureSayEvent, scriptInterface);

		lua_State* L = scriptInterface->getLuaState();
		scriptInterface->pushFunction(m_monsterType->info.creatureSayEvent);

		LuaScriptInterface::pushUserdata<Monster>(L, getMonster());
		LuaScriptInterface::setMetatable(L, -1, "Monster");

		LuaScriptInterface::pushUserdata<Creature>(L, creature);
		LuaScriptInterface::setCreatureMetatable(L, -1, creature);

		lua_pushnumber(L, type);
		LuaScriptInterface::pushString(L, text);

		scriptInterface->callVoidFunction(4);
	}
}

void Monster::onAttackedByPlayer(const std::shared_ptr<Player> &attackerPlayer) {
    // ═══ CANCELA QUALQUER PERSEGUIÇÃO OU RETORNO IMEDIATAMENTE ═══
    clearStairPursuit();
    clearWaypoints();
    m_returningToSpawn = false;
    m_returningHome = false;
    m_walkingForReturn = false;
    m_returnPath.clear();
    m_hasReturnedToSpawn = false;
    m_lastProactiveCheck = 0;  // permite ação proativa imediata no próximo ciclo

    // ================================================================
    // MCR – Atualizar engajamento e retaliação
    // ================================================================
    m_engagement = std::min(100, m_engagement + 2);

    // Se o monstro estiver a regressar ao spawn/casa, ativa a defesa pessoal
    if (m_returningToSpawn || m_returningHome) {
        m_defensiveRetaliation = true;
        m_lastRetaliationTime = getCurrentTimeMs();
        setAttackedCreature(attackerPlayer);
    }

    // ================================================================
    // Código original do evento de script (mantido integralmente)
    // ================================================================
    if (m_monsterType->info.monsterAttackedByPlayerEvent != -1) {
        LuaScriptInterface* scriptInterface = m_monsterType->info.scriptInterface;
        if (!scriptInterface->reserveScriptEnv()) {
            g_logger().error("Monstro {} criatura {}] Chama o estouro de pilha. Muitas luas "
                             "chamadas de script sendo aninhadas.",
                             getName(), this->getName());
            return;
        }
        ScriptEnvironment* env = scriptInterface->getScriptEnv();
        env->setScriptId(m_monsterType->info.monsterAttackedByPlayerEvent, scriptInterface);

        lua_State* L = scriptInterface->getLuaState();
        scriptInterface->pushFunction(m_monsterType->info.monsterAttackedByPlayerEvent);

        LuaScriptInterface::pushUserdata<Monster>(L, getMonster());
        LuaScriptInterface::setMetatable(L, -1, "Monster");

        LuaScriptInterface::pushUserdata<Player>(L, attackerPlayer);
        LuaScriptInterface::setMetatable(L, -1, "Player");

        scriptInterface->callVoidFunction(2);
    }
}

void Monster::onSpawn(const Position &position) {
	if (m_monsterType->info.spawnEvent != -1) {
		// onSpawn(self, spawnPosition)
		LuaScriptInterface* scriptInterface = m_monsterType->info.scriptInterface;
		if (!scriptInterface->reserveScriptEnv()) {
			g_logger().error("Monstro {} criatura {}] Chama o estouro de pilha. Muitas luas "
			                 "chamadas de script sendo aninhadas.",
			                 getName(), this->getName());
			return;
		}

		ScriptEnvironment* env = scriptInterface->getScriptEnv();
		env->setScriptId(m_monsterType->info.spawnEvent, scriptInterface);

		lua_State* L = scriptInterface->getLuaState();
		scriptInterface->pushFunction(m_monsterType->info.spawnEvent);

		LuaScriptInterface::pushUserdata<Monster>(L, getMonster());
		LuaScriptInterface::setMetatable(L, -1, "Monster");
		LuaScriptInterface::pushPosition(L, position);

		scriptInterface->callVoidFunction(2);
	}
}

void Monster::addFriend(const std::shared_ptr<Creature> &creature) {
	if (creature == getMonster()) {
		g_logger().error("[{}]: adicionar criatura \351 igual a monstro", __FUNCTION__);
		return;
	}

	assert(creature != getMonster());
	friendList.try_emplace(creature->getID(), creature);
}

void Monster::removeFriend(const std::shared_ptr<Creature> &creature) {
	std::erase_if(friendList, [id = creature->getID()](const auto &it) {
		const auto &target = it.second.lock();
		return !target || target->getID() == id;
	});
}

bool Monster::addTarget(const std::shared_ptr<Creature> &creature, bool pushFront /* = false*/) {
	if (creature == getMonster()) {
		g_logger().error("[{}]: adicionar criatura \351 igual a monstro", __FUNCTION__);
		return false;
	}

	assert(creature != getMonster());

	auto it = getTargetIterator(creature);
	if (it != targetList.end()) {
		return false;
	}

	if (pushFront) {
		targetList.emplace_front(creature);
	} else {
		targetList.emplace_back(creature);
	}

	const auto &master = getMaster();
	if (!master && getFaction() != FACTION_DEFAULT && creature->getPlayer()) {
		totalPlayersOnScreen++;
	}

	return true;
}

bool Monster::removeTarget(const std::shared_ptr<Creature> &creature) {
	if (!creature) {
		return false;
	}

	auto it = getTargetIterator(creature);
	if (it == targetList.end()) {
		return false;
	}

	const auto &master = getMaster();
	if (!master && getFaction() != FACTION_DEFAULT && creature->getPlayer()) {
		totalPlayersOnScreen--;
	}

	if (auto shared = it->lock()) {
		targetList.erase(it);
	} else {
		return false;
	}

	return true;
}

void Monster::updateTargetList() {
	if (!g_dispatcher().context().isAsync()) {
		setAsyncTaskFlag(UpdateTargetList, true);
		return;
	}

	std::erase_if(friendList, [this](const auto &it) {
		const auto &target = it.second.lock();
		return !target || target->getHealth() <= 0 || !canSee(target->getPosition());
	});

	std::erase_if(targetList, [this](const std::weak_ptr<Creature> &ref) {
		const auto &target = ref.lock();
		return !target || target->getHealth() <= 0 || !canSee(target->getPosition());
	});

	for (const auto &spectator : Spectators().find<Creature>(position, true, 0, 0, 0, 0, false)) {
		if (spectator.get() != this && canSee(spectator->getPosition())) {
			onCreatureFound(spectator);
		}
	}
}

void Monster::clearTargetList() {
	targetList.clear();
}

void Monster::clearFriendList() {
	friendList.clear();
}

void Monster::onCreatureFound(const std::shared_ptr<Creature> &creature, bool pushFront /* = false*/) {
	if (isFriend(creature)) {
		addFriend(creature);
	}

	if (isOpponent(creature)) {
		addTarget(creature, pushFront);
	}

	updateIdleStatus();
}

void Monster::onCreatureEnter(const std::shared_ptr<Creature> &creature) {
	onCreatureFound(creature, true);
}

bool Monster::isFriend(const std::shared_ptr<Creature> &creature) const {
	const auto &master = getMaster();
	const auto &masterPlayer = master ? master->getPlayer() : nullptr;
	if (isSummon() && masterPlayer) {
		auto tmpPlayer = creature->getPlayer();
		if (!tmpPlayer) {
			const auto &creatureMaster = creature->getMaster();
			if (creatureMaster && creatureMaster->getPlayer()) {
				tmpPlayer = creatureMaster->getPlayer();
			}
		}

		if (tmpPlayer && (tmpPlayer == master || masterPlayer->isPartner(tmpPlayer))) {
			return true;
		}
	}

	return creature->getMonster() && !creature->isSummon();
}

bool Monster::isOpponent(const std::shared_ptr<Creature> &creature) const {
	if (!creature) {
		return false;
	}

	const auto &master = getMaster();
	const auto &masterPlayer = master ? master->getPlayer() : nullptr;
	if (isSummon() && masterPlayer) {
		return creature != master;
	}

	const auto &player = creature ? creature->getPlayer() : nullptr;
	if (player && player->hasFlag(PlayerFlags_t::IgnoredByMonsters)) {
		return false;
	}

	if (getFaction() != FACTION_DEFAULT) {
		return isEnemyFaction(creature->getFaction()) || creature->getFaction() == FACTION_PLAYER;
	}

	const auto &creatureMaster = creature->getMaster();
	const auto &creaturePlayer = creatureMaster ? creatureMaster->getPlayer() : nullptr;
	if (player || creaturePlayer) {
		return true;
	}

	return false;
}

uint64_t Monster::getLostExperience() const {
	float extraExperience = forgeStack <= 15 ? (forgeStack + 10) / 10 : 28;
	return skillLoss ? static_cast<uint64_t>(std::round(m_monsterType->info.experience * extraExperience)) : 0;
}

uint16_t Monster::getLookCorpse() const {
	return m_monsterType->info.lookcorpse;
}

void Monster::onCreatureLeave(const std::shared_ptr<Creature> &creature) {
	// update friendList
	if (isFriend(creature)) {
		removeFriend(creature);
	}

	// update targetList
	if (isOpponent(creature)) {
		removeTarget(creature);
		if (targetList.empty()) {
			updateIdleStatus();
		}
	}
}

bool Monster::searchTarget(TargetSearchType_t searchType /*= TARGETSEARCH_DEFAULT*/) {
	if (searchType == TARGETSEARCH_DEFAULT) {
		int32_t rnd = uniform_random(1, 100);

		searchType = TARGETSEARCH_NEAREST;

		int32_t sum = this->m_monsterType->info.strategiesTargetNearest;
		if (rnd > sum) {
			searchType = TARGETSEARCH_HP;
			sum += this->m_monsterType->info.strategiesTargetHealth;

			if (rnd > sum) {
				searchType = TARGETSEARCH_DAMAGE;
				sum += this->m_monsterType->info.strategiesTargetDamage;
				if (rnd > sum) {
					searchType = TARGETSEARCH_RANDOM;
				}
			}
		}
	}

	std::vector<std::shared_ptr<Creature>> resultList;
	const Position &myPos = getPosition();

	for (const auto &cref : targetList) {
		const auto &creature = cref.lock();
		if (creature && isTarget(creature)) {
			if ((static_self_cast<Monster>()->targetDistance == 1) || canUseAttack(myPos, creature)) {
				resultList.emplace_back(creature);
			}
		}
	}

	if (resultList.empty()) {
		return false;
	}

	std::shared_ptr<Creature> getTarget = nullptr;

	switch (searchType) {
		case TARGETSEARCH_NEAREST: {
			getTarget = nullptr;
			if (!resultList.empty()) {
				auto it = resultList.begin();
				getTarget = *it;

				if (++it != resultList.end()) {
					const Position &targetPosition = getTarget->getPosition();
					int32_t minRange = std::max<int32_t>(Position::getDistanceX(myPos, targetPosition), Position::getDistanceY(myPos, targetPosition));
					int32_t factionOffset = static_cast<int32_t>(getTarget->getFaction()) * 100;
					do {
						const Position &pos = (*it)->getPosition();

						int32_t distance = std::max<int32_t>(Position::getDistanceX(myPos, pos), Position::getDistanceY(myPos, pos)) + factionOffset;
						if (distance < minRange) {
							getTarget = *it;
							minRange = distance;
						}
					} while (++it != resultList.end());
				}
			} else {
				int32_t minRange = std::numeric_limits<int32_t>::max();
				for (const auto &creature : getTargetList()) {
					if (!isTarget(creature)) {
						continue;
					}

					const Position &pos = creature->getPosition();
					int32_t factionOffset = static_cast<int32_t>(getTarget->getFaction()) * 100;
					int32_t distance = std::max<int32_t>(Position::getDistanceX(myPos, pos), Position::getDistanceY(myPos, pos)) + factionOffset;
					if (distance < minRange) {
						getTarget = creature;
						minRange = distance;
					}
				}
			}

			if (getTarget && selectTarget(getTarget)) {
				return true;
			}
			break;
		}
		case TARGETSEARCH_HP: {
			getTarget = nullptr;
			if (!resultList.empty()) {
				auto it = resultList.begin();
				getTarget = *it;
				if (++it != resultList.end()) {
					int32_t factionOffset = static_cast<int32_t>(getTarget->getFaction()) * 100000;
					int32_t minHp = getTarget->getHealth() + factionOffset;
					do {
						auto hp = (*it)->getHealth() + factionOffset;
						factionOffset = static_cast<int32_t>((*it)->getFaction()) * 100000;
						if (hp < minHp) {
							getTarget = *it;
							minHp = hp;
						}
					} while (++it != resultList.end());
				}
			}
			if (getTarget && selectTarget(getTarget)) {
				return true;
			}
			break;
		}
		case TARGETSEARCH_DAMAGE: {
			getTarget = nullptr;
			if (!resultList.empty()) {
				auto it = resultList.begin();
				getTarget = *it;
				if (++it != resultList.end()) {
					int32_t mostDamage = 0;
					do {
						int32_t factionOffset = static_cast<int32_t>((*it)->getFaction()) * 100000;
						const auto dmg = damageMap.find((*it)->getID());
						if (dmg != damageMap.end() && dmg->second.total + factionOffset > mostDamage) {
							mostDamage = dmg->second.total;
							getTarget = *it;
						}
					} while (++it != resultList.end());
				}
			}
			if (getTarget && selectTarget(getTarget)) {
				return true;
			}
			break;
		}
		case TARGETSEARCH_RANDOM:
		default: {
			if (!resultList.empty()) {
				auto it = resultList.begin();
				std::advance(it, uniform_random(0, resultList.size() - 1));
				return selectTarget(*it);
			}
			break;
		}
	}

	// lets just pick the first target in the list
	return std::ranges::any_of(getTargetList(), [this](const std::shared_ptr<Creature> &creature) {
		return selectTarget(creature);
	});
}

void Monster::onFollowCreatureComplete(const std::shared_ptr<Creature> &creature) {
	if (removeTarget(creature) && (hasFollowPath || !isSummon())) {
		addTarget(creature, hasFollowPath);
	}
}

RaceType_t Monster::getRace() const {
	return m_monsterType->info.race;
}

float Monster::getMitigation() const {
	float mitigation = m_monsterType->info.mitigation * getDefenseMultiplier();
	if (g_configManager().getBoolean(DISABLE_MONSTER_ARMOR)) {
		mitigation += std::ceil(static_cast<float>(getDefense() + getArmor()) / 100.f) * getDefenseMultiplier() * 2.f;
	}
	return std::min<float>(mitigation, 30.f);
}

int32_t Monster::getArmor() const {
	return m_monsterType->info.armor * getDefenseMultiplier();
}

BlockType_t Monster::blockHit(const std::shared_ptr<Creature> &attacker, const CombatType_t &combatType, int32_t &damage, bool checkDefense /* = false*/, bool checkArmor /* = false*/, bool /* field = false */) {
	BlockType_t blockType = Creature::blockHit(attacker, combatType, damage, checkDefense, checkArmor);

	if (damage != 0) {
		int32_t elementMod = 0;
		auto it = m_monsterType->info.elementMap.find(combatType);
		if (it != m_monsterType->info.elementMap.end()) {
			elementMod = it->second;
		}

		// Wheel of destiny
		const auto &player = attacker ? attacker->getPlayer() : nullptr;
		if (player && player->wheel().getInstant("Ballistic Mastery")) {
			elementMod -= player->wheel().checkElementSensitiveReduction(combatType);
		}

		if (elementMod != 0) {
			damage = static_cast<int32_t>(std::round(damage * ((100 - elementMod) / 100.)));
			if (damage <= 0) {
				damage = 0;
				blockType = BLOCK_ARMOR;
			}
		}
	}

	return blockType;
}

bool Monster::isTarget(const std::shared_ptr<Creature> &creature) {
	if (creature->isRemoved() || !creature->isAttackable() || creature->getZoneType() == ZONE_PROTECTION || !canSeeCreature(creature)) {
		return false;
	}

	if (creature->getPosition().z != getPosition().z) {
		return false;
	}

	if (!isSummon()) {
		if (getFaction() != FACTION_DEFAULT) {
			return isEnemyFaction(creature->getFaction());
		}
	}

	return true;
}

void Monster::setFatalHoldDuration(int32_t value) {
	fatalHoldDuration = value;
}

bool Monster::isFleeing() const {
	return !isSummon() && getHealth() <= runAwayHealth && challengeFocusDuration <= 0 && challengeMeleeDuration <= 0 && fatalHoldDuration <= 0;
}

bool Monster::selectTarget(const std::shared_ptr<Creature> &creature) {
	if (!isTarget(creature)) {
		return false;
	}

	const auto &player = creature ? creature->getPlayer() : nullptr;
	if (player && player->isLoginProtected()) {
		return false;
	}

	auto it = getTargetIterator(creature);
	if (it == targetList.end()) {
		// Target not found in our target list.
		return false;
	}

	if (isHostile() || isSummon()) {
		if (setAttackedCreature(creature)) {
			checkCreatureAttack();
		}
	}
	return setFollowCreature(creature);
}

void Monster::setIdle(bool idle) {
	if (isRemoved() || getHealth() <= 0) {
		return;
	}

	isIdle = idle;

	if (!isIdle) {
		g_game().addCreatureCheck(getMonster());
	} else {
		onIdleStatus();
		clearTargetList();
		clearFriendList();
		Game::removeCreatureCheck(static_self_cast<Monster>());
	}
}

void Monster::updateIdleStatus() {
	if (!g_dispatcher().context().isAsync()) {
		setAsyncTaskFlag(UpdateIdleStatus, true);
		return;
	}

	bool idle = false;
	if (conditions.empty()) {
		if (!isSummon() && targetList.empty()) {
			if (isInSpawnLocation()) {
				idle = true;
			} else {
				isWalkingBack = true;
			}
		} else if (const auto &master = getMaster()) {
			if (((!isSummon() && totalPlayersOnScreen == 0) || (isSummon() && master->getMonster() && master->getMonster()->totalPlayersOnScreen == 0)) && getFaction() != FACTION_DEFAULT) {
				idle = true;
			}
		}
	}

	setIdle(idle);
}

bool Monster::getIdleStatus() const {
	return isIdle;
}

bool Monster::isInSpawnLocation() const {
	if (!spawnMonster) {
		return true;
	}
	return position == masterPos || masterPos == Position();
}

void Monster::onAddCondition(ConditionType_t type) {
	onConditionStatusChange(type);
}

void Monster::onConditionStatusChange(ConditionType_t /*type*/) {
	updateIdleStatus();
}

void Monster::onEndCondition(ConditionType_t type) {
	onConditionStatusChange(type);
}

void Monster::onThink(uint32_t interval) {
    Creature::onThink(interval);

    if (m_monsterType->info.thinkEvent != -1) {
        LuaScriptInterface* scriptInterface = m_monsterType->info.scriptInterface;
        if (!LuaScriptInterface::reserveScriptEnv()) {
            g_logger().error("Monstro %s Estouro de pilha de chamadas.", getName());
            return;
        }
        ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
        env->setScriptId(m_monsterType->info.thinkEvent, scriptInterface);
        lua_State* L = scriptInterface->getLuaState();
        scriptInterface->pushFunction(m_monsterType->info.thinkEvent);
        LuaScriptInterface::pushUserdata<Monster>(L, getMonster());
        LuaScriptInterface::setMetatable(L, -1, "Monster");
        lua_pushnumber(L, interval);
        if (scriptInterface->callFunction(2)) return;
    }

    if (challengeMeleeDuration != 0) {
        challengeMeleeDuration -= interval;
        if (challengeMeleeDuration <= 0) {
            challengeMeleeDuration = 0;
            targetDistance = m_monsterType->info.targetDistance;
            g_game().updateCreatureIcon(static_self_cast<Monster>());
        }
    }

    if (!m_monsterType->canSpawn(position)) {
        g_game().removeCreature(static_self_cast<Monster>());
    }

    if (!isInSpawnRange(position)) {
        g_game().internalTeleport(static_self_cast<Monster>(), masterPos);
        setIdle(true);
        return;
    }

    updateIdleStatus();

    // ==============================
    // MCR – Lógica de perseguição multi‑piso
    // ==============================
    bool isMCR = false;
    if (isSummon()) {
        isMCR = (getMaster() && getMaster()->getPlayer() != nullptr);
    } else {
        const auto& info = getMonsterType()->info;
        isMCR = info.isHostile && info.targetDistance > 0;
    }
    m_isMCR = isMCR;

    if (isMCR) {
        onThinkMCR();
    }

    setAsyncTaskFlag(OnThink, true);
}

void Monster::onThink_async() {
    // Se a criatura é gerida pelo MCR e tem uma perseguição ativa,
    // o movimento é controlado pelo onThinkMCR; caso contrário,
    // executa a lógica normal de idle/walkback.
    if (m_isMCR && (m_pursuingStairs || m_followingWaypoints || m_returningToSpawn || m_returningHome)) {
        return;
    }

    if (isIdle) return;
    addEventWalk();

    const auto &attackedCreature = getAttackedCreature();
    const auto &followCreature = getFollowCreature();

    if (isWalkingToPosition()) return;

    if (isSummon()) {
        const auto &master = getMaster();
        if (attackedCreature.get() == this) {
            setFollowCreature(nullptr);
        } else if (attackedCreature && followCreature != attackedCreature) {
            setFollowCreature(attackedCreature);
        } else if (master && master->getAttackedCreature()) {
            selectTarget(master->getAttackedCreature());
        } else if (master && master != followCreature) {
            setFollowCreature(master);
        }
    } else if (!targetList.empty()) {
        const bool attackedCreatureIsUnattackable = attackedCreature && !canUseAttack(getPosition(), attackedCreature);
        const bool attackedCreatureIsUnreachable = targetDistance <= 1 && attackedCreature && followCreature && !hasFollowPath;
        if (!getAttackedCreature() || attackedCreatureIsUnattackable || attackedCreatureIsUnreachable) {
            if (!followCreature || !hasFollowPath) {
                searchTarget(TARGETSEARCH_NEAREST);
            } else if (attackedCreature && isFleeing() && !canUseAttack(getPosition(), attackedCreature)) {
                searchTarget(TARGETSEARCH_DEFAULT);
            }
        }
    }

    onThinkTarget(EVENT_CREATURE_THINK_INTERVAL);

    safeCall([this] {
        onThinkYell(EVENT_CREATURE_THINK_INTERVAL);
        onThinkDefense(EVENT_CREATURE_THINK_INTERVAL);
        onThinkSound(EVENT_CREATURE_THINK_INTERVAL);
    });
}

void Monster::onThinkMCR() {
    if (m_inOnThinkMCR) return;
    m_inOnThinkMCR = true;
    mcrEnsureMyTileWalkable();

    uint64_t now = getCurrentTimeMs();

    // ═══ INICIALIZAÇÃO ÚNICA DA POSIÇÃO DE SPAWN ═══
    if (!m_hasSpawnPosition && getPosition().x != 0) {
        m_spawnPosition = getPosition();
        m_hasSpawnPosition = true;
        g_logger().info("[MCR-DEBUG] {} spawn position definida: {}", getName(), m_spawnPosition.toString());
    }

    // ═══ LIMPEZA DE ESCADAS FALHADAS EXPIRADAS ═══
    for (auto it = m_recentlyFailedStairs.begin(); it != m_recentlyFailedStairs.end(); ) {
        if (now >= it->second) {
            g_logger().info("[MCR-DEBUG] {} escada falhada expirada: {}", getName(), it->first.toString());
            it = m_recentlyFailedStairs.erase(it);
        } else {
            ++it;
        }
    }

    // ═══ LIMPEZA PERIÓDICA DE OBSTÁCULOS TEMPORÁRIOS ═══
    static uint64_t lastCleanup = 0;
    if (now - lastCleanup > 5000) {
        g_globalMonsterMap().cleanupTemporaryObstacles();
        lastCleanup = now;
    }

    // ═══ OBTÉM O LÍDER UMA ÚNICA VEZ ═══
    std::shared_ptr<Creature> leader;
    if (isSummon()) {
        auto master = getMaster();
        if (master && master.get()) leader = master;
    } else {
        if (!m_attackedCreature.expired()) leader = m_attackedCreature.lock();
        if (!leader) leader = m_persistentTargetPlayer;
    }

    // ═══ ATUALIZAÇÃO GLOBAL DE ENGAJAMENTO E TIMEOUTS ═══
    if (leader && !leader->isRemoved()) {
        bool visible = canSee(leader->getPosition());
        updateEngagement(visible, false, false);

        // CORREÇÃO E: deadline renovado sempre que o líder está visível
        if (visible) {
            m_sightLostTicks = 0;
            m_pursuitDeadline = computePursuitDeadline();
        } else {
            // Se não está visível, define um deadline mínimo (5s) se ainda não existir
            if (m_pursuitDeadline == 0) {
                m_pursuitDeadline = now + 5000;
            }
            m_sightLostTicks++;
            if (m_sightLostTicks >= 10) {
                g_logger().info("[MCR-DEBUG] {} perdeu líder de vista por 10 ticks, retornando ao spawn", getName());
                clearStairPursuit();
                clearWaypoints();
                setFollowCreature(nullptr);
                setAttackedCreature(nullptr);
                if (!isSummon()) {
                    if (m_spawnPosition.z != getPosition().z && !m_returnPath.empty()) {
                        m_homePosition = m_spawnPosition;
                        iniciarRetornoSpawn();
                    } else {
                        m_homePosition = m_spawnPosition;
                        m_returningHome = true;
                    }
                }
                m_inOnThinkMCR = false;
                return;
            }
            if (now > m_pursuitDeadline && m_pursuitDeadline != 0) {
                g_logger().info("[MCR-DEBUG] {} deadline de perseguição expirado, retornando ao spawn", getName());
                clearStairPursuit();
                clearWaypoints();
                setFollowCreature(nullptr);
                setAttackedCreature(nullptr);
                if (!isSummon()) {
                    if (m_spawnPosition.z != getPosition().z && !m_returnPath.empty()) {
                        m_homePosition = m_spawnPosition;
                        iniciarRetornoSpawn();
                    } else {
                        m_homePosition = m_spawnPosition;
                        m_returningHome = true;
                    }
                }
                m_inOnThinkMCR = false;
                return;
            }
        }
    } else {
        m_engagement = std::max(0, m_engagement - 3);
        m_sightLostTicks = 0;
    }

    // ═══ 0. WAYPOINTS COGNITIVOS ═══
    if (m_followingWaypoints && !m_waypoints.empty() && m_waypointIndex < m_waypoints.size()) {
        Position currentWaypoint = m_waypoints[m_waypointIndex];
        int distToWp = std::abs(getPosition().x - currentWaypoint.x) + std::abs(getPosition().y - currentWaypoint.y);

        // ──── INICIALIZAÇÃO DAS NOVAS VARIÁVEIS (apenas na primeira execução) ────
        if (m_leaderDistanceStuckCycles == 0 && m_lastDistToLeader == 0) {
            m_lastDistToLeader = leader ? (std::abs(getPosition().x - leader->getPosition().x) + std::abs(getPosition().y - leader->getPosition().y)) : 0;
        }
        // ────────────────────────────────────────────────────────────────────────

        // ──────── NOVO TIMEOUT BASEADO NA DISTÂNCIA AO LÍDER ────────
        int currentDistToLeader = leader ? (std::abs(getPosition().x - leader->getPosition().x) + std::abs(getPosition().y - leader->getPosition().y)) : 0;
        if (currentDistToLeader >= m_lastDistToLeader) {
            m_leaderDistanceStuckCycles++;
            if (m_leaderDistanceStuckCycles > 30) {
                g_logger().info("[MCR-WALK] {} sem reduzir distância ao líder por 30 ciclos. Abortando waypoints.", getName());
                clearWaypoints();
                setFollowCreature(nullptr);
                setAttackedCreature(nullptr);
                if (!isSummon()) {
                    m_homePosition = m_spawnPosition;
                    m_returningHome = true;
                }
                m_inOnThinkMCR = false;
                return;
            }
        } else {
            m_leaderDistanceStuckCycles = 0;
        }
        m_lastDistToLeader = currentDistToLeader;
        // ────────────────────────────────────────────────────────────

        // Timeout de segurança antigo (só para perseguição de escada)
        if (m_pursuingStairs && m_stairTotalCycles > 30) {
            int distToStair = std::abs(getPosition().x - m_stairOrigin.x) + std::abs(getPosition().y - m_stairOrigin.y);
            if (distToStair >= m_minDistToStair) {
                g_logger().info("[MCR-WALK] {} waypoints sem progresso ({} ciclos). Abortando e marcando escada como falhada.",
                    getName(), m_stairTotalCycles);
                m_recentlyFailedStairs[m_stairOrigin] = now + FAILED_STAIR_COOLDOWN;
                m_stairQueue.clear();
                clearStairPursuit();
                m_inOnThinkMCR = false;
                return;
            }
            m_minDistToStair = distToStair;
            m_stairTotalCycles = 0;
        }

        if (distToWp <= 1) {
            g_logger().info("[MCR-WALK] {} waypoint {} alcançado. Avançando para o próximo (índice {}/{})",
                getName(), currentWaypoint.toString(), m_waypointIndex + 1, m_waypoints.size());
            m_waypointIndex++;
            if (m_waypointIndex >= m_waypoints.size()) {
                m_followingWaypoints = false;
                m_waypoints.clear();
                g_logger().info("[MCR-WALK] {} waypoints concluídos.", getName());
            }
            m_inOnThinkMCR = false;
            return;
        }

        std::vector<Direction> listDir;
        FindPathParams fpp;
        getPathSearchParams(getMonster(), fpp);
        fpp.minTargetDist = 0;
        fpp.maxTargetDist = 1;
        fpp.fullPathSearch = true;
        fpp.clearSight = false;
        fpp.maxSearchDist = 120;

        if (getPathTo(currentWaypoint, listDir, fpp) && !listDir.empty()) {
            g_logger().info("[MCR-WALK] {} A* para waypoint {}: {} passos. Iniciando caminhada.",
                getName(), currentWaypoint.toString(), listDir.size());
            startAutoWalk(listDir);
            setWalkingToPosition(true);
            m_inOnThinkMCR = false;
            return;
        }

        g_logger().info("[MCR-WALK] {} A* falhou para waypoint {}. Scan e recálculo.", getName(), currentWaypoint.toString());
        g_globalMonsterMap().scanPlayerTrail(getPosition(), 15);
        g_globalMonsterMap().scanPlayerTrail(currentWaypoint, 15);
        auto newPath = g_globalMonsterMap().findPath(getPosition(), currentWaypoint);
        if (!newPath.empty()) {
            std::vector<Position> remaining(m_waypoints.begin() + m_waypointIndex + 1, m_waypoints.end());
            m_waypoints.resize(m_waypointIndex);
            m_waypoints.insert(m_waypoints.end(), newPath.begin(), newPath.end());
            m_waypoints.insert(m_waypoints.end(), remaining.begin(), remaining.end());
            m_waypointIndex = 0;
            g_logger().info("[MCR-WALK] {} waypoints recalculados ({} novos pontos).", getName(), m_waypoints.size());
        } else {
            g_logger().info("[MCR-WALK] {} waypoint {} inalcançável, avançando.", getName(), currentWaypoint.toString());
            m_waypointIndex++;
        }
        m_inOnThinkMCR = false;
        return;
    }

    // ═══ 1. COMBATE ═══
    if (!isSummon() && !m_returningToSpawn && !m_returningHome) {
        if (now - m_lastCombatCheck >= 2000) {
            m_lastCombatCheck = now;
            auto targetCreature = getAttackedCreature();
            if (!targetCreature) targetCreature = getFollowCreature();
            if (targetCreature && !targetCreature->isRemoved() && targetCreature->getPlayer()
                && canUseAttack(getPosition(), targetCreature)) {
                g_logger().info("[MCR-DEBUG] {} COMBATE iniciado contra {}", getName(), targetCreature->getName());
                m_hasReturnedToSpawn = false;
                clearStairPursuit();
                clearWaypoints();
                setFollowCreature(targetCreature);
                setAttackedCreature(targetCreature);
                std::vector<Direction> walkDir;
                if (getPathTo(targetCreature->getPosition(), walkDir, 0, targetDistance, true, true) && !walkDir.empty())
                    startAutoWalk(walkDir);
            }
        }
    }

    // ═══ 2. RETORNO AO SPAWN / CASA ═══
    if (m_returningHome || m_returningToSpawn) {
        if (leader && !leader->isRemoved() && leader->getPlayer() && !isSummon()
            && canSee(leader->getPosition())) {
            int distToLeader = std::abs(getPosition().x - leader->getPosition().x)
                             + std::abs(getPosition().y - leader->getPosition().y);
            if (distToLeader <= 10) {
                g_logger().info("[MCR-RETURN] {} cancelando retorno — líder visível a {} tiles.",
                    getName(), distToLeader);
                m_returningToSpawn = false;
                m_returningHome = false;
                m_returnPath.clear();
                m_walkingForReturn = false;
                m_stuckReturnTargetFails = 0;
                m_flankingFailCount = 0;
                m_hasReturnedToSpawn = false;
                clearWaypoints();
                setFollowCreature(leader);
                setAttackedCreature(leader);

                std::vector<Direction> walkDir;
                FindPathParams fpp;
                getPathSearchParams(getMonster(), fpp);
                fpp.clearSight = false;
                fpp.fullPathSearch = true;
                fpp.maxSearchDist = 120;
                if (getPathTo(leader->getPosition(), walkDir, fpp) && !walkDir.empty()) {
                    startAutoWalk(walkDir);
                } else {
                    auto cognitive = g_globalMonsterMap().findPath(getPosition(), leader->getPosition());
                    if (!cognitive.empty()) {
                        m_waypoints = cognitive;
                        m_waypointIndex = 0;
                        m_followingWaypoints = true;
                        m_leaderDistanceStuckCycles = 0;
                        m_lastDistToLeader = leader ? (std::abs(getPosition().x - leader->getPosition().x) + std::abs(getPosition().y - leader->getPosition().y)) : 0;
                        m_lastGlobalPathStart = now;
                        m_savedFollowId = leader->getID();
                    }
                }
                m_inOnThinkMCR = false;
                return;
            }
        }

        if (m_defensiveRetaliation) {
            if (now - m_lastRetaliationTime > 5000 || !getAttackedCreature()) {
                m_defensiveRetaliation = false;
                setFollowCreature(nullptr);
                setAttackedCreature(nullptr);
            } else {
                m_inOnThinkMCR = false;
                return;
            }
        }
        if (m_returningHome) {
            g_logger().info("[MCR-DEBUG] {} processando retorno simples para casa", getName());
            processarRetornoSimples();
        } else {
            g_logger().info("[MCR-DEBUG] {} processando retorno por escadas para spawn", getName());
            processarRetornoSpawn();
        }
        m_inOnThinkMCR = false;
        return;
    }

    // ═══ 4. PROCURA DE ESCADAS ═══
    if (!m_pursuingStairs && leader && !leader->isRemoved()) {
        bool deveProcurar = false;
        if (leader->getPosition().z != getPosition().z) {
            // Líder noutro piso – sempre procura escadas, mesmo com waypoints ativos
            deveProcurar = true;
            if (m_followingWaypoints) {
                g_logger().info("[MCR-DEBUG] {} líder noutro piso, abortando waypoints para procurar escadas.", getName());
                clearWaypoints();
                setFollowCreature(nullptr);
                setAttackedCreature(nullptr);
            }
        } else if (!m_followingWaypoints && !m_returningToSpawn && !m_returningHome) {
            int distToLeader = std::abs(getPosition().x - leader->getPosition().x)
                             + std::abs(getPosition().y - leader->getPosition().y);
            if (distToLeader > 20) {
                deveProcurar = true;
            } else {
                FindPathParams fpp;
                getPathSearchParams(getMonster(), fpp);
                fpp.minTargetDist = 1; fpp.maxTargetDist = targetDistance;
                fpp.fullPathSearch = true; fpp.clearSight = false; fpp.maxSearchDist = 120;
                std::vector<Direction> dummy;
                if (!getPathTo(leader->getPosition(), dummy, fpp)) {
                    deveProcurar = true;
                }
            }
        }

        if (deveProcurar && now - m_lastStairCheck >= 1000) {
            m_lastStairCheck = now;
            g_logger().info("[MCR-DEBUG] {} chamando checkStairPursuit (líder z={} meu z={})",
                getName(), leader->getPosition().z, getPosition().z);
            checkStairPursuit();
        }
    }

    // ═══ 5. PERSEGUIÇÃO ATIVA ═══
    if (m_pursuingStairs) {
        Position myPos = getPosition();
        int dist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
        m_stairTotalCycles++;

        // Tentativa de cercamento inteligente (mantida)
        trySmartFlanking();

        // Se o líder está no mesmo piso e acessível, cancela a perseguição e faz follow
        if (leader && leader.get() && leader->getPosition().z == myPos.z) {
            int distToLeader = std::abs(myPos.x - leader->getPosition().x) + std::abs(myPos.y - leader->getPosition().y);
            if (distToLeader <= 3) {
                FindPathParams fpp;
                fpp.minTargetDist = 1; fpp.maxTargetDist = targetDistance;
                fpp.fullPathSearch = true; fpp.clearSight = true; fpp.maxSearchDist = 0;
                std::vector<Direction> dummy;
                if (getPathTo(leader->getPosition(), dummy, fpp)) {
                    g_logger().info("[MCR-DEBUG] {} líder acessível, cancelando perseguição e iniciando follow", getName());
                    if (!isSummon()) m_returnPath.clear();
                    m_stairQueue.clear();
                    m_waypoints.clear();
                    m_waypointIndex = 0;
                    m_followingWaypoints = false;
                    clearStairPursuit();
                    setFollowCreature(leader);
                    setAttackedCreature(leader);
                    std::vector<Direction> walkDir;
                    if (getPathTo(leader->getPosition(), walkDir, 0, targetDistance, true, true) && !walkDir.empty())
                        startAutoWalk(walkDir);
                    m_inOnThinkMCR = false;
                    return;
                }
            }
        }

        // Se está a seguir waypoints, o movimento é gerido pelo bloco 0; não interfere
        if (m_followingWaypoints) {
            m_inOnThinkMCR = false;
            return;
        }

        // ──────── CORREÇÃO C: falso stuck deteta se a distância à escada diminuiu ────────
        if (isWalkingToPosition()) {
            int currentDist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
            if (currentDist < m_lastStuckDist) {
                m_stairStuckCount = 0;
                m_lastStuckDist = currentDist;
            } else {
                m_stairStuckCount++;
                if (m_stairStuckCount >= 8) {
                    g_logger().info("[MCR-DEBUG] {} preso há 8 ciclos, tentando desencravar", getName());
                    // Tenta waypoints de superfície (migalhas)
                    auto leader3 = (!m_attackedCreature.expired() ? m_attackedCreature.lock() : nullptr);
                    if (!leader3 || !leader3.get()) leader3 = m_persistentTargetPlayer;
                    if (leader3 && leader3.get()) {
                        auto player = leader3->getPlayer();
                        if (player) {
                            auto& waypoints = player->getSurfaceWaypoints();
                            if (!waypoints.empty()) {
                                const SurfaceWaypoint* bestWp = nullptr;
                                int bestDist = std::numeric_limits<int>::max();
                                for (const auto& wp : waypoints) {
                                    if (wp.pos.z == m_stairOrigin.z) {
                                        int d = std::abs(wp.pos.x - m_stairOrigin.x) + std::abs(wp.pos.y - m_stairOrigin.y);
                                        if (d < bestDist) { bestDist = d; bestWp = &wp; }
                                    }
                                }
                                if (bestWp && bestWp->pos != myPos) {
                                    g_logger().info("[MCR-DEBUG] {} seguindo waypoint de superfície {}", getName(), bestWp->pos.toString());
                                    walkToWaypoint(bestWp->pos);
                                    m_stairStuckCount = 0;
                                    m_inOnThinkMCR = false;
                                    return;
                                }
                            }
                        }
                    }

                    // Fallback para tiles adjacentes
                    std::vector<Position> adjacentTiles;
                    for (int dx = -1; dx <= 1; ++dx)
                        for (int dy = -1; dy <= 1; ++dy) {
                            if (dx == 0 && dy == 0) continue;
                            Position adjPos(myPos.x + dx, myPos.y + dy, myPos.z);
                            auto tile = g_game().map.getTile(adjPos);
                            if (tile && !tile->hasFlag(TILESTATE_BLOCKPATH)) adjacentTiles.push_back(adjPos);
                        }
                    if (!adjacentTiles.empty()) {
                        Position bestTile = adjacentTiles.front();
                        int bestDist = std::abs(myPos.x - bestTile.x) + std::abs(myPos.y - bestTile.y);
                        for (const auto& tile : adjacentTiles) {
                            int d = std::abs(myPos.x - tile.x) + std::abs(myPos.y - tile.y);
                            if (d < bestDist) { bestDist = d; bestTile = tile; }
                        }
                        g_logger().info("[MCR-DEBUG] {} desencravando para tile adjacente {}", getName(), bestTile.toString());
                        walkToWaypoint(bestTile);
                        m_stairStuckCount = 0;
                        m_inOnThinkMCR = false;
                        return;
                    }
                    m_stairStuckCount = 0;
                    m_inOnThinkMCR = false;
                    return;
                }
            }
        }

        // Se não está a caminhar nem a seguir waypoints, inicia a caminhada para a escada
        if (!isWalkingToPosition() && !m_followingWaypoints) {
            walkToWaypoint(m_stairOrigin);
        }

        // Se a caminhada falhou e a distância é > 1, a escada é inalcançável (marcar como falhada)
        if (!isWalkingToPosition() && !m_followingWaypoints && dist > 1) {
            g_logger().info("[MCR-DEBUG] {} escada {} inalcançável (dist={}), marcando como falhada.",
                getName(), m_stairOrigin.toString(), dist);
            m_recentlyFailedStairs[m_stairOrigin] = now + FAILED_STAIR_COOLDOWN;
            m_stairQueue.clear();
            clearStairPursuit();
            m_inOnThinkMCR = false;
            return;
        }

        // Chegada à escada (transição nativa ou teleporte)
        if (myPos == m_stairOrigin || dist <= 1) {
            bool transitionDone = false;

            // Se não está exatamente sobre a escada, tenta um movimento final
            if (myPos != m_stairOrigin) {
                Direction dir = getDirectionTo(myPos, m_stairOrigin);
                if (dir != DIRECTION_NONE) {
                    Position oldPos = myPos;
                    g_game().internalMoveCreature(static_self_cast<Monster>(), dir, 0);
                    if (getPosition() != oldPos) {
                        m_inOnThinkMCR = false;
                        return;
                    }
                }
            }

            // Se já está sobre a escada e o piso mudou, a transição nativa ocorreu
            if (myPos.z != m_stairOrigin.z) {
                g_logger().info("[MCR-STAIR] {} transição de piso detectada (movimento nativo).", getName());
                transitionDone = true;
            } else {
                // Escada ativa: tenta obter o destino real
                Position realDest = m_stairDestination;
                auto tile = g_game().map.getTile(myPos);
                if (tile) {
                    Position tileDest = tile->getDestination();
                    if (tileDest.x != 0 || tileDest.y != 0) realDest = tileDest;
                }
                if (realDest.x != 0 || realDest.y != 0) {
                    g_game().internalTeleport(static_self_cast<Monster>(), realDest);
                    g_logger().info("[MCR-STAIR] {} escada ativa: teleportando para {}.", getName(), realDest.toString());
                    transitionDone = true;
                } else {
                    g_logger().info("[MCR-STAIR] {} escada ativa sem destino válido, a desistir.", getName());
                    m_recentlyFailedStairs[m_stairOrigin] = now + FAILED_STAIR_COOLDOWN;
                }
            }

            if (transitionDone) {
                if (!isSummon()) {
                    m_returnPath.push_back({m_stairOrigin, m_stairDestination, now, m_stairIsActive});
                }

                m_lastUsedStairOrigin = m_stairOrigin;
                m_lastUsedStairDest = m_stairDestination;
                m_sameStairRepeatCount = 0;
                m_lastSuccessfulTeleport = now;

                // Avança na fila de escadas (rota multi‑piso planeada pelo BFS)
                if (!m_stairQueue.empty()) {
                    m_stairQueue.pop_front();
                    if (!m_stairQueue.empty()) {
                        const auto& nextStair = m_stairQueue.front();
                        m_stairOrigin = nextStair.origin;
                        m_stairDestination = nextStair.destination;
                        m_stairIsActive = nextStair.isActive;
                        m_stairStuckCount = 0;
                        m_stairTotalCycles = 0;
                        m_stairPathfindFailCount = 0;
                        m_forcedMoveFailCount = 0;
                        g_logger().info("[MCR-STAIR] {} próxima escada na fila: {} -> {}",
                            getName(), m_stairOrigin.toString(), m_stairDestination.toString());
                        walkToWaypoint(m_stairOrigin);
                        m_inOnThinkMCR = false;
                        return;
                    } else {
                        g_logger().info("[MCR-STAIR] {} chegou ao piso do líder.", getName());
                        clearStairPursuit();
                        if (leader && leader.get()) {
                            setFollowCreature(leader);
                            setAttackedCreature(leader);
                        }
                    }
                } else {
                    // Escada avulsa (fallback) – conclui perseguição
                    clearStairPursuit();
                }
            }

            m_inOnThinkMCR = false;
            return;
        }

        m_inOnThinkMCR = false;
        return;
    }

    // ═══ 6. PROACTIVA / CERCAMENTO ═══
    // ──────── CORREÇÃO B: removido !m_followingWaypoints da condição ────────
    if (!m_pursuingStairs && !m_returningToSpawn && !m_returningHome) {
        if (leader && leader->getPosition().z == getPosition().z) {
            FindPathParams fpp;
            getPathSearchParams(getMonster(), fpp);
            fpp.clearSight = false;
            fpp.fullPathSearch = true;
            fpp.maxSearchDist = 120;
            std::vector<Direction> dummy;
            if (!getPathTo(leader->getPosition(), dummy, fpp)) {
                if (m_flankingFailCount < 12) {
                    if (now - m_lastFlankingAttempt > 600) {
                        m_lastFlankingAttempt = now;
                        if (m_flankingFailCount == 6) {
                            g_logger().info("[MCR-DEBUG] {} scan agressivo após 6 falhas de cercamento.", getName());
                            g_globalMonsterMap().scanArea(getPosition(), 25, 2, 2, 1000,
                                leader->getPlayer()->getStairTransitions(), true);
                            g_globalMonsterMap().scanArea(leader->getPosition(), 25, 2, 2, 1000,
                                leader->getPlayer()->getStairTransitions(), true);
                        }
                        g_logger().info("[MCR-DEBUG] {} líder inacessível no mesmo piso, forçando cercamento imediato", getName());
                        tryFlankingRoute();
                        if (m_followingWaypoints) {
                            m_flankingFailCount = 0;
                            m_inOnThinkMCR = false;
                            return;
                        }
                        if (!m_followingWaypoints) {
                            m_flankingFailCount++;
                        }
                    }
                } else {
                    g_logger().info("[MCR-DEBUG] {} demasiadas falhas de cercamento, a desistir.", getName());
                    clearStairPursuit();
                    clearWaypoints();
                    setFollowCreature(nullptr);
                    setAttackedCreature(nullptr);
                    if (!isSummon()) {
                        if (m_spawnPosition.z != getPosition().z && !m_returnPath.empty()) {
                            m_homePosition = m_spawnPosition;
                            iniciarRetornoSpawn();
                        } else {
                            m_homePosition = m_spawnPosition;
                            m_returningHome = true;
                        }
                    }
                    m_flankingFailCount = 0;
                    m_inOnThinkMCR = false;
                    return;
                }
            } else {
                m_flankingFailCount = 0;
            }
        }

        if (now - m_lastProactiveCheck >= 2000) {
            m_lastProactiveCheck = now;
            auto followCreature = getFollowCreature();
            if (!followCreature || !hasFollowPath) {
                if (m_proactiveFailCount >= 3 && now - m_lastExtendedScanAttempt > 10000) {
                    g_logger().info("[MCR-DEBUG] {} forçando scan expandido após {} falhas proativas.", getName(), m_proactiveFailCount);
                    if (leader && leader->getPlayer()) {
                        g_globalMonsterMap().scanArea(getPosition(), 30, 2, 2, 2000,
                            leader->getPlayer()->getStairTransitions(), true);
                    }
                    m_lastExtendedScanAttempt = now;
                    m_proactiveFailCount = 0;
                }
                g_logger().info("[MCR-DEBUG] {} tentando rota proativa/cerco", getName());
                tryFlankingRoute();
                if (!m_followingWaypoints) {
                    tryAlternativeRouteToLeader();
                    if (!m_followingWaypoints) tryProactiveGlobalPursuit();
                }
            }
        }
    }

    if (m_followingWaypoints) { m_inOnThinkMCR = false; return; }

    // ═══ 7. OCIOSO / SEGUIR CRIATURA ═══
    if (!m_pursuingStairs && !m_followingWaypoints && !m_returningToSpawn && !m_returningHome) {
        if (now - m_lastIdleCheck >= 2000) {
            m_lastIdleCheck = now;
            auto followCreature = getFollowCreature();
            if (followCreature && !hasFollowPath) {
                std::vector<Direction> listDir;
                if (getPathTo(followCreature->getPosition(), listDir, 0, targetDistance, true, true) && !listDir.empty()) {
                    g_logger().info("[MCR-DEBUG] {} iniciando follow normal para {}", getName(), followCreature->getName());
                    startAutoWalk(listDir);
                    m_idleFailCount = 0;
                } else {
                    m_idleFailCount++;
                    if (m_idleFailCount > 5) {
                        setFollowCreature(nullptr);
                        setAttackedCreature(nullptr);
                        m_idleFailCount = 0;
                    }
                }
            } else if (!followCreature) {
                m_idleFailCount = 0;
                if (m_hasSpawnPosition) {
                    int distToSpawn = std::abs(getPosition().x - m_spawnPosition.x)
                                    + std::abs(getPosition().y - m_spawnPosition.y);
                    if (distToSpawn > 10) {
                        g_logger().info("[MCR-DEBUG] {} longe do spawn ({} tiles), retornando", getName(), distToSpawn);
                        tryReturnToSpawn();
                    } else {
                        g_logger().info("[MCR-DEBUG] {} ocioso, deambulando", getName());
                        tryIdleWander();
                    }
                } else {
                    tryIdleWander();
                }
            }
        }
    }

    m_inOnThinkMCR = false;
}

void Monster::doAttacking(uint32_t interval) {
	const auto &attackedCreature = getAttackedCreature();
	if (!getAttackedCreature() || attackedCreature->isLifeless() || (isSummon() && attackedCreature.get() == this)) {
		return;
	}

	const auto &player = attackedCreature->getPlayer();
	if (player && player->isLoginProtected()) {
		return;
	}

	bool updateLook = true;
	bool resetTicks = interval != 0;
	attackTicks += interval;

	const Position &myPos = getPosition();
	const Position &targetPos = attackedCreature->getPosition();

	for (const spellBlock_t &spellBlock : attackSpells) {
		bool inRange = false;

		if (spellBlock.spell == nullptr || (spellBlock.isMelee && isFleeing())) {
			continue;
		}

		if (canUseSpell(myPos, targetPos, spellBlock, interval, inRange, resetTicks)) {
			if (spellBlock.chance >= static_cast<uint32_t>(uniform_random(1, 100))) {
				if (updateLook) {
					updateLookDirection();
					updateLook = false;
				}

				minCombatValue = spellBlock.minCombatValue;
				maxCombatValue = spellBlock.maxCombatValue;

				if (spellBlock.spell == nullptr) {
					continue;
				}

				spellBlock.spell->castSpell(getMonster(), attackedCreature);

				if (spellBlock.isMelee) {
					extraMeleeAttack = false;
				}
			}
		}

		if (!inRange && spellBlock.isMelee) {
			// melee swing out of reach
			extraMeleeAttack = true;
		}
	}

	if (updateLook) {
		updateLookDirection();
	}

	if (resetTicks) {
		attackTicks = 0;
	}
}

bool Monster::hasExtraSwing() {
	return extraMeleeAttack;
}

bool Monster::canUseAttack(const Position &pos, const std::shared_ptr<Creature> &target) const {
	if (isHostile()) {
		const Position &targetPos = target->getPosition();
		uint32_t distance = std::max<uint32_t>(Position::getDistanceX(pos, targetPos), Position::getDistanceY(pos, targetPos));
		for (const spellBlock_t &spellBlock : attackSpells) {
			if (spellBlock.range != 0 && distance <= spellBlock.range) {
				return g_game().isSightClear(pos, targetPos, true);
			}
		}
		return false;
	}
	return true;
}

bool Monster::canUseSpell(const Position &pos, const Position &targetPos, const spellBlock_t &sb, uint32_t interval, bool &inRange, bool &resetTicks) {
	inRange = true;

	if (sb.isMelee && isFleeing()) {
		return false;
	}

	if (extraMeleeAttack) {
		lastMeleeAttack = OTSYS_TIME();
	} else if (sb.isMelee && (OTSYS_TIME() - lastMeleeAttack) < 1500) {
		return false;
	}

	if (!sb.isMelee || !extraMeleeAttack) {
		if (sb.speed > attackTicks) {
			resetTicks = false;
			return false;
		}

		if (attackTicks % sb.speed >= interval) {
			// already used this spell for this round
			return false;
		}
	}

	if (sb.range != 0 && std::max<uint32_t>(Position::getDistanceX(pos, targetPos), Position::getDistanceY(pos, targetPos)) > sb.range) {
		inRange = false;
		return false;
	}
	return true;
}

void Monster::onThinkTarget(uint32_t interval) {
	if (!isSummon()) {
		if (m_monsterType->info.changeTargetSpeed != 0) {
			bool canChangeTarget = true;

			if (challengeFocusDuration > 0) {
				challengeFocusDuration -= interval;
				canChangeTarget = false;

				if (challengeFocusDuration <= 0) {
					challengeFocusDuration = 0;
				}
			}

			if (fatalHoldDuration > 0 && runAwayHealth > 0) {
				fatalHoldDuration -= interval;

				if (fatalHoldDuration <= 0) {
					fatalHoldDuration = 0;
				}
			}

			if (m_targetChangeCooldown > 0) {
				m_targetChangeCooldown -= interval;

				if (m_targetChangeCooldown <= 0) {
					m_targetChangeCooldown = 0;
					targetChangeTicks = m_monsterType->info.changeTargetSpeed;
				} else {
					canChangeTarget = false;
				}
			}

			if (canChangeTarget) {
				targetChangeTicks += interval;

				if (targetChangeTicks >= m_monsterType->info.changeTargetSpeed) {
					targetChangeTicks = 0;
					m_targetChangeCooldown = m_monsterType->info.changeTargetSpeed;

					if (challengeFocusDuration > 0) {
						challengeFocusDuration = 0;
					}

					if (m_monsterType->info.changeTargetChance >= uniform_random(1, 100)) {
						if (m_monsterType->info.targetDistance <= 1) {
							searchTarget(TARGETSEARCH_RANDOM);
						} else {
							searchTarget(TARGETSEARCH_NEAREST);
						}
					}
				}
			}
		}
	}
}

void Monster::onThinkDefense(uint32_t interval) {
	bool resetTicks = true;
	defenseTicks += interval;

	for (const spellBlock_t &spellBlock : defenseSpells) {
		if (spellBlock.speed > defenseTicks) {
			resetTicks = false;
			continue;
		}

		if (spellBlock.spell == nullptr || defenseTicks % spellBlock.speed >= interval) {
			// already used this spell for this round
			continue;
		}

		if ((spellBlock.chance >= static_cast<uint32_t>(uniform_random(1, 100)))) {
			minCombatValue = spellBlock.minCombatValue;
			maxCombatValue = spellBlock.maxCombatValue;
			spellBlock.spell->castSpell(getMonster(), getMonster());
		}
	}

	if (!isSummon() && m_summons.size() < m_monsterType->info.maxSummons && hasFollowPath) {
		for (const auto &[summonName, summonChance, summonSpeed, summonCount, summonForce] : m_monsterType->info.summons) {
			if (summonSpeed > defenseTicks) {
				resetTicks = false;
				continue;
			}

			if (m_summons.size() >= m_monsterType->info.maxSummons) {
				continue;
			}

			if (defenseTicks % summonSpeed >= interval) {
				// already used this spell for this round
				continue;
			}

			uint32_t summonsCount = 0;
			for (const auto &summon : m_summons) {
				if (summon && summon->getName() == summonName) {
					++summonsCount;
				}
			}

			if (summonsCount >= summonCount) {
				continue;
			}

			if (summonChance < static_cast<uint32_t>(uniform_random(1, 100))) {
				continue;
			}

			const auto &summon = Monster::createMonster(summonName);
			if (summon && g_game().placeCreature(summon, getPosition(), false, summonForce)) {
				if (getSoulPit()) {
					const auto stack = getForgeStack();
					summon->setSoulPitStack(stack, true);
				}
				summon->setMaster(static_self_cast<Monster>(), true);
				g_game().addMagicEffect(getPosition(), CONST_ME_MAGIC_BLUE);
				g_game().addMagicEffect(summon->getPosition(), CONST_ME_TELEPORT);
				g_game().sendSingleSoundEffect(summon->getPosition(), SoundEffect_t::MONSTER_SPELL_SUMMON, getMonster());
			}
		}
	}

	if (resetTicks) {
		defenseTicks = 0;
	}
}

void Monster::onThinkYell(uint32_t interval) {
	if (m_monsterType->info.yellSpeedTicks == 0) {
		return;
	}

	yellTicks += interval;
	if (yellTicks >= m_monsterType->info.yellSpeedTicks) {
		yellTicks = 0;

		if (!m_monsterType->info.voiceVector.empty() && (m_monsterType->info.yellChance >= static_cast<uint32_t>(uniform_random(1, 100)))) {
			const uint32_t index = uniform_random(0, m_monsterType->info.voiceVector.size() - 1);
			const auto &[text, yellText] = m_monsterType->info.voiceVector[index];

			if (yellText) {
				g_game().internalCreatureSay(static_self_cast<Monster>(), TALKTYPE_MONSTER_YELL, text, false);
			} else {
				g_game().internalCreatureSay(static_self_cast<Monster>(), TALKTYPE_MONSTER_SAY, text, false);
			}
		}
	}
}

void Monster::onThinkSound(uint32_t interval) {
	if (m_monsterType->info.soundSpeedTicks == 0) {
		return;
	}

	soundTicks += interval;
	if (soundTicks >= m_monsterType->info.soundSpeedTicks) {
		soundTicks = 0;

		if (!m_monsterType->info.soundVector.empty() && (m_monsterType->info.soundChance >= static_cast<uint32_t>(uniform_random(1, 100)))) {
			int64_t index = uniform_random(0, static_cast<int64_t>(m_monsterType->info.soundVector.size() - 1));
			g_game().sendSingleSoundEffect(static_self_cast<Monster>()->getPosition(), m_monsterType->info.soundVector[index], getMonster());
		}
	}
}

bool Monster::pushItem(const std::shared_ptr<Item> &item, const Direction &dir) {
	if (!item) {
		return false;
	}

	auto fromTile = item->getTile();
	if (!fromTile) {
		return false;
	}

	if (fromTile->getHouse()) {
		return false;
	}

	const Position &fromPos = fromTile->getPosition();
	std::shared_ptr<Cylinder> fromCyl = fromTile;

	for (auto [dx, dy] : getPushItemLocationOptions(dir)) {
		Position toPos(fromPos.x + dx, fromPos.y + dy, fromPos.z);
		auto toTile = g_game().map.getTile(toPos);

		if (toTile && g_game().canThrowObjectTo(fromPos, toPos) && g_game().internalMoveItem(fromCyl, toTile, INDEX_WHEREEVER, item, item->getItemCount(), nullptr) == RETURNVALUE_NOERROR) {
			return true;
		}
	}
	return false;
}

void Monster::pushItems(const std::shared_ptr<Tile> &tile, const Direction &nextDirection) {
	if (!tile) {
		return;
	}

	const auto* items = tile->getItemList();
	if (!items || items->empty()) {
		return;
	}

	if (tile->getHouse()) {
		return;
	}

	uint32_t moveCount = 0;
	uint32_t removeCount = 0;
	int32_t downItemSize = tile->getDownItemCount();
	std::vector<std::shared_ptr<Item>> downItems;
	downItems.reserve(downItemSize);
	for (int32_t i = 0; i < downItemSize; ++i) {
		downItems.push_back(items->at(i));
	}

	for (auto i = static_cast<int32_t>(downItems.size()); --i >= 0;) {
		const auto &item = downItems.at(i);
		if (!item || !item->hasProperty(CONST_PROP_MOVABLE) || !item->canBeMoved()) {
			continue;
		}
		if (item->getTile() != tile) {
			continue;
		}
		if (!item->hasProperty(CONST_PROP_BLOCKPATH) && !item->hasProperty(CONST_PROP_BLOCKSOLID)) {
			continue;
		}

		if (moveCount < 20 && pushItem(item, nextDirection)) {
			++moveCount;
		} else if (removeCount < 10 && !item->isCorpse() && g_game().internalRemoveItem(item) == RETURNVALUE_NOERROR) {
			++removeCount;
		}
	}

	if (removeCount > 0) {
		g_game().addMagicEffect(tile->getPosition(), CONST_ME_POFF);
	}
}

bool Monster::pushCreature(const std::shared_ptr<Creature> &creature) {
	static std::vector<Direction> dirList {
		DIRECTION_NORTH,
		DIRECTION_WEST, DIRECTION_EAST,
		DIRECTION_SOUTH
	};
	[[maybe_unused]] auto last = std::ranges::shuffle(dirList, getRandomGenerator());

	for (const Direction &dir : dirList) {
		const Position &tryPos = Spells::getCasterPosition(creature, dir);
		const auto &toTile = g_game().map.getTile(tryPos);
		if (toTile && !toTile->hasFlag(TILESTATE_BLOCKPATH) && g_game().internalMoveCreature(creature, dir) == RETURNVALUE_NOERROR) {
			return true;
		}
	}
	return false;
}

void Monster::pushCreatures(const std::shared_ptr<Tile> &tile) {
	if (!tile) {
		return;
	}

	const CreatureVector* creatures = tile->getCreatures();
	if (!creatures || creatures->empty()) {
		return;
	}

	CreatureVector creaturesCopy = *creatures;
	uint32_t killedCount = 0;
	std::shared_ptr<Monster> lastPushedMonster = nullptr;

	for (int i = static_cast<int>(creaturesCopy.size()) - 1; i >= 0; --i) {
		const auto &creature = creaturesCopy[i];
		if (!creature) {
			continue;
		}

		const std::shared_ptr<Monster> monster = creature->getMonster();
		if (monster && monster->isPushable()) {
			if (monster != lastPushedMonster && Monster::pushCreature(monster)) {
				lastPushedMonster = monster;
				continue;
			}

			monster->changeHealth(-monster->getHealth());
			monster->setDropLoot(true);
			killedCount++;
		}
	}

	if (killedCount > 0) {
		g_game().addMagicEffect(tile->getPosition(), CONST_ME_BLOCKHIT);
	}
}

bool Monster::getNextStep(Direction &nextDirection, uint32_t &flags) {
        // ============================================================
    // MCR: Se estiver a caminhar para uma posição fixa, usa o
    //      caminho pré‑calculado (ignora random step e follow)
    // ============================================================
    if (isWalkingToPosition()) {
        return Creature::getNextStep(nextDirection, flags);
    }
    // ============================================================
	
	
	if (isIdle || getHealth() <= 0) {
        eventWalk = 0;
        return false;
    }

    bool result = false;

    if (getFollowCreature() && hasFollowPath) {
        doFollowCreature(flags, nextDirection, result);
    } else if (isWalkingBack) {
        doWalkBack(flags, nextDirection, result);
    } else {
        doRandomStep(nextDirection, result);
    }

	if (result && (canPushItems() || canPushCreatures())) {
		const Position &pos = getNextPosition(nextDirection, getPosition());
		const auto &posTile = g_game().map.getTile(pos);
		if (posTile) {
			if (canPushItems()) {
				Monster::pushItems(posTile, nextDirection);
			}

			if (canPushCreatures()) {
				if (g_dispatcher().context().getGroup() == TaskGroup::Walk) {
					Monster::pushCreatures(posTile);
				} else {
					g_dispatcher().addWalkEvent([=] {
						Monster::pushCreatures(posTile);
					});
				}
			}
		}
	}

	return result;
}

void Monster::doRandomStep(Direction &nextDirection, bool &result) {
	if (getTimeSinceLastMove() >= 1000) {
		randomStepping = true;
		result = getRandomStep(getPosition(), nextDirection);
	}
}

void Monster::doWalkBack(uint32_t &flags, Direction &nextDirection, bool &result) {
	if (totalPlayersOnScreen > 0) {
		isWalkingBack = false;
		return;
	}

	result = Creature::getNextStep(nextDirection, flags);
	if (result) {
		flags |= FLAG_PATHFINDING;
	} else {
		if (ignoreFieldDamage) {
			ignoreFieldDamage = false;
		}

		int32_t distance = std::max<int32_t>(Position::getDistanceX(position, masterPos), Position::getDistanceY(position, masterPos));
		if (distance == 0) {
			isWalkingBack = false;
			return;
		}

		std::vector<Direction> listDir;
		if (!getPathTo(masterPos, listDir, 0, std::max<int32_t>(0, distance - 5), true, true, distance)) {
			isWalkingBack = false;
			return;
		}
		startAutoWalk(listDir);
	}
}

void Monster::doFollowCreature(uint32_t &flags, Direction &nextDirection, bool &result) {
	randomStepping = false;
	result = Creature::getNextStep(nextDirection, flags);
	if (result) {
		flags |= FLAG_PATHFINDING;
	} else {
		if (ignoreFieldDamage) {
			ignoreFieldDamage = false;
		}
		// target dancing
		const auto &attackedCreature = getAttackedCreature();
		const auto &followCreature = getFollowCreature();
		if (attackedCreature && attackedCreature == followCreature) {
			if (isFleeing()) {
				result = getDanceStep(getPosition(), nextDirection, false, false);
			} else if (m_monsterType->info.staticAttackChance < static_cast<uint32_t>(uniform_random(1, 100))) {
				result = getDanceStep(getPosition(), nextDirection);
			}
		}
	}
}

bool Monster::getRandomStep(const Position &creaturePos, Direction &moveDirection) {
	static std::vector<Direction> dirList {
		DIRECTION_NORTH,
		DIRECTION_WEST, DIRECTION_EAST,
		DIRECTION_SOUTH
	};
	[[maybe_unused]] auto last = std::ranges::shuffle(dirList, getRandomGenerator());

	for (const Direction &dir : dirList) {
		if (canWalkTo(creaturePos, dir)) {
			moveDirection = dir;
			return true;
		}
	}
	return false;
}

bool Monster::getDanceStep(const Position &creaturePos, Direction &moveDirection, bool keepAttack /*= true*/, bool keepDistance /*= true*/) {
	const auto &attackedCreature = getAttackedCreature();
	if (!getAttackedCreature()) {
		return false;
	}
	bool canDoAttackNow = canUseAttack(creaturePos, attackedCreature);
	const Position &centerPos = attackedCreature->getPosition();

	int_fast32_t offset_x = Position::getOffsetX(creaturePos, centerPos);
	int_fast32_t offset_y = Position::getOffsetY(creaturePos, centerPos);

	int_fast32_t distance_x = std::abs(offset_x);
	int_fast32_t distance_y = std::abs(offset_y);

	uint32_t centerToDist = std::max<uint32_t>(distance_x, distance_y);

	// monsters not at targetDistance shouldn't dancestep
	if (centerToDist < static_cast<uint32_t>(targetDistance)) {
		return false;
	}

	std::vector<Direction> dirList;
	auto tryAddDirection = [&](Direction direction, int_fast32_t newX, int_fast32_t newY) {
		uint32_t tmpDist = std::max<uint32_t>(std::abs(newX - centerPos.getX()), std::abs(newY - centerPos.getY()));
		if (tmpDist == centerToDist && canWalkTo(creaturePos, direction)) {
			bool result = true;

			if (keepAttack) {
				result = (!canDoAttackNow || canUseAttack(Position(newX, newY, creaturePos.z), attackedCreature));
			}

			if (result) {
				dirList.emplace_back(direction);
			}
		}
	};

	if (!keepDistance || offset_y >= 0) {
		tryAddDirection(DIRECTION_NORTH, creaturePos.getX(), creaturePos.getY() - 1);
	}

	if (!keepDistance || offset_y <= 0) {
		tryAddDirection(DIRECTION_SOUTH, creaturePos.getX(), creaturePos.getY() + 1);
	}

	if (!keepDistance || offset_x <= 0) {
		tryAddDirection(DIRECTION_EAST, creaturePos.getX() + 1, creaturePos.getY());
	}

	if (!keepDistance || offset_x >= 0) {
		tryAddDirection(DIRECTION_WEST, creaturePos.getX() - 1, creaturePos.getY());
	}

	if (!dirList.empty()) {
		[[maybe_unused]] auto last = std::ranges::shuffle(dirList, getRandomGenerator());
		moveDirection = dirList[uniform_random(0, dirList.size() - 1)];
		return true;
	}
	return false;
}

bool Monster::getDistanceStep(const Position &targetPos, Direction &moveDirection, bool flee /* = false */) {
	const Position &creaturePos = getPosition();

	int_fast32_t dx = Position::getDistanceX(creaturePos, targetPos);
	int_fast32_t dy = Position::getDistanceY(creaturePos, targetPos);

	if (int32_t distance = std::max<int32_t>(static_cast<int32_t>(dx), static_cast<int32_t>(dy)); !flee && (distance > targetDistance || !g_game().isSightClear(creaturePos, targetPos, true))) {
		return false; // let the A* calculate it
	} else if (!flee && distance == targetDistance) {
		return true; // we don't really care here, since it's what we wanted to reach (a dancestep will take of dancing in that position)
	}

	int_fast32_t offsetx = Position::getOffsetX(creaturePos, targetPos);
	int_fast32_t offsety = Position::getOffsetY(creaturePos, targetPos);

	if (dx <= 1 && dy <= 1) {
		// seems like a target is near, it this case we need to slow down our movements (as a monster)
		if (stepDuration < 2) {
			stepDuration++;
		}
	} else if (stepDuration > 0) {
		stepDuration--;
	}

	if (offsetx == 0 && offsety == 0) {
		return getRandomStep(creaturePos, moveDirection); // player is "on" the monster so let's get some random step and rest will be taken care later.
	}

	if (dx == dy) {
		// player is diagonal to the monster
		if (offsetx >= 1 && offsety >= 1) {
			// player is NW
			// escape to SE, S or E [and some extra]
			bool s = canWalkTo(creaturePos, DIRECTION_SOUTH);
			bool e = canWalkTo(creaturePos, DIRECTION_EAST);

			if (s && e) {
				moveDirection = boolean_random() ? DIRECTION_SOUTH : DIRECTION_EAST;
				return true;
			} else if (s) {
				moveDirection = DIRECTION_SOUTH;
				return true;
			} else if (e) {
				moveDirection = DIRECTION_EAST;
				return true;
			} else if (canWalkTo(creaturePos, DIRECTION_SOUTHEAST)) {
				moveDirection = DIRECTION_SOUTHEAST;
				return true;
			}

			/* fleeing */
			bool n = canWalkTo(creaturePos, DIRECTION_NORTH);
			bool w = canWalkTo(creaturePos, DIRECTION_WEST);

			if (flee) {
				if (n && w) {
					moveDirection = boolean_random() ? DIRECTION_NORTH : DIRECTION_WEST;
					return true;
				} else if (n) {
					moveDirection = DIRECTION_NORTH;
					return true;
				} else if (w) {
					moveDirection = DIRECTION_WEST;
					return true;
				}
			}

			/* end of fleeing */

			if (w && canWalkTo(creaturePos, DIRECTION_SOUTHWEST)) {
				moveDirection = DIRECTION_WEST;
			} else if (n && canWalkTo(creaturePos, DIRECTION_NORTHEAST)) {
				moveDirection = DIRECTION_NORTH;
			}

			return true;
		} else if (offsetx <= -1 && offsety <= -1) {
			// player is SE
			// escape to NW , W or N [and some extra]
			bool w = canWalkTo(creaturePos, DIRECTION_WEST);
			bool n = canWalkTo(creaturePos, DIRECTION_NORTH);

			if (w && n) {
				moveDirection = boolean_random() ? DIRECTION_WEST : DIRECTION_NORTH;
				return true;
			} else if (w) {
				moveDirection = DIRECTION_WEST;
				return true;
			} else if (n) {
				moveDirection = DIRECTION_NORTH;
				return true;
			}

			if (canWalkTo(creaturePos, DIRECTION_NORTHWEST)) {
				moveDirection = DIRECTION_NORTHWEST;
				return true;
			}

			/* fleeing */
			bool s = canWalkTo(creaturePos, DIRECTION_SOUTH);
			bool e = canWalkTo(creaturePos, DIRECTION_EAST);

			if (flee) {
				if (s && e) {
					moveDirection = boolean_random() ? DIRECTION_SOUTH : DIRECTION_EAST;
					return true;
				} else if (s) {
					moveDirection = DIRECTION_SOUTH;
					return true;
				} else if (e) {
					moveDirection = DIRECTION_EAST;
					return true;
				}
			}

			/* end of fleeing */

			if (s && canWalkTo(creaturePos, DIRECTION_SOUTHWEST)) {
				moveDirection = DIRECTION_SOUTH;
			} else if (e && canWalkTo(creaturePos, DIRECTION_NORTHEAST)) {
				moveDirection = DIRECTION_EAST;
			}

			return true;
		} else if (offsetx >= 1 && offsety <= -1) {
			// player is SW
			// escape to NE, N, E [and some extra]
			bool n = canWalkTo(creaturePos, DIRECTION_NORTH);
			bool e = canWalkTo(creaturePos, DIRECTION_EAST);
			if (n && e) {
				moveDirection = boolean_random() ? DIRECTION_NORTH : DIRECTION_EAST;
				return true;
			} else if (n) {
				moveDirection = DIRECTION_NORTH;
				return true;
			} else if (e) {
				moveDirection = DIRECTION_EAST;
				return true;
			}

			if (canWalkTo(creaturePos, DIRECTION_NORTHEAST)) {
				moveDirection = DIRECTION_NORTHEAST;
				return true;
			}

			/* fleeing */
			bool s = canWalkTo(creaturePos, DIRECTION_SOUTH);
			bool w = canWalkTo(creaturePos, DIRECTION_WEST);

			if (flee) {
				if (s && w) {
					moveDirection = boolean_random() ? DIRECTION_SOUTH : DIRECTION_WEST;
					return true;
				} else if (s) {
					moveDirection = DIRECTION_SOUTH;
					return true;
				} else if (w) {
					moveDirection = DIRECTION_WEST;
					return true;
				}
			}

			/* end of fleeing */

			if (w && canWalkTo(creaturePos, DIRECTION_NORTHWEST)) {
				moveDirection = DIRECTION_WEST;
			} else if (s && canWalkTo(creaturePos, DIRECTION_SOUTHEAST)) {
				moveDirection = DIRECTION_SOUTH;
			}

			return true;
		} else if (offsetx <= -1 && offsety >= 1) {
			// player is NE
			// escape to SW, S, W [and some extra]
			bool w = canWalkTo(creaturePos, DIRECTION_WEST);
			bool s = canWalkTo(creaturePos, DIRECTION_SOUTH);
			if (w && s) {
				moveDirection = boolean_random() ? DIRECTION_WEST : DIRECTION_SOUTH;
				return true;
			} else if (w) {
				moveDirection = DIRECTION_WEST;
				return true;
			} else if (s) {
				moveDirection = DIRECTION_SOUTH;
				return true;
			} else if (canWalkTo(creaturePos, DIRECTION_SOUTHWEST)) {
				moveDirection = DIRECTION_SOUTHWEST;
				return true;
			}

			/* fleeing */
			bool n = canWalkTo(creaturePos, DIRECTION_NORTH);
			bool e = canWalkTo(creaturePos, DIRECTION_EAST);

			if (flee) {
				if (n && e) {
					moveDirection = boolean_random() ? DIRECTION_NORTH : DIRECTION_EAST;
					return true;
				} else if (n) {
					moveDirection = DIRECTION_NORTH;
					return true;
				} else if (e) {
					moveDirection = DIRECTION_EAST;
					return true;
				}
			}

			/* end of fleeing */

			if (e && canWalkTo(creaturePos, DIRECTION_SOUTHEAST)) {
				moveDirection = DIRECTION_EAST;
			} else if (n && canWalkTo(creaturePos, DIRECTION_NORTHWEST)) {
				moveDirection = DIRECTION_NORTH;
			}

			return true;
		}
	}

	// Now let's decide where the player is located to the monster (what direction) so we can decide where to escape.
	if (dy > dx) {
		Direction playerDir = offsety < 0 ? DIRECTION_SOUTH : DIRECTION_NORTH;
		switch (playerDir) {
			case DIRECTION_NORTH: {
				// Player is to the NORTH, so obviously we need to check if we can go SOUTH, if not then let's choose WEST or EAST and again if we can't we need to decide about some diagonal movements.
				if (canWalkTo(creaturePos, DIRECTION_SOUTH)) {
					moveDirection = DIRECTION_SOUTH;
					return true;
				}

				bool w = canWalkTo(creaturePos, DIRECTION_WEST);
				bool e = canWalkTo(creaturePos, DIRECTION_EAST);
				if (w && e && offsetx == 0) {
					moveDirection = boolean_random() ? DIRECTION_WEST : DIRECTION_EAST;
					return true;
				} else if (w && offsetx <= 0) {
					moveDirection = DIRECTION_WEST;
					return true;
				} else if (e && offsetx >= 0) {
					moveDirection = DIRECTION_EAST;
					return true;
				}

				/* fleeing */
				if (flee) {
					if (w && e) {
						moveDirection = boolean_random() ? DIRECTION_WEST : DIRECTION_EAST;
						return true;
					} else if (w) {
						moveDirection = DIRECTION_WEST;
						return true;
					} else if (e) {
						moveDirection = DIRECTION_EAST;
						return true;
					}
				}

				/* end of fleeing */

				bool sw = canWalkTo(creaturePos, DIRECTION_SOUTHWEST);
				bool se = canWalkTo(creaturePos, DIRECTION_SOUTHEAST);
				if (sw || se) {
					// we can move both dirs
					if (sw && se) {
						moveDirection = boolean_random() ? DIRECTION_SOUTHWEST : DIRECTION_SOUTHEAST;
					} else if (w) {
						moveDirection = DIRECTION_WEST;
					} else if (sw) {
						moveDirection = DIRECTION_SOUTHWEST;
					} else if (e) {
						moveDirection = DIRECTION_EAST;
					} else if (se) {
						moveDirection = DIRECTION_SOUTHEAST;
					}
					return true;
				}

				/* fleeing */
				if (flee && canWalkTo(creaturePos, DIRECTION_NORTH)) {
					// towards player, yea
					moveDirection = DIRECTION_NORTH;
					return true;
				}

				/* end of fleeing */
				break;
			}

			case DIRECTION_SOUTH: {
				if (canWalkTo(creaturePos, DIRECTION_NORTH)) {
					moveDirection = DIRECTION_NORTH;
					return true;
				}

				bool w = canWalkTo(creaturePos, DIRECTION_WEST);
				bool e = canWalkTo(creaturePos, DIRECTION_EAST);
				if (w && e && offsetx == 0) {
					moveDirection = boolean_random() ? DIRECTION_WEST : DIRECTION_EAST;
					return true;
				} else if (w && offsetx <= 0) {
					moveDirection = DIRECTION_WEST;
					return true;
				} else if (e && offsetx >= 0) {
					moveDirection = DIRECTION_EAST;
					return true;
				}

				/* fleeing */
				if (flee) {
					if (w && e) {
						moveDirection = boolean_random() ? DIRECTION_WEST : DIRECTION_EAST;
						return true;
					} else if (w) {
						moveDirection = DIRECTION_WEST;
						return true;
					} else if (e) {
						moveDirection = DIRECTION_EAST;
						return true;
					}
				}

				/* end of fleeing */

				bool nw = canWalkTo(creaturePos, DIRECTION_NORTHWEST);
				bool ne = canWalkTo(creaturePos, DIRECTION_NORTHEAST);
				if (nw || ne) {
					// we can move both dirs
					if (nw && ne) {
						moveDirection = boolean_random() ? DIRECTION_NORTHWEST : DIRECTION_NORTHEAST;
					} else if (w) {
						moveDirection = DIRECTION_WEST;
					} else if (nw) {
						moveDirection = DIRECTION_NORTHWEST;
					} else if (e) {
						moveDirection = DIRECTION_EAST;
					} else if (ne) {
						moveDirection = DIRECTION_NORTHEAST;
					}
					return true;
				}

				/* fleeing */
				if (flee && canWalkTo(creaturePos, DIRECTION_SOUTH)) {
					// towards player, yea
					moveDirection = DIRECTION_SOUTH;
					return true;
				}

				/* end of fleeing */
				break;
			}

			default:
				break;
		}
	} else {
		Direction playerDir = offsetx < 0 ? DIRECTION_EAST : DIRECTION_WEST;
		switch (playerDir) {
			case DIRECTION_WEST: {
				if (canWalkTo(creaturePos, DIRECTION_EAST)) {
					moveDirection = DIRECTION_EAST;
					return true;
				}

				bool n = canWalkTo(creaturePos, DIRECTION_NORTH);
				bool s = canWalkTo(creaturePos, DIRECTION_SOUTH);
				if (n && s && offsety == 0) {
					moveDirection = boolean_random() ? DIRECTION_NORTH : DIRECTION_SOUTH;
					return true;
				} else if (n && offsety <= 0) {
					moveDirection = DIRECTION_NORTH;
					return true;
				} else if (s && offsety >= 0) {
					moveDirection = DIRECTION_SOUTH;
					return true;
				}

				/* fleeing */
				if (flee) {
					if (n && s) {
						moveDirection = boolean_random() ? DIRECTION_NORTH : DIRECTION_SOUTH;
						return true;
					} else if (n) {
						moveDirection = DIRECTION_NORTH;
						return true;
					} else if (s) {
						moveDirection = DIRECTION_SOUTH;
						return true;
					}
				}

				/* end of fleeing */

				bool se = canWalkTo(creaturePos, DIRECTION_SOUTHEAST);
				bool ne = canWalkTo(creaturePos, DIRECTION_NORTHEAST);
				if (se || ne) {
					if (se && ne) {
						moveDirection = boolean_random() ? DIRECTION_SOUTHEAST : DIRECTION_NORTHEAST;
					} else if (s) {
						moveDirection = DIRECTION_SOUTH;
					} else if (se) {
						moveDirection = DIRECTION_SOUTHEAST;
					} else if (n) {
						moveDirection = DIRECTION_NORTH;
					} else if (ne) {
						moveDirection = DIRECTION_NORTHEAST;
					}
					return true;
				}

				/* fleeing */
				if (flee && canWalkTo(creaturePos, DIRECTION_WEST)) {
					// towards player, yea
					moveDirection = DIRECTION_WEST;
					return true;
				}

				/* end of fleeing */
				break;
			}

			case DIRECTION_EAST: {
				if (canWalkTo(creaturePos, DIRECTION_WEST)) {
					moveDirection = DIRECTION_WEST;
					return true;
				}

				bool n = canWalkTo(creaturePos, DIRECTION_NORTH);
				bool s = canWalkTo(creaturePos, DIRECTION_SOUTH);
				if (n && s && offsety == 0) {
					moveDirection = boolean_random() ? DIRECTION_NORTH : DIRECTION_SOUTH;
					return true;
				} else if (n && offsety <= 0) {
					moveDirection = DIRECTION_NORTH;
					return true;
				} else if (s && offsety >= 0) {
					moveDirection = DIRECTION_SOUTH;
					return true;
				}

				/* fleeing */
				if (flee) {
					if (n && s) {
						moveDirection = boolean_random() ? DIRECTION_NORTH : DIRECTION_SOUTH;
						return true;
					} else if (n) {
						moveDirection = DIRECTION_NORTH;
						return true;
					} else if (s) {
						moveDirection = DIRECTION_SOUTH;
						return true;
					}
				}

				/* end of fleeing */

				bool nw = canWalkTo(creaturePos, DIRECTION_NORTHWEST);
				bool sw = canWalkTo(creaturePos, DIRECTION_SOUTHWEST);
				if (nw || sw) {
					if (nw && sw) {
						moveDirection = boolean_random() ? DIRECTION_NORTHWEST : DIRECTION_SOUTHWEST;
					} else if (n) {
						moveDirection = DIRECTION_NORTH;
					} else if (nw) {
						moveDirection = DIRECTION_NORTHWEST;
					} else if (s) {
						moveDirection = DIRECTION_SOUTH;
					} else if (sw) {
						moveDirection = DIRECTION_SOUTHWEST;
					}
					return true;
				}

				/* fleeing */
				if (flee && canWalkTo(creaturePos, DIRECTION_EAST)) {
					// towards player, yea
					moveDirection = DIRECTION_EAST;
					return true;
				}

				/* end of fleeing */
				break;
			}

			default:
				break;
		}
	}

	return true;
}

bool Monster::isTargetNearby() const {
	return stepDuration >= 1;
}

bool Monster::isIgnoringFieldDamage() const {
	return ignoreFieldDamage;
}

bool Monster::israndomStepping() const {
	return randomStepping;
}

void Monster::setIgnoreFieldDamage(bool ignore) {
	ignoreFieldDamage = ignore;
}

bool Monster::getIgnoreFieldDamage() const {
	return ignoreFieldDamage;
}

uint16_t Monster::getRaceId() const {
	return m_monsterType->info.raceid;
}

// Hazard system
bool Monster::getHazard() const {
	return hazard;
}

void Monster::setHazard(bool value) {
	hazard = value;
}

bool Monster::getHazardSystemCrit() const {
	return hazardCrit;
}

void Monster::setHazardSystemCrit(bool value) {
	hazardCrit = value;
}

bool Monster::getHazardSystemDodge() const {
	return hazardDodge;
}

void Monster::setHazardSystemDodge(bool value) {
	hazardDodge = value;
}

bool Monster::getHazardSystemDamageBoost() const {
	return hazardDamageBoost;
}

void Monster::setHazardSystemDamageBoost(bool value) {
	hazardDamageBoost = value;
}

bool Monster::getHazardSystemDefenseBoost() const {
	return hazardDefenseBoost;
}

void Monster::setHazardSystemDefenseBoost(bool value) {
	hazardDefenseBoost = value;
}

bool Monster::getSoulPit() const {
	return soulPit;
}

void Monster::setSoulPit(bool value) {
	soulPit = value;
}

void Monster::setSoulPitStack(uint8_t stack, bool isSummon /* = false */) {
	const bool isBoss = stack == 40;
	const CreatureIconModifications_t icon = isBoss ? CreatureIconModifications_t::ReducedHealthExclamation : CreatureIconModifications_t::ReducedHealth;
	setForgeStack(stack);
	setIcon("soulpit", CreatureIcon(icon, isBoss ? 0 : stack));
	setSoulPit(true);
	setDropLoot(false);
	setSkillLoss(isBoss && !isSummon);
}

bool Monster::canWalkTo(Position pos, Direction moveDirection) {
	pos = getNextPosition(moveDirection, pos);
	if (isInSpawnRange(pos)) {
		const auto &tile = g_game().map.getTile(pos);
		if (tile && tile->getTopVisibleCreature(getMonster()) == nullptr && tile->queryAdd(0, getMonster(), 1, FLAG_PATHFINDING | FLAG_IGNOREFIELDDAMAGE) == RETURNVALUE_NOERROR) {
			return true;
		}
	}
	return false;
}

void Monster::death(const std::shared_ptr<Creature> &lastHitCreature) {
	if (monsterForgeClassification > ForgeClassifications_t::FORGE_NORMAL_MONSTER) {
		g_game().removeForgeMonster(getID(), monsterForgeClassification, true);
	}
	const auto &attackedCreature = getAttackedCreature();
	std::shared_ptr<Player> resolvedPlayer;

	if (lastHitCreature) {
		resolvedPlayer = lastHitCreature->getPlayer();
		if (!resolvedPlayer) {
			const auto &lastHitMaster = lastHitCreature->getMaster();
			if (lastHitMaster) {
				resolvedPlayer = lastHitMaster->getPlayer();
			}
		}
	}
	if (!resolvedPlayer && attackedCreature) {
		resolvedPlayer = attackedCreature->getPlayer();
		if (!resolvedPlayer) {
			const auto &attackedMaster = attackedCreature->getMaster();
			if (attackedMaster) {
				resolvedPlayer = attackedMaster->getPlayer();
			}
		}
	}

	const auto &targetPlayer = resolvedPlayer;

	for (const auto &summon : m_summons) {
		if (!summon) {
			continue;
		}
		summon->changeHealth(-summon->getHealth());
		summon->removeMaster();
	}
	m_summons.clear();

	clearTargetList();
	clearFriendList();
	onIdleStatus();

	setDead(true);

	// MCR: Fecha a janela do escudeiro (se aberta) quando a criatura morre
	if (auto master = getMaster()) {
		if (auto masterPlayer = master->getPlayer()) {
			masterPlayer->closeRemoteContainer();
		}
	}

	if (!m_monsterType) {
		return;
	}

	g_game().sendSingleSoundEffect(static_self_cast<Monster>()->getPosition(), m_monsterType->info.deathSound, getMonster());
	// ... restante da função ...


	if (!targetPlayer) {
		return;
	}

	auto [activeCharm, _] = g_iobestiary().getCharmFromTarget(targetPlayer, m_monsterType);
	if (activeCharm == CHARM_CARNAGE) {
		const auto &charm = g_iobestiary().getBestiaryCharm(activeCharm);
		const auto charmTier = targetPlayer->getCharmTier(activeCharm);
		if (charm && charm->chance[charmTier] >= normal_random(1, 10000) / 100.0) {
			g_iobestiary().parseCharmCombat(charm, targetPlayer, getMonster());
		}
	}
}

std::shared_ptr<Item> Monster::getCorpse(const std::shared_ptr<Creature> &lastHitCreature, const std::shared_ptr<Creature> &mostDamageCreature) {
	const auto &corpse = Creature::getCorpse(lastHitCreature, mostDamageCreature);
	if (corpse) {
		if (mostDamageCreature) {
			if (mostDamageCreature->getPlayer()) {
				corpse->setAttribute(ItemAttribute_t::CORPSEOWNER, mostDamageCreature->getID());
			} else {
				const auto &mostDamageCreatureMaster = mostDamageCreature->getMaster();
				if (mostDamageCreatureMaster && mostDamageCreatureMaster->getPlayer()) {
					corpse->setAttribute(ItemAttribute_t::CORPSEOWNER, mostDamageCreatureMaster->getID());
				}
			}
		}
	}
	return corpse;
}

bool Monster::isInSpawnRange(const Position &pos) const {
	if (!spawnMonster) {
		return true;
	}

	if (Monster::despawnRadius == 0) {
		return true;
	}

	if (!SpawnsMonster::isInZone(masterPos, Monster::despawnRadius, pos)) {
		return false;
	}

	if (Monster::despawnRange == 0) {
		return true;
	}

	if (Position::getDistanceZ(pos, masterPos) > Monster::despawnRange) {
		return false;
	}

	return true;
}

bool Monster::getCombatValues(int32_t &min, int32_t &max) {
	if (minCombatValue == 0 && maxCombatValue == 0) {
		return false;
	}

	min = minCombatValue;
	max = maxCombatValue;
	return true;
}

void Monster::updateLookDirection() {
	Direction newDir = getDirection();
	const auto &attackedCreature = getAttackedCreature();
	if (!getAttackedCreature()) {
		return;
	}

	const Position &pos = getPosition();
	const Position &attackedCreaturePos = attackedCreature->getPosition();
	int_fast32_t offsetx = Position::getOffsetX(attackedCreaturePos, pos);
	int_fast32_t offsety = Position::getOffsetY(attackedCreaturePos, pos);

	int32_t dx = std::abs(offsetx);
	int32_t dy = std::abs(offsety);
	if (dx > dy) {
		// look EAST/WEST
		if (offsetx < 0) {
			newDir = DIRECTION_WEST;
		} else {
			newDir = DIRECTION_EAST;
		}
	} else if (dx < dy) {
		// look NORTH/SOUTH
		if (offsety < 0) {
			newDir = DIRECTION_NORTH;
		} else {
			newDir = DIRECTION_SOUTH;
		}
	} else {
		Direction dir = getDirection();
		if (offsetx < 0 && offsety < 0) {
			if (dir == DIRECTION_SOUTH) {
				newDir = DIRECTION_WEST;
			} else if (dir == DIRECTION_EAST) {
				newDir = DIRECTION_NORTH;
			}
		} else if (offsetx < 0 && offsety > 0) {
			if (dir == DIRECTION_NORTH) {
				newDir = DIRECTION_WEST;
			} else if (dir == DIRECTION_EAST) {
				newDir = DIRECTION_SOUTH;
			}
		} else if (offsetx > 0 && offsety < 0) {
			if (dir == DIRECTION_SOUTH) {
				newDir = DIRECTION_EAST;
			} else if (dir == DIRECTION_WEST) {
				newDir = DIRECTION_NORTH;
			}
		} else {
			if (dir == DIRECTION_NORTH) {
				newDir = DIRECTION_EAST;
			} else if (dir == DIRECTION_WEST) {
				newDir = DIRECTION_SOUTH;
			}
		}
	}
	g_game().internalCreatureTurn(getMonster(), newDir);
}

void Monster::dropLoot(const std::shared_ptr<Container> &corpse, const std::shared_ptr<Creature> &) {
	if (corpse && lootDrop) {
		// Only fiendish drops sliver
		if (ForgeClassifications_t classification = getMonsterForgeClassification();
		    // Condition
		    classification == ForgeClassifications_t::FORGE_FIENDISH_MONSTER) {
			auto minSlivers = g_configManager().getNumber(FORGE_MIN_SLIVERS);
			auto maxSlivers = g_configManager().getNumber(FORGE_MAX_SLIVERS);

			auto sliverCount = static_cast<uint16_t>(uniform_random(minSlivers, maxSlivers));

			const auto &sliver = Item::CreateItem(ITEM_FORGE_SLIVER, sliverCount);
			if (g_game().internalAddItem(corpse, sliver) != RETURNVALUE_NOERROR) {
				corpse->internalAddThing(sliver);
			}
		}
		if (!this->isRewardBoss() && g_configManager().getNumber(RATE_LOOT) > 0) {
			g_callbacks().executeCallback(EventCallback_t::monsterOnDropLoot, getMonster(), corpse);
			g_callbacks().executeCallback(EventCallback_t::monsterPostDropLoot, getMonster(), corpse);
		}
	}
}

void Monster::setNormalCreatureLight() {
	internalLight = m_monsterType->info.light;
}

void Monster::drainHealth(const std::shared_ptr<Creature> &attacker, int32_t damage) {
	Creature::drainHealth(attacker, damage);

	if (damage > 0 && randomStepping) {
		ignoreFieldDamage = true;
	}

	if (isInvisible()) {
		removeCondition(CONDITION_INVISIBLE);
	}
}

void Monster::changeHealth(int32_t healthChange, bool sendHealthChange /* = true*/) {
	if (m_monsterType && !m_monsterType->info.soundVector.empty() && m_monsterType->info.soundChance >= static_cast<uint32_t>(uniform_random(1, 100))) {
		auto index = uniform_random(0, m_monsterType->info.soundVector.size() - 1);
		g_game().sendSingleSoundEffect(static_self_cast<Monster>()->getPosition(), m_monsterType->info.soundVector[index], getMonster());
	}

	// In case a player with ignore flag set attacks the monster
	setIdle(false);
	Creature::changeHealth(healthChange, sendHealthChange);
}

bool Monster::challengeCreature(const std::shared_ptr<Creature> &creature, int targetChangeCooldown) {
	if (isSummon()) {
		return false;
	}

	bool result = selectTarget(creature);
	if (result) {
		challengeFocusDuration = targetChangeCooldown;
		targetChangeTicks = 0;
		// Wheel of destiny
		const auto &player = creature ? creature->getPlayer() : nullptr;
		if (player && !player->isRemoved()) {
			player->wheel().healIfBattleHealingActive();
		}
	}
	return result;
}

bool Monster::changeTargetDistance(int32_t distance, uint32_t duration /* = 12000*/) {
	if (isSummon()) {
		return false;
	}

	if (m_monsterType->info.isRewardBoss) {
		return false;
	}

	bool shouldUpdate = m_monsterType->info.targetDistance > distance ? true : false;
	challengeMeleeDuration = duration;
	targetDistance = distance;

	if (shouldUpdate) {
		g_game().updateCreatureIcon(static_self_cast<Monster>());
	}
	return true;
}

bool Monster::isChallenged() const {
	return challengeFocusDuration > 0;
}

std::vector<CreatureIcon> Monster::getIcons() const {
	std::vector<CreatureIcon> icons;

	auto creatureIcons = Creature::getIcons();
	// this add pre existing icons, such as from forge system
	icons.insert(icons.end(), creatureIcons.begin(), creatureIcons.end());

	using enum CreatureIconModifications_t;

	if (challengeMeleeDuration > 0 && m_monsterType->info.targetDistance > targetDistance) {
		icons.emplace_back(CreatureIcon(TurnedMelee));
	}

	if (varBuffs[BUFF_DAMAGERECEIVED] > 100) {
		icons.emplace_back(CreatureIcon(HigherDamageReceived));
	}

	if (varBuffs[BUFF_DAMAGEDEALT] < 100) {
		icons.emplace_back(CreatureIcon(LowerDamageDealt));
	}

	return icons;
}

bool Monster::isImmune(ConditionType_t conditionType) const {
	return m_isImmune || m_monsterType->info.m_conditionImmunities[static_cast<size_t>(conditionType)];
}

bool Monster::isImmune(CombatType_t combatType) const {
	return m_isImmune || m_monsterType->info.m_damageImmunities[combatTypeToIndex(combatType)];
}

void Monster::setImmune(bool immune) {
	m_isImmune = immune;
}

bool Monster::isImmune() const {
	return m_isImmune;
}

float Monster::getAttackMultiplier() const {
	float multiplier = m_monsterType->getAttackMultiplier();
	if (auto stacks = getForgeStack(); stacks > 0) {
		multiplier *= (1.35 + (stacks - 1) * 0.1);
	}
	return multiplier;
}

float Monster::getDefenseMultiplier() const {
	float multiplier = m_monsterType->getDefenseMultiplier();
	if (auto stacks = getForgeStack(); stacks > 0) {
		multiplier *= (1 + (0.1 * stacks));
	}
	return multiplier;
}

bool Monster::isDead() const {
	return m_isDead;
}

void Monster::setDead(bool isDead) {
	m_isDead = isDead;
}

void Monster::getPathSearchParams(const std::shared_ptr<Creature> &creature, FindPathParams &fpp) {
	Creature::getPathSearchParams(creature, fpp);

	fpp.minTargetDist = 1;
	fpp.maxTargetDist = targetDistance;

	if (isSummon()) {
		const auto &master = getMaster();
		if (master && master == creature) {
			fpp.maxTargetDist = 2;
			fpp.fullPathSearch = true;
		} else if (targetDistance <= 1) {
			fpp.fullPathSearch = true;
		} else {
			fpp.fullPathSearch = !canUseAttack(getPosition(), creature);
		}
	} else if (isFleeing()) {
		// Distance should be higher than the client view range (MAP_MAX_CLIENT_VIEW_PORT_X/MAP_MAX_CLIENT_VIEW_PORT_Y)
		fpp.maxTargetDist = MAP_MAX_VIEW_PORT_X;
		fpp.clearSight = false;
		fpp.keepDistance = true;
		fpp.fullPathSearch = false;
	} else if (targetDistance <= 1) {
		fpp.fullPathSearch = true;
	} else {
		fpp.fullPathSearch = !canUseAttack(getPosition(), creature);
	}
}

void Monster::applyStacks() {
	// Change health based in stacks
	const auto percentToIncrement = 1 + (15 * forgeStack + 35) / 100.f;
	auto newHealth = static_cast<int32_t>(std::ceil(static_cast<float>(healthMax) * percentToIncrement));

	healthMax = newHealth;
	health = newHealth;
}

void Monster::configureForgeSystem() {
	if (!canBeForgeMonster()) {
		return;
	}

	if (monsterForgeClassification == ForgeClassifications_t::FORGE_FIENDISH_MONSTER) {
		setForgeStack(15);
		setIcon("forge", CreatureIcon(CreatureIconModifications_t::Fiendish, 0 /* don't show stacks on fiends */));
		g_game().updateCreatureIcon(static_self_cast<Monster>());
	} else if (monsterForgeClassification == ForgeClassifications_t::FORGE_INFLUENCED_MONSTER) {
		auto stack = static_cast<uint16_t>(normal_random(1, 5));
		setForgeStack(stack);
		setIcon("forge", CreatureIcon(CreatureIconModifications_t::Influenced, stack));
		g_game().updateCreatureIcon(static_self_cast<Monster>());
	}

	// Event to give Dusts
	const std::string &Eventname = "ForgeSystemMonster";
	registerCreatureEvent(Eventname);

	g_game().sendUpdateCreature(static_self_cast<Monster>());
}

bool Monster::canBeForgeMonster() const {
	return getForgeStack() == 0 && !isSummon() && !isRewardBoss() && canDropLoot() && isForgeCreature() && getRaceId() > 0;
}

bool Monster::isForgeCreature() const {
	return m_monsterType->info.isForgeCreature;
}

void Monster::setForgeMonster(bool forge) const {
	m_monsterType->info.isForgeCreature = forge;
}

uint16_t Monster::getForgeStack() const {
	return forgeStack;
}

void Monster::setForgeStack(uint16_t stack) {
	forgeStack = stack;
	applyStacks();
}

ForgeClassifications_t Monster::getMonsterForgeClassification() const {
	return monsterForgeClassification;
}

void Monster::setMonsterForgeClassification(ForgeClassifications_t classification) {
	monsterForgeClassification = classification;
}

void Monster::setTimeToChangeFiendish(time_t time) {
	timeToChangeFiendish = time;
}

time_t Monster::getTimeToChangeFiendish() const {
	return timeToChangeFiendish;
}

std::shared_ptr<MonsterType> Monster::getMonsterType() const {
	return m_monsterType;
}

void Monster::clearFiendishStatus() {
	timeToChangeFiendish = 0;
	forgeStack = 0;
	monsterForgeClassification = ForgeClassifications_t::FORGE_NORMAL_MONSTER;

	health = m_monsterType->info.health * m_monsterType->getHealthMultiplier();
	healthMax = m_monsterType->info.healthMax * m_monsterType->getHealthMultiplier();

	removeIcon("forge");
	g_game().updateCreatureIcon(static_self_cast<Monster>());
	g_game().sendUpdateCreature(static_self_cast<Monster>());
}

bool Monster::canDropLoot() const {
	return !m_monsterType->info.lootItems.empty();
}

std::vector<std::pair<int8_t, int8_t>> Monster::getPushItemLocationOptions(const Direction &direction) {
	if (direction == DIRECTION_WEST || direction == DIRECTION_EAST) {
		return { { 0, -1 }, { 0, 1 } };
	}
	if (direction == DIRECTION_NORTH || direction == DIRECTION_SOUTH) {
		return { { -1, 0 }, { 1, 0 } };
	}
	if (direction == DIRECTION_NORTHWEST) {
		return { { 0, -1 }, { -1, 0 } };
	}
	if (direction == DIRECTION_NORTHEAST) {
		return { { 0, -1 }, { 1, 0 } };
	}
	if (direction == DIRECTION_SOUTHWEST) {
		return { { 0, 1 }, { -1, 0 } };
	}
	if (direction == DIRECTION_SOUTHEAST) {
		return { { 0, 1 }, { 1, 0 } };
	}

	return {};
}

void Monster::onExecuteAsyncTasks() {
	if (hasAsyncTaskFlag(UpdateTargetList)) {
		updateTargetList();
	}

	if (hasAsyncTaskFlag(UpdateIdleStatus)) {
		updateIdleStatus();
	}

	if (hasAsyncTaskFlag(OnThink)) {
		onThink_async();
	}
}

bool Monster::checkCanApplyCharm(const std::shared_ptr<Player> &player, charmRune_t charmRune) const {
	if (!player) {
		return false;
	}

	uint16_t playerCharmRaceid = player->parseRacebyCharm(charmRune, false, 0);
	if (playerCharmRaceid != 0) {
		if (m_monsterType && playerCharmRaceid == m_monsterType->info.raceid) {
			const auto &charm = g_iobestiary().getBestiaryCharm(charmRune);
			if (charm) {
				return true;
			}
		}
	}

	return false;
}

void Monster::setCustomName(const std::string& name) {
    m_customName = name;
}

std::string Monster::getCustomName() const {
    return m_customName.empty() ? getName() : m_customName;
}

void Monster::createInventoryContainer(uint16_t size) {
    auto backpack = Item::CreateItem(2854); // ID da Mochila
    if (backpack) {
        m_inventoryContainer = backpack->getContainer();
        // Define o nome da mochila como o nome da criatura SPA
        backpack->setAttribute(ItemAttribute_t::NAME, getCustomName());
    }
}

// getInventoryContainer já está inline no monster.hpp — não coloques a definição aqui.

void Monster::dropInventoryOnDeath(const std::shared_ptr<Item> &corpse) {
    if (!m_inventoryContainer || !corpse) return;
    auto corpseContainer = corpse->getContainer();
    if (!corpseContainer) return;

    // Transfere todos os itens do inventário para o corpo
    for (const auto &item : m_inventoryContainer->getItems()) {
        corpseContainer->addThing(item);
    }
    // Liberta o container (os itens já estão no corpo)
    m_inventoryContainer = nullptr;
}



void Monster::onWalkComplete() {
    // Alimentar o grafo global com o tile atual
    if (!isSummon()) {
        auto tile = g_game().map.getTile(getPosition());
        if (tile && !tile->hasFlag(TILESTATE_BLOCKPATH)) {
            g_globalMonsterMap().addTile(getPosition(), true, false);
        }
    }

    if (m_followingWaypoints) return;

    if (m_walkingForReturn) {
        m_walkingForReturn = false;
        processarRetornoSpawn();
        return;
    }

    if (m_pursuingStairs) {
        // A transição de piso será detetada no próximo ciclo pelo onThinkMCR
        return;
    }

    setWalkingToPosition(false);

    if (m_savedFollowId != 0) {
        auto saved = g_game().getCreatureByID(m_savedFollowId);
        if (saved) {
            setFollowCreature(saved);
            m_savedFollowId = 0;
        }
    }
}

void Monster::checkStairPursuit() {
    if (m_pursuingStairs || m_returningToSpawn) return;
    if (m_hasReturnedToSpawn && !isSummon()) return;

    uint64_t now = getCurrentTimeMs();
    if (now - m_lastGlobalScanAttempt < 1500) return;
    m_lastGlobalScanAttempt = now;

    std::shared_ptr<Creature> leader;
    if (isSummon()) {
        leader = getMaster();
    } else {
        if (!m_attackedCreature.expired()) leader = m_attackedCreature.lock();
        else if (m_persistentTargetPlayer) leader = m_persistentTargetPlayer;
    }
    if (!leader || !leader->getPlayer()) return;

    Position leaderPos = leader->getPosition();
    Position myPos = getPosition();
    if (!g_globalMonsterMap().isWalkable(leaderPos)) {
        g_globalMonsterMap().addTile(leaderPos, true, false);
    }

    // ═══════════════════════════════════════════════
    // PLANEAMENTO MULTI‑PISO VIA BFS
    // ═══════════════════════════════════════════════
    auto fullPath = g_globalMonsterMap().findPath(myPos, leaderPos);
    int custoMultiPiso = fullPath.empty() ? std::numeric_limits<int>::max() : static_cast<int>(fullPath.size());

    int custoMesmoPiso = std::numeric_limits<int>::max();
    if (leaderPos.z == myPos.z) {
        std::vector<Direction> dirs;
        FindPathParams fpp;
        getPathSearchParams(getMonster(), fpp);
        fpp.fullPathSearch = true;
        fpp.clearSight = false;
        fpp.maxSearchDist = 120;
        if (getPathTo(leaderPos, dirs, fpp)) {
            custoMesmoPiso = static_cast<int>(dirs.size());
        }
    }

    if (custoMultiPiso < custoMesmoPiso) {
        std::deque<StairTransition> extractedStairs;
        Position previous = myPos;
        for (const auto& pos : fullPath) {
            if (pos.z != previous.z) {
                StairTransition trans;
                trans.origin = previous;
                trans.destination = pos;
                auto tile = g_game().map.getTile(previous);
                trans.isActive = tile && tile->hasFlag(TILESTATE_FLOORCHANGE) && tile->hasFlag(TILESTATE_BLOCKPATH);
                trans.timestamp = now;
                extractedStairs.push_back(trans);
            }
            previous = pos;
        }

        if (!extractedStairs.empty()) {
            m_stairQueue = extractedStairs;
            const auto& firstStair = m_stairQueue.front();
            m_pursuingStairs = true;
            clearWaypoints();
            m_stairOrigin          = firstStair.origin;
            m_stairDestination     = firstStair.destination;
            m_stairIsActive        = firstStair.isActive;
            m_stairStuckCount      = 0;
            m_stairTotalCycles     = 0;
            m_stairPathfindFailCount = 0;
            m_forcedMoveFailCount  = 0;
            m_currentTransitionIndex = std::numeric_limits<size_t>::max();
            m_pursuitStartTime      = now;
            m_stairAttemptStartTime = now;
            m_minDistToStair        = std::numeric_limits<int>::max();
            m_lastDistImprovementTime = now;
            m_homePosition          = myPos;
            m_pursuitDeadline       = computePursuitDeadline();
            m_sightLostTicks        = 0;
            m_savedFollowId         = leader->getID();
            setFollowCreature(nullptr);
            m_lastStuckDist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
            g_logger().info("[MCR-STAIR] {} rota multi‑piso planeada ({} passos) vs {} passos no mesmo piso. Primeira escada: {} -> {}",
                getName(), custoMultiPiso, custoMesmoPiso, m_stairOrigin.toString(), m_stairDestination.toString());
            walkToWaypoint(m_stairOrigin);
            return;
        } else {
            g_logger().info("[MCR-STAIR] {} BFS encontrou caminho mas sem transições de piso. Scan agressivo.", getName());
            g_globalMonsterMap().scanPlayerTrail(myPos, 25);
            g_globalMonsterMap().scanPlayerTrail(leaderPos, 25);
        }
    } else if (custoMesmoPiso < std::numeric_limits<int>::max()) {
        g_logger().info("[MCR-STAIR] {} rota multi‑piso não é melhor ({} passos) que a rota no mesmo piso ({} passos). Mantendo A*.",
            getName(), custoMultiPiso, custoMesmoPiso);
        return;
    }

    // ═══════════════════════════════════════════════
    // FALLBACK: ESCOLHA DE ESCADA INDIVIDUAL (GRAFO)
    // ═══════════════════════════════════════════════
    auto& filaJogador = leader->getPlayer()->getStairTransitions();
    for (const auto& trans : filaJogador) {
        g_globalMonsterMap().addStairTransition(trans.origin, trans.destination);
        g_globalMonsterMap().scanPlayerTrail(trans.origin, 12);
        g_globalMonsterMap().scanPlayerTrail(trans.destination, 12);
    }

    int targetDeltaZ = leaderPos.z - myPos.z;
    int diffToLeader = std::abs(targetDeltaZ);
    auto allTransitions = g_globalMonsterMap().getAllTransitions();
    int bestCost = std::numeric_limits<int>::max();
    Position bestOrigin, bestDest;
    bool bestIsActive = false;
    const int MAX_STAIR_DIST = 12;

    for (const auto& [origin, dest] : allTransitions) {
        if (origin.z != myPos.z) continue;
        if (dest.z == origin.z) continue;

        int deltaZ = dest.z - origin.z;
        if (targetDeltaZ != 0) {
            if ((targetDeltaZ > 0 && deltaZ <= 0) || (targetDeltaZ < 0 && deltaZ >= 0)) continue;
        }

        int newDiff = std::abs(leaderPos.z - dest.z);
        if (newDiff >= diffToLeader) continue;

        if (!canStairBeUsed(origin, deltaZ)) continue;
        if (m_recentlyFailedStairs.find(origin) != m_recentlyFailedStairs.end()) continue;

        int distToStair = std::abs(myPos.x - origin.x) + std::abs(myPos.y - origin.y);
        if (distToStair > MAX_STAIR_DIST) continue;

        auto destTile = g_game().map.getTile(dest);
        if (destTile && destTile->getTopCreature() && destTile->getTopCreature() != getMonster()) {
            if (!(dest == leaderPos)) {
                g_globalMonsterMap().addTemporaryObstacle(dest, 2000);
                continue;
            }
        }

        int distDestToPlayer = std::abs(dest.x - leaderPos.x) + std::abs(dest.y - leaderPos.y);
        int cost = distToStair + distDestToPlayer + (newDiff * 15);

        if (cost < bestCost) {
            bestCost = cost;
            bestOrigin = origin;
            bestDest = dest;
            auto tile = g_game().map.getTile(origin);
            bestIsActive = tile && tile->hasFlag(TILESTATE_FLOORCHANGE);
        }
    }

    if (bestCost < std::numeric_limits<int>::max()) {
        // Anti‑ping‑pong
        if (m_lastUsedStairOrigin == bestOrigin && m_lastUsedStairDest == bestDest &&
            now - m_lastSuccessfulTeleport < 5000) {
            m_sameStairRepeatCount++;
            if (m_sameStairRepeatCount >= 3) {
                g_logger().info("[MCR-STAIR] {} ping‑pong detetado na escada {}, forçando cooldown longo.",
                    getName(), bestOrigin.toString());
                m_recentlyFailedStairs[bestOrigin] = now + 45000;
                m_sameStairRepeatCount = 0;
                clearStairPursuit();
                return;
            }
        } else {
            m_sameStairRepeatCount = 0;
        }

        if (!g_globalMonsterMap().isWalkable(bestDest)) {
            g_globalMonsterMap().scanArea(bestDest, 5, 1, 1, 100, filaJogador);
        }

        m_pursuingStairs = true;
        clearWaypoints();
        m_stairOrigin          = bestOrigin;
        m_stairDestination     = bestDest;
        m_stairIsActive        = bestIsActive;
        m_stairStuckCount      = 0;
        m_stairTotalCycles     = 0;
        m_stairPathfindFailCount = 0;
        m_forcedMoveFailCount  = 0;
        m_currentTransitionIndex = std::numeric_limits<size_t>::max();
        m_pursuitStartTime      = now;
        m_stairAttemptStartTime = now;
        m_minDistToStair        = std::numeric_limits<int>::max();
        m_lastDistImprovementTime = now;
        m_homePosition          = myPos;
        m_pursuitDeadline       = computePursuitDeadline();
        m_sightLostTicks        = 0;
        m_savedFollowId         = leader->getID();
        setFollowCreature(nullptr);
        m_lastStuckDist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
        g_logger().info("[MCR-STAIR] {} usou escada alternativa do grafo: {} -> {} (custo={})",
            getName(), bestOrigin.toString(), bestDest.toString(), bestCost);
        walkToWaypoint(m_stairOrigin);
        return;
    }

    // ═══════════════════════════════════════════════
    // FALLBACK: ESCADAS DO JOGADOR
    // ═══════════════════════════════════════════════
    auto& fila = leader->getPlayer()->getStairTransitions();
    if (!fila.empty()) {
        if (m_nextStairIndex == std::numeric_limits<size_t>::max())
            m_nextStairIndex = isSummon() ? fila.size() : 0;

        size_t idx = m_nextStairIndex;
        bestCost = std::numeric_limits<int>::max();
        size_t bestIdx = std::numeric_limits<size_t>::max();

        while (idx < fila.size()) {
            const StairTransition& trans = fila[idx];
            if (trans.origin.z == myPos.z && trans.destination.z == leaderPos.z) {
                if (m_recentlyFailedStairs.find(trans.origin) != m_recentlyFailedStairs.end()) {
                    ++idx;
                    continue;
                }
                if (!g_globalMonsterMap().isWalkable(leaderPos)) {
                    g_globalMonsterMap().addTile(leaderPos, true, false);
                }
                if (leaderPos.z == myPos.z) {
                    FindPathParams fpp;
                    getPathSearchParams(getMonster(), fpp);
                    std::vector<Direction> dummy;
                    if (getPathTo(leaderPos, dummy, fpp)) {
                        return;
                    }
                }
                auto pathToStair = g_globalMonsterMap().findPath(myPos, trans.origin);
                int distToOrigin = pathToStair.empty()
                    ? (std::abs(myPos.x - trans.origin.x) + std::abs(myPos.y - trans.origin.y))
                    : static_cast<int>(pathToStair.size());
                int distDestToPlayer = std::abs(trans.destination.x - leaderPos.x)
                                     + std::abs(trans.destination.y - leaderPos.y);
                int cost = distToOrigin + distDestToPlayer;
                if (cost < bestCost) { bestCost = cost; bestIdx = idx; }
            }
            ++idx;
        }

        if (bestIdx != std::numeric_limits<size_t>::max()) {
            const StairTransition& trans = fila[bestIdx];
            if (m_recentlyFailedStairs.find(trans.origin) != m_recentlyFailedStairs.end()) {
                g_logger().info("[MCR-DEBUG] {} todas as escadas do jogador falharam, retornando ao spawn", getName());
                if (!isSummon()) {
                    m_homePosition = m_spawnPosition;
                    iniciarRetornoSpawn();
                }
                return;
            }

            // Anti‑ping‑pong
            if (m_lastUsedStairOrigin == trans.origin && m_lastUsedStairDest == trans.destination &&
                now - m_lastSuccessfulTeleport < 5000) {
                m_sameStairRepeatCount++;
                if (m_sameStairRepeatCount >= 3) {
                    g_logger().info("[MCR-STAIR] {} ping‑pong detetado na escada {}, forçando cooldown longo.",
                        getName(), trans.origin.toString());
                    m_recentlyFailedStairs[trans.origin] = now + 45000;
                    m_sameStairRepeatCount = 0;
                    clearStairPursuit();
                    return;
                }
            } else {
                m_sameStairRepeatCount = 0;
            }

            m_pursuingStairs = true;
            clearWaypoints();
            m_stairOrigin = trans.origin;
            m_stairDestination = trans.destination;
            m_stairIsActive = trans.isActive;
            m_stairStuckCount = 0;
            m_stairTotalCycles = 0;
            m_stairPathfindFailCount = 0;
            m_currentTransitionIndex = bestIdx;
            m_pursuitStartTime = now;
            m_stairAttemptStartTime = now;
            m_minDistToStair = std::numeric_limits<int>::max();
            m_lastDistImprovementTime = now;
            m_homePosition = myPos;
            m_pursuitDeadline = computePursuitDeadline();
            m_sightLostTicks = 0;
            m_savedFollowId = leader->getID();
            setFollowCreature(nullptr);
            m_lastStuckDist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
            g_logger().info("[MCR-STAIR] {} perseguição INICIADA. stairOrigin={} stairDest={} isActive={} (melhor índice {})",
                getName(), m_stairOrigin.toString(), m_stairDestination.toString(), m_stairIsActive ? "sim" : "não", bestIdx);
            walkToWaypoint(m_stairOrigin);
            return;
        }
    } else {
        // Fila vazia
        if (isSummon()) {
            auto path = g_globalMonsterMap().findPath(myPos, leaderPos);
            if (!path.empty()) {
                clearWaypoints();
                m_waypoints = path;
                m_waypointIndex = 0;
                m_followingWaypoints = true;
                m_savedFollowId = leader->getID();
                setFollowCreature(nullptr);
                g_logger().info("[MCR-STAIR] {} (summon) encontrou rota cognitiva até ao mestre.", getName());
                return;
            }
            if (leaderPos.z != myPos.z) {
                bool foundStair = false;
                auto allTrans = g_globalMonsterMap().getAllTransitions();
                for (const auto& [origin, dest] : allTrans) {
                    if (origin.z == myPos.z && dest.z == leaderPos.z) {
                        m_pursuingStairs = true;
                        clearWaypoints();
                        m_stairOrigin = origin;
                        m_stairDestination = dest;
                        auto tile = g_game().map.getTile(origin);
                        m_stairIsActive = tile && tile->hasFlag(TILESTATE_FLOORCHANGE) && tile->hasFlag(TILESTATE_BLOCKPATH);
                        m_stairStuckCount = 0;
                        m_stairTotalCycles = 0;
                        m_stairPathfindFailCount = 0;
                        m_forcedMoveFailCount = 0;
                        m_savedFollowId = leader->getID();
                        setFollowCreature(nullptr);
                        foundStair = true;
                        g_logger().info("[MCR-STAIR] {} (summon) encontrou escada alternativa pelo grafo para alcançar o mestre.", getName());
                        walkToWaypoint(m_stairOrigin);
                        break;
                    }
                }
                if (foundStair) return;
            }
            g_game().internalTeleport(static_self_cast<Monster>(), leaderPos);
            g_logger().info("[MCR-STAIR] {} (summon) teleportou para o mestre (fila vazia).", getName());
        }
    }

    // ═══════════════════════════════════════════════
    // ÚLTIMO RECURSO: PROCURA DIRECTA NO MAPA REAL
    // ═══════════════════════════════════════════════
    Position realStair = findStairNearReal(leaderPos, 12);
    if (realStair.x != 0 || realStair.y != 0) {
        int deltaZ = 0;
        auto tile = g_game().map.getTile(realStair);
        if (tile->hasFlag(TILESTATE_FLOORCHANGE_DOWN)) deltaZ = -1;
        else if (tile->hasFlag(TILESTATE_FLOORCHANGE_NORTH) || tile->hasFlag(TILESTATE_FLOORCHANGE_SOUTH) ||
                 tile->hasFlag(TILESTATE_FLOORCHANGE_EAST)  || tile->hasFlag(TILESTATE_FLOORCHANGE_WEST)  ||
                 tile->hasFlag(TILESTATE_FLOORCHANGE_SOUTH_ALT) || tile->hasFlag(TILESTATE_FLOORCHANGE_EAST_ALT)) deltaZ = 1;
        else deltaZ = (leaderPos.z > myPos.z) ? 1 : -1;

        Position dest = realStair;
        dest.z += deltaZ;

        m_pursuingStairs = true;
        clearWaypoints();
        m_stairOrigin = realStair;
        m_stairDestination = dest;
        m_stairIsActive = (tile && tile->hasFlag(TILESTATE_FLOORCHANGE) && tile->hasFlag(TILESTATE_BLOCKPATH));
        m_stairStuckCount = 0;
        m_stairTotalCycles = 0;
        m_stairPathfindFailCount = 0;
        m_forcedMoveFailCount = 0;
        m_pursuitStartTime = now;
        m_stairAttemptStartTime = now;
        m_minDistToStair = std::numeric_limits<int>::max();
        m_lastDistImprovementTime = now;
        m_homePosition = myPos;
        m_pursuitDeadline = computePursuitDeadline();
        m_sightLostTicks = 0;
        m_savedFollowId = leader->getID();
        setFollowCreature(nullptr);
        m_lastStuckDist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
        g_logger().info("[MCR-STAIR] {} usou escada real do mapa: {} -> {}",
            getName(), realStair.toString(), dest.toString());
        walkToWaypoint(m_stairOrigin);
        return;
    }
}

void Monster::walkToWaypoint(const Position& target) {
    // Se já está a seguir waypoints, não faz nada (será tratado no onThinkMCR)
    if (m_followingWaypoints) {
        g_logger().info("[MCR-WALK] {} já a seguir waypoints, ignorando walkToWaypoint.", getName());
        return;
    }

    Position actualTarget = target;

    // Ajuste para escadas: se longe, usa adjacente; se perto, pisa a escada
    if (m_pursuingStairs && target == m_stairOrigin) {
        int distToStair = std::abs(getPosition().x - target.x) + std::abs(getPosition().y - target.y);
        g_logger().info("[MCR-WALK] {} perseguindo escada, distância: {}", getName(), distToStair);
        if (distToStair == 1) {
            // Já adjacente: tenta pisar a escada directamente
            Direction dir = getDirectionTo(getPosition(), target);
            if (dir != DIRECTION_NONE) {
                Position oldPos = getPosition();
                g_game().internalMoveCreature(static_self_cast<Monster>(), dir, 0);
                if (getPosition() != oldPos) {
                    return; // movimento bem-sucedido, transição pode ocorrer no próximo ciclo
                }
            }
            // Se falhar, tenta o caminho normal (A*)
        } else if (distToStair > 1) {
            // Procura tile adjacente
            static const int dx[] = {-1, 1, 0, 0};
            static const int dy[] = {0, 0, -1, 1};
            for (int i = 0; i < 4; ++i) {
                Position adj(target.x + dx[i], target.y + dy[i], target.z);
                auto tile = g_game().map.getTile(adj);
                if (tile && !tile->hasFlag(TILESTATE_BLOCKPATH) && !tile->hasFlag(TILESTATE_BLOCKSOLID)) {
                    actualTarget = adj;
                    g_logger().info("[MCR-WALK] {} ajustando alvo para adjacente: {}", getName(), actualTarget.toString());
                    break;
                }
            }
        }
    }

    // Tenta A* nativo com alcance alargado
    std::vector<Direction> listDir;
    FindPathParams fpp;
    getPathSearchParams(getMonster(), fpp);
    fpp.minTargetDist = 0;
    fpp.maxTargetDist = 1;
    fpp.fullPathSearch = true;
    fpp.clearSight = false;
    fpp.maxSearchDist = 120;

    if (getPathTo(actualTarget, listDir, fpp) && !listDir.empty()) {
        g_logger().info("[MCR-WALK] {} A* encontrou caminho com {} passos. Iniciando caminhada.", getName(), listDir.size());
        startAutoWalk(listDir);
        setWalkingToPosition(true);
        if (!isSummon()) {
            m_lastDistImprovementTime = getCurrentTimeMs();
            m_minDistToStair = std::abs(getPosition().x - actualTarget.x) +
                               std::abs(getPosition().y - actualTarget.y);
        }
        return;
    }
    g_logger().info("[MCR-WALK] {} A* falhou para {} (dist={}). Tentando mapa cognitivo.",
        getName(), actualTarget.toString(),
        std::abs(getPosition().x - actualTarget.x) + std::abs(getPosition().y - actualTarget.y));

    // A* falhou – tenta obter uma rota cognitiva e converter em waypoints
    auto fullPath = g_globalMonsterMap().findPath(getPosition(), actualTarget);
    if (!fullPath.empty()) {
        // Validação do primeiro waypoint
        auto firstWp = fullPath.front();
        std::vector<Direction> testDir;
        FindPathParams fppTest;
        getPathSearchParams(getMonster(), fppTest);
        fppTest.minTargetDist = 0;
        fppTest.maxTargetDist = 0;
        fppTest.fullPathSearch = true;
        fppTest.clearSight = false;
        fppTest.maxSearchDist = 120;

        if (!getPathTo(firstWp, testDir, fppTest)) {
            auto approach = g_globalMonsterMap().findNearestApproachTo(getPosition(), firstWp);
            if (!approach.empty()) {
                fullPath = approach;
                g_logger().info("[MCR-WALK] {} waypoint inicial inalcançável. Usando aproximação máxima ({} passos).",
                    getName(), approach.size());
            } else {
                g_logger().info("[MCR-WALK] {} waypoint inicial inalcançável e sem aproximação. Abortando waypoints.", getName());
                setWalkingToPosition(false);
                clearWaypoints();
                return;
            }
        }

        m_waypoints.clear();
        bool hasFloorChange = false;
        for (size_t i = 1; i < fullPath.size(); ++i) {
            if (fullPath[i].z != fullPath[i-1].z) {
                hasFloorChange = true;
                break;
            }
        }

        if (hasFloorChange) {
            // Modo multi‑piso: extrai apenas transições + início/fim
            m_waypoints.push_back(fullPath.front());
            for (size_t i = 1; i < fullPath.size(); ++i) {
                if (fullPath[i].z != fullPath[i-1].z) {
                    m_waypoints.push_back(fullPath[i-1]);
                    m_waypoints.push_back(fullPath[i]);
                }
            }
            m_waypoints.push_back(fullPath.back());
        } else {
            m_waypoints = fullPath;
        }

        // Remove duplicados consecutivos e o ponto de partida
        m_waypoints.erase(std::unique(m_waypoints.begin(), m_waypoints.end()), m_waypoints.end());
        if (!m_waypoints.empty() && m_waypoints.front() == getPosition()) {
            m_waypoints.erase(m_waypoints.begin());
        }

        if (!m_waypoints.empty()) {
            m_waypointIndex = 0;
            m_followingWaypoints = true;
            g_logger().info("[MCR-WALK] {} gerou {} waypoints. Primeiro: {}",
                getName(), m_waypoints.size(), m_waypoints.front().toString());
            return;
        } else {
            g_logger().info("[MCR-WALK] {} caminho cognitivo encontrado mas sem waypoints válidos.", getName());
        }
    }

    // Aproximação máxima
    auto approachPath = g_globalMonsterMap().findNearestApproachTo(getPosition(), actualTarget);
    if (!approachPath.empty()) {
        m_waypoints = approachPath;
        if (!m_waypoints.empty() && m_waypoints.front() == getPosition()) {
            m_waypoints.erase(m_waypoints.begin());
        }
        if (!m_waypoints.empty()) {
            m_waypointIndex = 0;
            m_followingWaypoints = true;
            g_logger().info("[MCR-WALK] {} usando aproximação máxima com {} waypoints.", getName(), m_waypoints.size());
            return;
        }
    }

    g_logger().info("[MCR-WALK] {} falha total: nem A* nem BFS encontraram caminho. Desistindo.", getName());
    setWalkingToPosition(false);
}

void Monster::iniciarRetornoSpawn() {
    // ═══ LIMPA ESTADO DE PERSEGUIÇÃO E CERCAMENTO ═══
    clearStairPursuit();
    m_persistentTargetPlayer.reset();

    // Reseta contadores de falhas para o retorno começar limpo
    m_flankingFailCount = 0;
    m_idleFailCount = 0;
    m_stuckReturnTargetFails = 0;
    m_stuckReturnTarget = Position();

    if (m_returnPath.empty()) {
        g_logger().info("[MCR-STAIR] {} sem caminho de retorno, a voltar ao comportamento normal.", getName());
        return;
    }

    std::reverse(m_returnPath.begin(), m_returnPath.end());
    m_returningToSpawn = true;
    processarRetornoSpawn();
}

void Monster::processarRetornoSimples() {
    if (!m_returningHome) return;

    m_flankingFailCount = 0;
    m_idleFailCount = 0;

    if (isWalkingToPosition()) {
        if (m_returnWalkStartTime == 0) {
            m_returnWalkStartTime = getCurrentTimeMs();
        }
        if (getCurrentTimeMs() - m_returnWalkStartTime > 5000) {
            g_logger().info("[MCR-RETURN] {} caminhada de retorno simples excedeu 5s, cancelando.", getName());
            setIdle(true);
            setWalkingToPosition(false);
            m_walkingForReturn = false;
            m_returnWalkStartTime = 0;
            if (!m_returnPath.empty()) {
                m_returningHome = false;
                m_returningToSpawn = true;
                processarRetornoSpawn();
                return;
            }
            m_totalReturnFails++;
            if (m_totalReturnFails > 10) {
                g_logger().info("[MCR-RETURN] {} demasiadas falhas no retorno simples, deambulando.", getName());
                m_returningHome = false;
                m_hasReturnedToSpawn = false;
                m_wrongFloorCycles = 0;
                tryIdleWander();
                return;
            }
            return;
        }
        m_totalReturnFails = 0;
        return;
    }

    if (m_followingWaypoints) return;

    m_returnWalkStartTime = 0;
    Position myPos = getPosition();

    if (myPos.z != m_homePosition.z) {
        if (!m_returnPath.empty()) {
            m_returningHome = false;
            m_returningToSpawn = true;
            processarRetornoSpawn();
            return;
        }
        // Teleporte de último recurso após 30 ciclos preso no piso errado
        m_wrongFloorCycles++;
        if (m_wrongFloorCycles > 15) {
            g_logger().info("[MCR-RETURN] {} preso no piso errado há 30 ciclos. Teleportando para o spawn.", getName());
            g_game().internalTeleport(static_self_cast<Monster>(), m_spawnPosition);
            m_returningHome = false;
            m_wrongFloorCycles = 0;
            m_hasReturnedToSpawn = true;
            return;
        }
        g_logger().info("[MCR-RETURN] {} está noutro piso sem escadas de retorno, aguardando.", getName());
        tryIdleWander();
        return;
    }

    if (myPos == m_homePosition) {
        g_logger().info("[MCR-RETURN] {} chegou a casa.", getName());
        m_returningHome = false;
        m_walkingForReturn = false;
        m_totalReturnFails = 0;
        m_wrongFloorCycles = 0;
        m_hasReturnedToSpawn = true;
        m_nextStairIndex = std::numeric_limits<size_t>::max();
        return;
    }

    uint64_t now = getCurrentTimeMs();
    if (now - m_lastGlobalScanAttempt < 1000) return;
    m_lastGlobalScanAttempt = now;

    int distToHome = std::abs(myPos.x - m_homePosition.x) + std::abs(myPos.y - m_homePosition.y);

    if (distToHome <= 1) {
        Direction dir = getDirectionTo(myPos, m_homePosition);
        if (dir != DIRECTION_NONE) {
            Position oldPos = myPos;
            g_game().internalMoveCreature(static_self_cast<Monster>(), dir, 0);
            if (getPosition() == m_homePosition) {
                g_logger().info("[MCR-RETURN] {} chegou a casa.", getName());
                m_returningHome = false;
                m_walkingForReturn = false;
                m_totalReturnFails = 0;
                m_wrongFloorCycles = 0;
                m_hasReturnedToSpawn = true;
                return;
            }
            if (getPosition() == oldPos) {
                invalidateTileBlocked(getNextPosition(dir, myPos));
                m_totalReturnFails++;
            } else {
                m_totalReturnFails = 0;
            }
        } else {
            m_totalReturnFails++;
        }
        if (m_totalReturnFails > 10) {
            g_logger().info("[MCR-RETURN] {} não consegue alcançar casa, deambulando.", getName());
            m_returningHome = false;
            m_hasReturnedToSpawn = false;
            m_wrongFloorCycles = 0;
            tryIdleWander();
            return;
        }
        return;
    }

    std::vector<Direction> listDir;
    FindPathParams fpp;
    getPathSearchParams(getMonster(), fpp);
    fpp.minTargetDist = 0;
    fpp.maxTargetDist = 0;
    fpp.fullPathSearch = true;
    fpp.clearSight = false;
    fpp.maxSearchDist = 100;

    if (getPathTo(m_homePosition, listDir, fpp) && !listDir.empty()) {
        startAutoWalk(listDir);
        m_walkingForReturn = true;
        m_totalReturnFails = 0;
        return;
    }

    walkToWaypoint(m_homePosition);
    m_walkingForReturn = true;

    if (m_followingWaypoints) return;

    m_totalReturnFails++;

    if (m_totalReturnFails > 10) {
        g_logger().info("[MCR-RETURN] {} demasiadas falhas no retorno simples, deambulando.", getName());
        m_returningHome = false;
        m_hasReturnedToSpawn = false;
        m_wrongFloorCycles = 0;
        tryIdleWander();
        return;
    }

    Direction dir = getDirectionTo(myPos, m_homePosition);
    if (dir != DIRECTION_NONE) {
        Position oldPos = myPos;
        g_game().internalMoveCreature(static_self_cast<Monster>(), dir, 0);
        if (getPosition() == oldPos) {
            invalidateTileBlocked(getNextPosition(dir, myPos));
        } else {
            m_totalReturnFails = 0;
        }
        m_walkingForReturn = true;
    } else {
        m_totalReturnFails++;
    }
}

bool Monster::isPlayerNearby(int radius) {
    for (const auto& entry : g_game().getPlayers()) {
        auto& player = entry.second;   // entry é std::pair<key, value>
        if (player && player->getPosition().z == getPosition().z) {
            if (std::abs(player->getPosition().x - getPosition().x) <= radius &&
                std::abs(player->getPosition().y - getPosition().y) <= radius) {
                return true;
            }
        }
    }
    return false;
}

void Monster::processarRetornoSpawn() {
    if (!m_returningToSpawn || m_returnPath.empty()) {
        if (m_returningToSpawn) {
            g_logger().info("[MCR-RETURN] {} sem mais escadas no caminho de retorno, a caminhar para casa.", getName());
            m_returningToSpawn = false;
            m_walkingForReturn = false;
            m_nextStairIndex = std::numeric_limits<size_t>::max();
            m_homePosition = m_spawnPosition;
            m_returningHome = true;
            processarRetornoSimples();
            return;
        }
        m_returningToSpawn = false;
        m_walkingForReturn = false;
        m_nextStairIndex = std::numeric_limits<size_t>::max();
        clearStairPursuit();
        m_totalReturnFails = 0;
        m_stuckReturnTargetFails = 0;
        m_returnWalkStartTime = 0;
        return;
    }

    if (isWalkingToPosition()) {
        if (m_returnWalkStartTime == 0) {
            m_returnWalkStartTime = getCurrentTimeMs();
        }
        if (getCurrentTimeMs() - m_returnWalkStartTime > 5000) {
            g_logger().info("[MCR-RETURN] {} caminhada de retorno excedeu 5s, cancelando.", getName());
            setIdle(true);
            setWalkingToPosition(false);
            m_walkingForReturn = false;
            m_returnWalkStartTime = 0;
            if (!m_returnPath.empty()) {
                m_returnPath.pop_back();
                if (m_returnPath.empty()) {
                    g_logger().info("[MCR-RETURN] {} sem mais escadas, tentando chegar a casa a pé.", getName());
                    m_returningToSpawn = false;
                    m_homePosition = m_spawnPosition;
                    m_returningHome = true;
                    processarRetornoSimples();
                    return;
                }
                processarRetornoSpawn();
            }
            return;
        }
        m_totalReturnFails = 0;
        m_stuckReturnTargetFails = 0;
        return;
    }

    if (m_followingWaypoints) return;

    m_returnWalkStartTime = 0;

    StairTransition& trans = m_returnPath.back();
    Position myPos = getPosition();

    if (myPos == trans.destination) {
        bool shouldTeleport = false;
        auto tile = g_game().map.getTile(myPos);
        if (tile) {
            if (tile->hasFlag(TILESTATE_BLOCKPATH)) {
                shouldTeleport = true;
            } else {
                g_logger().info("[MCR-RETURN] {} a caminhar para escada de retorno em {}.", getName(), trans.origin.toString());
                walkToWaypoint(trans.origin);
                m_walkingForReturn = true;
                return;
            }
        } else {
            shouldTeleport = true;
        }

        if (shouldTeleport) {
            // Validação canónica da escada de retorno
            int deltaZ = trans.origin.z - trans.destination.z;
            if (!canStairBeUsed(trans.origin, deltaZ)) {
                g_logger().info("[MCR-RETURN] {} escada de retorno inválida (validação canónica), a avançar.", getName());
                m_returnPath.pop_back();
                m_totalReturnFails = 0;
                if (m_returnPath.empty()) {
                    m_returningToSpawn = false;
                    m_homePosition = m_spawnPosition;
                    m_returningHome = true;
                    processarRetornoSimples();
                } else {
                    processarRetornoSpawn();
                }
                return;
            }

            g_logger().info("[MCR-RETURN] {} a usar escada de retorno activa para {}.", getName(), trans.origin.toString());
            g_game().internalTeleport(static_self_cast<Monster>(), trans.origin);
            m_returnPath.pop_back();
            m_totalReturnFails = 0;
            if (m_returnPath.empty()) {
                g_logger().info("[MCR-RETURN] {} chegou ao destino final das escadas, a caminhar para casa.", getName());
                m_returningToSpawn = false;
                m_homePosition = m_spawnPosition;
                m_returningHome = true;
                processarRetornoSimples();
                return;
            }
            processarRetornoSpawn();
            return;
        }
        return;
    }

    uint64_t now = getCurrentTimeMs();
    const uint64_t returnThrottle = (m_stuckReturnTargetFails > 0) ? 800 : 1000;
    if (now - m_lastGlobalScanAttempt < returnThrottle) return;
    m_lastGlobalScanAttempt = now;

    walkToWaypoint(trans.destination);
    m_walkingForReturn = true;

    if (m_followingWaypoints) {
        m_stuckReturnTargetFails = 0;
        return;
    }

    if (!isWalkingToPosition() && !m_followingWaypoints) {
        if (trans.destination == m_stuckReturnTarget) {
            ++m_stuckReturnTargetFails;
        } else {
            m_stuckReturnTarget = trans.destination;
            m_stuckReturnTargetFails = 1;
        }

        if (m_stuckReturnTargetFails >= 3) {
            g_logger().info("[MCR-RETURN] {} tile {} bloqueado após 3 falhas consecutivas, a avançar no caminho.",
                getName(), trans.destination.toString());
            forceInvalidateTileInGraph(trans.destination);
            m_stuckReturnTargetFails = 0;
            m_stuckReturnTarget = Position();
            m_walkingForReturn = false;
            m_totalReturnFails++;
            if (m_totalReturnFails > 10) {
                g_logger().info("[MCR-RETURN] {} demasiadas falhas no retorno, reiniciando percurso.", getName());
                m_totalReturnFails = 0;
                m_stuckReturnTargetFails = 0;
                iniciarRetornoSpawn();
                return;
            }
            return;
        }

        Direction dir = getDirectionTo(myPos, trans.destination);
        if (dir != DIRECTION_NONE) {
            m_totalReturnFails++;

            if (m_totalReturnFails >= 5) {
                g_globalMonsterMap().scanPlayerTrail(myPos, 25);
                g_globalMonsterMap().scanPlayerTrail(trans.destination, 25);
                auto path = g_globalMonsterMap().findPath(myPos, trans.destination);
                if (path.empty()) {
                    path = g_globalMonsterMap().findNearestApproachTo(myPos, trans.destination);
                }
                if (!path.empty()) {
                    g_logger().info("[MCR-RETURN] {} usando mapa cognitivo para retornar.", getName());
                    m_waypoints = path;
                    m_waypointIndex = 0;
                    m_followingWaypoints = true;
                    m_walkingForReturn = false;
                    m_totalReturnFails = 0;
                    m_leaderDistanceStuckCycles = 0;
                    m_lastDistToLeader = (m_spawnPosition.x != 0) ? (std::abs(getPosition().x - m_spawnPosition.x) + std::abs(getPosition().y - m_spawnPosition.y)) : 0;
                    return;
                }
            }

            if (m_totalReturnFails > 10) {
                g_logger().info("[MCR-RETURN] {} demasiadas falhas no retorno, reiniciando percurso.", getName());
                m_totalReturnFails = 0;
                m_stuckReturnTargetFails = 0;
                iniciarRetornoSpawn();
                return;
            }

            Position oldPos = myPos;
            g_game().internalMoveCreature(static_self_cast<Monster>(), dir, 0);
            if (getPosition() == oldPos) {
                invalidateTileBlocked(getNextPosition(dir, myPos));
                g_logger().info("[MCR-RETURN] {} movimento falhou, tile invalidado no grafo.", getName());
            } else {
                m_totalReturnFails = 0;
            }
            m_walkingForReturn = true;
        } else {
            m_totalReturnFails++;
            if (m_totalReturnFails > 10) {
                g_logger().info("[MCR-RETURN] {} demasiadas falhas no retorno, reiniciando percurso.", getName());
                m_totalReturnFails = 0;
                m_stuckReturnTargetFails = 0;
                iniciarRetornoSpawn();
                return;
            }
            m_walkingForReturn = false;
        }
    } else {
        m_totalReturnFails = 0;
        m_stuckReturnTargetFails = 0;
    }
}

// ============================================================
//  Novas funções de suporte ao GlobalMonsterMap
// ============================================================
void Monster::tryUseGlobalMap() {
    if (m_followingWaypoints || !m_pursuingStairs) return;
    Position myPos = getPosition();
    int dist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
    if (dist <= 1) return;

    uint64_t now = getCurrentTimeMs();
    if (now - m_lastGlobalScanAttempt < 1500) return;
    m_lastGlobalScanAttempt = now;

    std::shared_ptr<Creature> leader;
    if (isSummon()) leader = getMaster();
    else {
        leader = !m_attackedCreature.expired() ? m_attackedCreature.lock() : nullptr;
        if (!leader) leader = m_persistentTargetPlayer;
    }
    if (!leader) return;
    auto player = leader->getPlayer();
    if (!player) return;

    for (const auto& trans : player->getStairTransitions())
        g_globalMonsterMap().addStairTransition(trans.origin, trans.destination);

    size_t added = 0;
    if (mcrTryScanArea(myPos, 15, 1, 1, 500, player->getStairTransitions(), &added)) {
        if (added > 0) {
            auto path = g_globalMonsterMap().findPath(myPos, m_stairOrigin);
            if (!path.empty()) {
                clearWaypoints();
                m_waypoints = path;
                m_waypointIndex = 0;
                m_followingWaypoints = true;
                m_leaderDistanceStuckCycles = 0;
                m_lastDistToLeader = leader ? (std::abs(myPos.x - leader->getPosition().x) + std::abs(myPos.y - leader->getPosition().y)) : 0;
                m_lastGlobalPathStart = getCurrentTimeMs();
                return;
            }
        }
    }

    if (now - m_lastExtendedScanAttempt >= 10000) {
        m_lastExtendedScanAttempt = now;
        size_t added2 = 0;
        if (mcrTryScanArea(myPos, 18, 1, 1, 1000, player->getStairTransitions(), &added2)) {
            if (added2 > 0) {
                auto path = g_globalMonsterMap().findPath(myPos, m_stairOrigin);
                if (!path.empty()) {
                    clearWaypoints();
                    m_waypoints = path;
                    m_waypointIndex = 0;
                    m_followingWaypoints = true;
                    m_leaderDistanceStuckCycles = 0;
                    m_lastDistToLeader = leader ? (std::abs(myPos.x - leader->getPosition().x) + std::abs(myPos.y - leader->getPosition().y)) : 0;
                    m_lastGlobalPathStart = getCurrentTimeMs();
                }
            }
        }
    }
}

void Monster::updateEngagement(bool playerVisible, bool damagedPlayer, bool tookDamage) {
    // Obtém o líder de forma segura (igual ao onThinkMCR)
    std::shared_ptr<Creature> leader;
    if (!m_attackedCreature.expired()) {
        leader = m_attackedCreature.lock();
    }
    if (!leader) {
        leader = m_persistentTargetPlayer;
    }

    if (!leader) {
        // Sem alvo, decaimento rápido
        m_engagement = std::max(0, m_engagement - 3);
        return;
    }

    if (damagedPlayer || tookDamage) {
        m_engagement = std::min(100, m_engagement + 3);
    } else if (playerVisible) {
        // Se o líder está muito próximo, sobe mais rápido
        int dist = std::abs(getPosition().x - leader->getPosition().x)
                 + std::abs(getPosition().y - leader->getPosition().y);
        int gain = (dist <= 3) ? 3 : 1;   // +3 se perto, +1 se longe
        m_engagement = std::min(100, m_engagement + gain);
    } else {
        m_engagement = std::max(0, m_engagement - 3);
    }
}

uint64_t Monster::computePursuitDeadline() {
    int baseTimeMs = 30000;               // sobe de 25000 para 30000
    int engagementTimeMs = m_engagement * 500; // sobe de 350 para 500 (max 50s)
    int totalMs = baseTimeMs + engagementTimeMs;
    if (totalMs > 60000) totalMs = 60000;  // máximo de 60 segundos
    return getCurrentTimeMs() + totalMs;
}

void Monster::resetEngagement() {
    m_engagement = 0;
}

void Monster::handleSummonMasterTeleport(Player* player) {
    mcrSafeTeleport(player->getPosition());
}

Player* Monster::getTargetPlayer() {
    if (!m_attackedCreature.expired()) {
        auto creature = m_attackedCreature.lock();
        if (creature) {
            Player* targetPlayer = creature->getPlayer().get();
            if (targetPlayer) return targetPlayer;          // "targetPlayer", não "player"
        }
    }
    return m_persistentTargetPlayer.get();
}

bool Monster::isPlayerTransition(Player* player, const Position& from, const Position& to) {
    if (!player) return false;
    for (const auto& trans : player->getStairTransitions()) {
        if (trans.origin == from && trans.destination == to) return true;
    }
    return false;
}

void Monster::tryProactiveGlobalPursuit() {
    if (m_followingWaypoints || m_returningToSpawn || m_returningHome) return;

    uint64_t throttle = m_pursuingStairs ? 10000 : 5000;
    uint64_t now = getCurrentTimeMs();
    if (now - m_lastRouteRequestTime < throttle) return;
    m_lastRouteRequestTime = now;

    int nearbyMonsters = 0;
    for (int dx = -5; dx <= 5; ++dx) {
        for (int dy = -5; dy <= 5; ++dy) {
            if (dx == 0 && dy == 0) continue;
            Position pos(getPosition().x + dx, getPosition().y + dy, getPosition().z);
            auto tile = g_game().map.getTile(pos);
            if (tile) {
                auto topCreature = tile->getTopCreature();
                if (topCreature) {
                    auto monster = topCreature->getMonster();
                    if (monster && !monster->isSummon() && monster->getID() != getID()) {
                        nearbyMonsters++;
                        if (nearbyMonsters > 2) break;
                    }
                }
            }
        }
        if (nearbyMonsters > 2) break;
    }
    if (nearbyMonsters > 2) return;

    std::shared_ptr<Creature> leader;
    if (isSummon()) leader = getMaster();
    else {
        leader = !m_attackedCreature.expired() ? m_attackedCreature.lock() : nullptr;
        if (!leader) leader = m_persistentTargetPlayer;
    }
    if (!leader || !leader->getPlayer()) return;

    {
        Position myPos = getPosition();
        auto myTile = g_game().map.getTile(myPos);
        if (myTile && myTile->getTopCreature() == getMonster()) {
            g_globalMonsterMap().addTile(myPos, true, false);
        }
    }

    const auto& stairs = leader->getPlayer()->getStairTransitions();
    for (const auto& trans : stairs)
        g_globalMonsterMap().addStairTransition(trans.origin, trans.destination);

    size_t added = 0;
    if (!mcrTryScanArea(getPosition(), 25, 2, 2, 500, stairs, &added)) {
        m_proactiveFailCount++;
        return;
    }
    if (added == 0) {
        m_proactiveFailCount++;
        return;
    }

    int bestCost = std::numeric_limits<int>::max();
    Position bestStairOrigin, bestStairDest;
    bool bestIsActive = false;
    const int MAX_STAIR_DIST = 12;

    auto allTransitions = g_globalMonsterMap().getAllTransitions();
    for (const auto& [origin, dest] : allTransitions) {
        if (origin.z != getPosition().z) continue;
        if (dest.z != leader->getPosition().z) continue;
        if (dest.z == origin.z) continue;

        int distToStair = std::abs(getPosition().x - origin.x) + std::abs(getPosition().y - origin.y);
        if (distToStair > MAX_STAIR_DIST) continue;

        auto path = g_globalMonsterMap().findPath(getPosition(), origin);
        if (path.empty()) continue;

        int distToStairPath = static_cast<int>(path.size());
        int distDestToPlayer = std::abs(dest.x - leader->getPosition().x)
                             + std::abs(dest.y - leader->getPosition().y);
        int cost = distToStairPath + distDestToPlayer;
        if (cost < bestCost) {
            bestCost = cost;
            bestStairOrigin = origin;
            bestStairDest = dest;
            auto tile = g_game().map.getTile(origin);
            bestIsActive = tile && tile->hasFlag(TILESTATE_FLOORCHANGE) && tile->hasFlag(TILESTATE_BLOCKPATH);
        }
    }

    if (bestCost < std::numeric_limits<int>::max()) {
        m_stairOrigin = bestStairOrigin;
        m_stairDestination = bestStairDest;
        m_stairIsActive = bestIsActive;
        m_pursuingStairs = true;
        m_stairStuckCount = 0;
        m_stairTotalCycles = 0;
        m_stairPathfindFailCount = 0;
        m_forcedMoveFailCount = 0;
        m_proactiveFailCount = 0;
        m_savedFollowId = leader->getID();
        setFollowCreature(nullptr);
        g_logger().info("[MCR-COGNI] {} perseguição proactiva (grafo): escada em {} (custo={})",
            getName(), bestStairOrigin.toString(), bestCost);
        walkToWaypoint(m_stairOrigin);
    } else {
        m_proactiveFailCount++;
    }
}

void Monster::invalidateTileBlocked(const Position& pos) {
    auto tile = g_game().map.getTile(pos);
    if (!tile) return;
    if (tile->getTopCreature()) return;

    bool blocked = tile->hasFlag(TILESTATE_BLOCKPATH) || tile->hasFlag(TILESTATE_BLOCKSOLID);
    if (!blocked) return;

    // Tiles sólidos (paredes, rochas, estalagmites) → bloqueio permanente
    if (tile->hasFlag(TILESTATE_BLOCKSOLID)) {
        g_globalMonsterMap().addTile(pos, false, false);
        g_logger().info("[MCR-COGNI] {} tile {} marcado como permanentemente bloqueado.", getName(), pos.toString());
        // Força scan local para atualizar o grafo na vizinhança
        g_globalMonsterMap().scanPlayerTrail(pos, 3);
        // Limpa a rota global actual, forçando recálculo no próximo ciclo
        clearWaypoints();
        return;
    }

    // Tiles não sólidos mas bloqueados → obstáculo temporário (agora 30s em vez de 15s)
    g_globalMonsterMap().addTemporaryObstacle(pos, 30000);
    g_logger().info("[MCR-COGNI] {} tile {} marcado como obstáculo temporário (30s).", getName(), pos.toString());
    // Mini‑scan e limpeza de rota também para estes casos
    g_globalMonsterMap().scanPlayerTrail(pos, 3);
    clearWaypoints();
}

void Monster::forceInvalidateTileInGraph(const Position& pos) {
    g_globalMonsterMap().markTilePermanentlyBlocked(pos);
    g_logger().info("[MCR-RETURN] {} tile {} marcado como bloqueado no grafo (forçado).",
        getName(), pos.toString());
}



Position Monster::findFreeTileNear(const Position& center, int maxRadius) const {
    for (int r = 1; r <= maxRadius; ++r) {
        for (int dx = -r; dx <= r; ++dx) {
            for (int dy = -r; dy <= r; ++dy) {
                // Apenas o anel exterior
                if (std::abs(dx) != r && std::abs(dy) != r) continue;
                Position check(center.x + dx, center.y + dy, center.z);
                auto tile = g_game().map.getTile(check);
                if (!tile) continue;
                if (tile->hasFlag(TILESTATE_BLOCKPATH) || tile->hasFlag(TILESTATE_BLOCKSOLID)) continue;
                // Nunca escolher tile com jogador
                auto topCreature = tile->getTopCreature();
                if (topCreature && topCreature->getPlayer()) continue;
                if (!topCreature) return check;
            }
        }
    }
    return Position(); // (0,0,0) indica que não encontrou
}

void Monster::mcrSafeTeleport(const Position& target) {
    Position safePos = findFreeTileNear(target, 4);
    if (safePos.x != 0 || safePos.y != 0) {
        g_game().internalTeleport(static_self_cast<Monster>(), safePos);
        g_game().addMagicEffect(safePos, CONST_ME_TELEPORT);
        return;
    }
    // Fallback: se o centro estiver livre, usa-o
    auto centerTile = g_game().map.getTile(target);
    if (centerTile && !centerTile->hasFlag(TILESTATE_BLOCKPATH) && !centerTile->getTopCreature()) {
        g_game().internalTeleport(static_self_cast<Monster>(), target);
    }
}

void Monster::tryAlternativeRouteToLeader() {
    if (m_followingWaypoints || m_pursuingStairs || m_returningToSpawn || m_returningHome) return;

    auto target = getAttackedCreature();
    if (!target) target = getFollowCreature();
    if (!target || !target->getPlayer()) {
        g_logger().info("[MCR-ALTROUTE] {} sem alvo válido, abortando.", getName());
        return;
    }

    Position myPos = getPosition();

    {
        auto myTile = g_game().map.getTile(myPos);
        if (myTile && myTile->getTopCreature() == getMonster()) {
            g_globalMonsterMap().addTile(myPos, true, false);
        }
    }

    Position targetPos = target->getPosition();

    if (myPos.z != targetPos.z) {
        g_logger().info("[MCR-ALTROUTE] {} alvo noutro piso, rota alternativa não se aplica.", getName());
        return;
    }

    FindPathParams fpp;
    getPathSearchParams(getMonster(), fpp);
    std::vector<Direction> dummy;
    if (getPathTo(targetPos, dummy, fpp)) {
        g_logger().info("[MCR-ALTROUTE] {} alvo já acessível via A*.", getName());
        return;
    }

    uint64_t now = getCurrentTimeMs();
    if (now - m_lastGlobalScanAttempt < 1000) return;
    m_lastGlobalScanAttempt = now;

    if (!g_globalMonsterMap().isWalkable(myPos)) {
        size_t dummyAdded;
        mcrTryScanArea(myPos, 20, 1, 1, 500,
            target->getPlayer()->getStairTransitions(), &dummyAdded);
        g_logger().info("[MCR-ALTROUTE] {} scan rápido executado ({} tiles adicionados).", getName(), dummyAdded);
    }

    auto fullPath = g_globalMonsterMap().findPath(myPos, targetPos);
    if (!fullPath.empty()) {
        clearWaypoints();
        m_waypoints = fullPath;
        m_waypointIndex = 0;
        m_followingWaypoints = true;
        m_lastGlobalPathStart = getCurrentTimeMs();
        m_savedFollowId = target->getID();
        setFollowCreature(nullptr);
        m_leaderDistanceStuckCycles = 0;
        m_lastDistToLeader = target ? (std::abs(getPosition().x - target->getPosition().x) + std::abs(getPosition().y - target->getPosition().y)) : 0;
        g_logger().info("[MCR-ALTROUTE] {} rota alternativa encontrada: {} passos", getName(), fullPath.size());
        return;
    }

    auto nearestPath = g_globalMonsterMap().findNearestApproachTo(myPos, targetPos);
    if (!nearestPath.empty()) {
        clearWaypoints();
        m_waypoints = nearestPath;
        m_waypointIndex = 0;
        m_followingWaypoints = true;
        m_lastGlobalPathStart = getCurrentTimeMs();
        m_savedFollowId = target->getID();
        setFollowCreature(nullptr);
        m_leaderDistanceStuckCycles = 0;
        m_lastDistToLeader = target ? (std::abs(getPosition().x - target->getPosition().x) + std::abs(getPosition().y - target->getPosition().y)) : 0;
        g_logger().info("[MCR-ALTROUTE] {} aproximação máxima: {} passos", getName(), nearestPath.size());
        return;
    }

    g_logger().info("[MCR-ALTROUTE] {} nenhuma rota alternativa encontrada.", getName());
}

void Monster::tryExploreArea() {
    uint64_t now = getCurrentTimeMs();
    uint64_t throttle = (g_globalMonsterMap().getTiles().size() < 1000) ? 10000 : 30000;
    if (now - m_lastExplorationScan < throttle) return;
    m_lastExplorationScan = now;

    Position myPos = getPosition();

    // Verifica cobertura: se mais de 40% dos tiles no raio 20 já estão mapeados, pula
    int coveredTiles = 0;
    int totalChecked = 0;
    for (int dx = -20; dx <= 20; ++dx) {
        for (int dy = -20; dy <= 20; ++dy) {
            if (dx == 0 && dy == 0) continue;
            totalChecked++;
            Position check(myPos.x + dx, myPos.y + dy, myPos.z);
            if (g_globalMonsterMap().isWalkable(check)) coveredTiles++;
        }
    }
    // 40% de cobertura (era 60%)
    if (totalChecked > 0 && coveredTiles > totalChecked * 0.4) {
        return;
    }

    size_t added = g_globalMonsterMap().scanArea(myPos, 40, 3, 3, 3000, {}, true);
    g_logger().info("[MCR-EXPLORE] {} scan exploratório: {} tiles adicionados (total: {})",
        getName(), added, g_globalMonsterMap().getTiles().size());
}

void Monster::tryFlankingRoute() {
    if (m_followingWaypoints) return;

    std::shared_ptr<Creature> leader;
    if (isSummon()) leader = getMaster();
    else {
        leader = !m_attackedCreature.expired() ? m_attackedCreature.lock() : nullptr;
        if (!leader) leader = m_persistentTargetPlayer;
    }
    if (!leader || !leader->getPlayer()) {
        g_logger().info("[MCR-FLANK] {} sem líder, abortando cercamento.", getName());
        return;
    }
    if (leader->getPosition().z != getPosition().z && !m_pursuingStairs) {
        g_logger().info("[MCR-FLANK] {} líder noutro piso e não está a perseguir escada, abortando.", getName());
        return;
    }

    Position leaderPos = leader->getPosition();
    if (!g_globalMonsterMap().isWalkable(leaderPos)) {
        g_globalMonsterMap().addTile(leaderPos, true, false);
    }

    FindPathParams fpp;
    getPathSearchParams(getMonster(), fpp);
    fpp.clearSight = false;
    fpp.fullPathSearch = true;
    fpp.maxSearchDist = 120;
    std::vector<Direction> dummy;
    if (getPathTo(leader->getPosition(), dummy, fpp)) {
        g_logger().info("[MCR-FLANK] {} líder já acessível via A*, cercamento desnecessário.", getName());
        return;
    }

    if (m_pursuingStairs && m_stairTotalCycles < 3) {
        g_logger().info("[MCR-FLANK] {} perseguição de escada recente, aguardando antes de cercar.", getName());
        return;
    }

    uint64_t now = getCurrentTimeMs();
    const uint64_t flankThrottle = canSee(leaderPos) ? 600 : 1000;
    if (now - m_lastFlankingAttempt < flankThrottle) return;
    m_lastFlankingAttempt = now;

    size_t addedLeader = g_globalMonsterMap().scanPlayerTrail(leaderPos, 10);
    size_t addedSelf = g_globalMonsterMap().scanPlayerTrail(getPosition(), 10);
    if (addedLeader > 0 || addedSelf > 0) {
        g_logger().info("[MCR-FLANK] {} scans: líder={} tiles, self={} tiles.", getName(), addedLeader, addedSelf);
    }

    auto fullPath = g_globalMonsterMap().findPath(getPosition(), leaderPos);
    bool isApproach = false;
    if (fullPath.empty()) {
        fullPath = g_globalMonsterMap().findNearestApproachTo(getPosition(), leaderPos);
        isApproach = true;
    }

    if (!fullPath.empty()) {
        if (isApproach) {
            Position lastPos = fullPath.back();
            int currentDist = std::abs(getPosition().x - leaderPos.x) + std::abs(getPosition().y - leaderPos.y);
            int newDist = std::abs(lastPos.x - leaderPos.x) + std::abs(lastPos.y - leaderPos.y);
            if (newDist >= currentDist) {
                g_logger().info("[MCR-FLANK] {} aproximação não reduz distância ({} -> {}), ignorando.", getName(), currentDist, newDist);
                return;
            }
            g_logger().info("[MCR-FLANK] {} vai cercar usando rota de aproximação ({} passos, distância reduzida de {} para {}).",
                getName(), fullPath.size(), currentDist, newDist);
        }

        if (fullPath.size() >= 1) {
            auto firstTile = g_game().map.getTile(fullPath[0]);
            if (firstTile && firstTile->getTopCreature() && firstTile->getTopCreature() != getMonster()) {
                g_globalMonsterMap().addTemporaryObstacle(fullPath[0], 2000);
                g_logger().info("[MCR-FLANK] {} primeiro tile {} ocupado, tentando avançar para o próximo passo.", getName(), fullPath[0].toString());
                if (fullPath.size() > 1) {
                    fullPath.erase(fullPath.begin());
                } else {
                    return;
                }
            }
        }

        clearWaypoints();
        m_waypoints = fullPath;
        m_waypointIndex = 0;
        m_followingWaypoints = true;
        m_lastGlobalPathStart = getCurrentTimeMs();
        // Inicialização do novo timeout
        m_leaderDistanceStuckCycles = 0;
        m_lastDistToLeader = (leader && !leader->isRemoved()) ? (std::abs(getPosition().x - leader->getPosition().x) + std::abs(getPosition().y - leader->getPosition().y)) : 0;

        if (m_pursuingStairs) {
            m_recentlyFailedStairs[m_stairOrigin] = getCurrentTimeMs() + FAILED_STAIR_COOLDOWN;
            m_savedFollowId = 0;
            clearStairPursuit();
        }

        setFollowCreature(nullptr);
        m_savedFollowId = leader->getID();

        g_logger().info("[MCR-FLANK] {} vai cercar o líder usando rota multi‑piso ({} passos)", getName(), fullPath.size());

        m_flankingFailCount = 0;
        m_lastFlankingAttempt = now;
        return;
    }

    g_logger().info("[MCR-FLANK] {} cercamento falhou (falha acumulada {}/12).", getName(), m_flankingFailCount + 1);
}

void Monster::tryReturnToSpawn() {
    if (!m_hasSpawnPosition) return;

    // Reseta contadores antes de iniciar o retorno
    m_flankingFailCount = 0;
    m_idleFailCount = 0;

    m_homePosition = m_spawnPosition;
    m_returningHome = true;
    g_logger().info("[MCR-RETURN] {} a regressar ao spawn.", getName());
}

void Monster::tryIdleWander() {
    if (isSummon()) return;

    uint64_t now = getCurrentTimeMs();
    if (now - m_lastIdleWanderTime < 3000) return;
    m_lastIdleWanderTime = now;

    if (isWalkingToPosition()) return;

    Position myPos = getPosition();

    // Lista de direções (8)
    static const int dx[] = {-1, 0, 1, 0, -1, 1, 1, -1};
    static const int dy[] = {0, -1, 0, 1, -1, 1, -1, 1};

    std::vector<Direction> directions;
    for (int i = 0; i < 8; ++i) {
        Position cand(myPos.x + dx[i], myPos.y + dy[i], myPos.z);
        auto tile = g_game().map.getTile(cand);
        if (!tile) continue;
        if (tile->hasFlag(TILESTATE_BLOCKPATH) || tile->hasFlag(TILESTATE_BLOCKSOLID)) continue;
        if (tile->getTopCreature()) continue;  // evita tiles ocupados
        directions.push_back(static_cast<Direction>(i));
    }

    if (directions.empty()) return;

    // Escolhe uma direção aleatória
    int rnd = uniform_random(0, static_cast<int>(directions.size()) - 1);
    Direction dir = directions[rnd];

    // Movimento simples (um tile na direção escolhida)
    g_game().internalMoveCreature(static_self_cast<Monster>(), dir, 0);
    g_logger().info("[MCR-IDLE] {} a deambular na direção {}.", getName(), static_cast<int>(dir));
}

std::vector<Position> Monster::getGlobalDestinations(const Position& pos) {
    return g_globalMonsterMap().getDestinations(pos);
}

void Monster::trySmartFlanking() {
    if (m_followingWaypoints) return;
    if (m_returningToSpawn || m_returningHome) return;
    if (!m_pursuingStairs) return; // só faz sentido quando já está perseguindo

    uint64_t now = getCurrentTimeMs();
    if (now - m_lastSmartFlankingAttempt < 10000) return;
    m_lastSmartFlankingAttempt = now;

    std::shared_ptr<Creature> leader;
    if (isSummon()) leader = getMaster();
    else {
        leader = !m_attackedCreature.expired() ? m_attackedCreature.lock() : nullptr;
        if (!leader) leader = m_persistentTargetPlayer;
    }
    if (!leader || !leader->getPlayer()) return;

    Position myPos = getPosition();
    Position leaderPos = leader->getPosition();

    // Se o líder está no mesmo piso e o A* encontra um caminho curto, não vale a pena cercar
    if (myPos.z == leaderPos.z) {
        FindPathParams fpp;
        getPathSearchParams(getMonster(), fpp);
        std::vector<Direction> dummy;
        if (getPathTo(leaderPos, dummy, fpp)) {
            int dist = std::abs(myPos.x - leaderPos.x) + std::abs(myPos.y - leaderPos.y);
            if (dist <= 15) return; // já está perto, não precisa de cercamento
        }
    }

    // Obtém todas as transições conhecidas no piso atual
    auto allTrans = g_globalMonsterMap().getAllTransitions();
    if (allTrans.empty()) return;

    // Procura a melhor escada (origem no piso atual) que leve a uma rota completa até o líder
    int bestCost = std::numeric_limits<int>::max();
    Position bestOrigin, bestDest;
    bool bestIsActive = false;

    for (const auto& [origin, dest] : allTrans) {
        if (origin.z != myPos.z) continue;
        // A escada deve levar para um piso diferente (para ser um cercamento)
        if (dest.z == origin.z) continue;
        // Verifica se o destino da escada está mapeado e é caminhável
        if (!g_globalMonsterMap().isWalkable(dest)) continue;

        // Calcula o custo: distância até a escada + distância estimada do destino ao líder
        int distToStair = std::abs(myPos.x - origin.x) + std::abs(myPos.y - origin.y);
        int distDestToLeader = std::abs(dest.x - leaderPos.x) + std::abs(dest.y - leaderPos.y);
        int cost = distToStair + distDestToLeader;
        if (cost < bestCost) {
            bestCost = cost;
            bestOrigin = origin;
            bestDest = dest;
            auto tile = g_game().map.getTile(origin);
            bestIsActive = tile && tile->hasFlag(TILESTATE_FLOORCHANGE) && tile->hasFlag(TILESTATE_BLOCKPATH);
        }
    }

    if (bestCost >= std::numeric_limits<int>::max()) return;

    // Tenta uma rota completa via grafo
    auto fullPath = g_globalMonsterMap().findPath(myPos, bestOrigin);
    if (fullPath.empty()) return;

    // Custo total: passos até a escada + 1 (uso da escada) + passos do destino ao líder
    int totalCost = static_cast<int>(fullPath.size()) + 1 + bestCost; // bestCost já inclui distância ao líder

    // Só substitui a perseguição atual se a nova rota for significativamente melhor
    int currentPlanDist = std::abs(myPos.x - m_stairOrigin.x) + std::abs(myPos.y - m_stairOrigin.y);
    if (totalCost >= currentPlanDist * 1.2) return; // não é muito melhor

    g_logger().info("[MCR-STAIR] {} cercamento inteligente: usando escada em {} -> {} (custo {} vs atual {})",
        getName(), bestOrigin.toString(), bestDest.toString(), totalCost, currentPlanDist);

    // Inicia a perseguição pela nova escada
    clearStairPursuit();
    m_pursuingStairs = true;
    m_stairOrigin = bestOrigin;
    m_stairDestination = bestDest;
    m_stairIsActive = bestIsActive;
    m_stairStuckCount = 0;
    m_stairTotalCycles = 0;
    m_stairPathfindFailCount = 0;
    m_forcedMoveFailCount = 0;
    m_pursuitStartTime = now;
    m_stairAttemptStartTime = now;
    m_minDistToStair = std::numeric_limits<int>::max();
    m_lastDistImprovementTime = now;
    m_homePosition = myPos;
    m_pursuitDeadline = computePursuitDeadline();
    m_sightLostTicks = 0;
    m_savedFollowId = leader->getID();
    setFollowCreature(nullptr);
    clearWaypoints();
    walkToWaypoint(m_stairOrigin);
}

void Monster::mcrEnsureMyTileWalkable() {
    Position myPos = getPosition();
    g_globalMonsterMap().addTile(myPos, true, false);
}


void Monster::clearWaypoints() {
    if (!m_waypoints.empty() || m_followingWaypoints) {
        g_logger().info("[MCR-WALK] {} clearWaypoints: removendo {} waypoints.", getName(), m_waypoints.size());
    }
    m_waypoints.clear();
    m_waypointIndex = 0;
    m_followingWaypoints = false;
    m_leaderDistanceStuckCycles = 0;
    m_lastDistToLeader = 0;
}

void Monster::clearStairPursuit() {
    if (m_clearingStairs) return;
    m_clearingStairs = true;
    m_lastProactiveCheck = 0;
    // m_pursuitDeadline = 0;  ← REMOVIDO DEFINITIVAMENTE

    g_logger().info("[MCR-STAIR] {} clearStairPursuit: limpando estado de perseguição.", getName());

    m_pursuingStairs = false;
    m_followingSurfaceWaypoint = false;
    m_stairQueue.clear();
    m_waypoints.clear();
    m_waypointIndex = 0;
    m_followingWaypoints = false;

    clearWaypoints();
    resetEngagement();

    if (m_savedFollowId != 0) {
        auto saved = g_game().getCreatureByID(m_savedFollowId);
        if (saved) {
            g_logger().info("[MCR-STAIR] {} restaurando follow para criatura ID {}.", getName(), m_savedFollowId);
            setFollowCreature(saved);
        } else {
            g_logger().info("[MCR-STAIR] {} criatura original (ID={}) já não existe.", getName(), m_savedFollowId);
        }
        m_savedFollowId = 0;
    }

    if (isSummon() && getMaster() && !getFollowCreature()) {
        g_logger().info("[MCR-STAIR] {} a restaurar follow para mestre (fallback).", getName());
        setFollowCreature(getMaster());
    }

    if (!isSummon() && !getFollowCreature() && !m_attackedCreature.expired()) {
        auto target = m_attackedCreature.lock();
        g_logger().info("[MCR-STAIR] {} restaurando follow para alvo de ataque {}.", getName(), target->getName());
        setFollowCreature(target);
    }

    m_clearingStairs = false;
}

bool Monster::canStairBeUsed(const Position& origin, int deltaZ) const {
    auto tile = g_game().map.getTile(origin);
    if (!tile || !tile->hasFlag(TILESTATE_FLOORCHANGE)) {
        return false;
    }

    // 1. Destino explícito (teleportes, etc.) – válido se a diferença de Z corresponder
    Position dest = tile->getDestination();
    if (dest.x != 0 || dest.y != 0) {
        return (dest.z - origin.z == deltaZ);
    }

    // 2. Sem destino explícito – valida pelas sub‑flags de direção
    bool goesDown = tile->hasFlag(TILESTATE_FLOORCHANGE_DOWN);
    bool goesUp   = tile->hasFlag(TILESTATE_FLOORCHANGE_NORTH) ||
                    tile->hasFlag(TILESTATE_FLOORCHANGE_SOUTH) ||
                    tile->hasFlag(TILESTATE_FLOORCHANGE_EAST)  ||
                    tile->hasFlag(TILESTATE_FLOORCHANGE_WEST)  ||
                    tile->hasFlag(TILESTATE_FLOORCHANGE_SOUTH_ALT) ||
                    tile->hasFlag(TILESTATE_FLOORCHANGE_EAST_ALT);

    // 2a. Se não há flags de direção, assume‑se bidirecional (ex.: escadas de pedra comuns)
    if (!goesDown && !goesUp) {
        return true;
    }

    // 2b. Valida conforme a direção pretendida
    if (deltaZ < 0 && goesDown) return true;
    if (deltaZ > 0 && goesUp)   return true;

    return false;
}

Position Monster::findStairNearReal(const Position& leaderPos, int radius) {
    Position myPos = getPosition();
    int targetDeltaZ = leaderPos.z - myPos.z;
    int bestCost = std::numeric_limits<int>::max();
    Position bestOrigin;

    for (int dx = -radius; dx <= radius; ++dx) {
        for (int dy = -radius; dy <= radius; ++dy) {
            Position check(myPos.x + dx, myPos.y + dy, myPos.z);
            if (check == myPos) continue;

            auto tile = g_game().map.getTile(check);
            if (!tile || !tile->hasFlag(TILESTATE_FLOORCHANGE)) continue;

            int deltaZ = 0;
            if (tile->hasFlag(TILESTATE_FLOORCHANGE_DOWN)) {
                deltaZ = -1;
            } else if (tile->hasFlag(TILESTATE_FLOORCHANGE_NORTH) || tile->hasFlag(TILESTATE_FLOORCHANGE_SOUTH) ||
                       tile->hasFlag(TILESTATE_FLOORCHANGE_EAST)  || tile->hasFlag(TILESTATE_FLOORCHANGE_WEST)  ||
                       tile->hasFlag(TILESTATE_FLOORCHANGE_SOUTH_ALT) || tile->hasFlag(TILESTATE_FLOORCHANGE_EAST_ALT)) {
                deltaZ = 1;
            } else {
                if (targetDeltaZ > 0) deltaZ = 1;
                else if (targetDeltaZ < 0) deltaZ = -1;
                else continue;
            }

            if (!canStairBeUsed(check, deltaZ)) continue;

            Position dest = check;
            dest.z += deltaZ;
            int newDiff = std::abs(leaderPos.z - dest.z);
            int currentDiff = std::abs(leaderPos.z - myPos.z);
            if (newDiff >= currentDiff) continue;

            int distToStair = std::abs(myPos.x - check.x) + std::abs(myPos.y - check.y);
            int distDestToPlayer = std::abs(dest.x - leaderPos.x) + std::abs(dest.y - leaderPos.y);
            int cost = distToStair + distDestToPlayer + (newDiff * 10);

            if (cost < bestCost) {
                bestCost = cost;
                bestOrigin = check;
            }
        }
    }
    return bestOrigin; // (0,0,0) se não encontrou
}