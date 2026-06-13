/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "lua/creature/creatureevent.hpp"

#include "creatures/players/player.hpp"
#include "items/item.hpp"
#include "lua/scripts/scripts.hpp"
#include "lib/di/container.hpp"

void CreatureEvents::clear() {
	for (const auto &[name, event] : creatureEvents) {
		event->clearEvent();
	}
}

bool CreatureEvents::registerLuaEvent(const std::shared_ptr<CreatureEvent> &creatureEvent) {
	if (creatureEvent->getEventType() == CREATURE_EVENT_NONE) {
		g_logger().error(
			"[{}] - Trying to register event without type for script: {}",
			__FUNCTION__,
			creatureEvent->getScriptInterface()->getLoadingScriptName()
		);
		return false;
	}

	const auto &oldEvent = getEventByName(creatureEvent->getName(), false);
	if (oldEvent) {
		// if there was an event with the same that is not loaded
		//(happens when realoading), it is reused
		if (!oldEvent->isLoaded() && oldEvent->getEventType() == creatureEvent->getEventType()) {
			oldEvent->copyEvent(creatureEvent);
		}

		return false;
	} else {
		// if not, register it normally
		creatureEvents.emplace(creatureEvent->getName(), creatureEvent);
		return true;
	}
}

std::shared_ptr<CreatureEvent> CreatureEvents::getEventByName(const std::string &name, bool forceLoaded /*= true*/) {
	const auto it = creatureEvents.find(name);
	if (it != creatureEvents.end()) {
		if (!forceLoaded || it->second->isLoaded()) {
			return it->second;
		}
	}
	return nullptr;
}

CreatureEvents &CreatureEvents::getInstance() {
	return inject<CreatureEvents>();
}

bool CreatureEvents::playerLogin(const std::shared_ptr<Player> &player) const {
	// fire global event if is registered
	for (const auto &it : creatureEvents) {
		if (it.second->getEventType() == CREATURE_EVENT_LOGIN) {
			if (!it.second->executeOnLogin(player)) {
				return false;
			}
		}
	}
	return true;
}

bool CreatureEvents::playerLogout(const std::shared_ptr<Player> &player) const {
	// fire global event if is registered
	for (const auto &it : creatureEvents) {
		if (it.second->getEventType() == CREATURE_EVENT_LOGOUT) {
			if (!it.second->executeOnLogout(player)) {
				return false;
			}
		}
	}
	return true;
}

bool CreatureEvents::playerAdvance(
	const std::shared_ptr<Player> &player,
	skills_t skill,
	uint32_t oldLevel,
	uint32_t newLevel
) const {
	for ([[maybe_unused]] const auto &[eventName, eventPtr] : creatureEvents) {
		if (eventPtr->getEventType() == CREATURE_EVENT_ADVANCE) {
			if (!eventPtr->executeAdvance(player, skill, oldLevel, newLevel)) {
				return false;
			}
		}
	}
	return true;
}

/*
 =======================
 CreatureEvent interface
 =======================
*/

CreatureEvent::CreatureEvent() = default;

LuaScriptInterface* CreatureEvent::getScriptInterface() const {
	return &g_scripts().getScriptInterface();
}

bool CreatureEvent::loadScriptId() {
	LuaScriptInterface &luaInterface = g_scripts().getScriptInterface();
	m_scriptId = luaInterface.getEvent();
	if (m_scriptId == -1) {
		g_logger().error("[MoveEvent::loadScriptId] Failed to load event. Script name: '{}', Module: '{}'", luaInterface.getLoadingScriptName(), luaInterface.getInterfaceName());
		return false;
	}

	return true;
}

int32_t CreatureEvent::getScriptId() const {
	return m_scriptId;
}

void CreatureEvent::setScriptId(int32_t newScriptId) {
	m_scriptId = newScriptId;
}

bool CreatureEvent::isLoadedScriptId() const {
	return m_scriptId != 0;
}

void CreatureEvents::removeInvalidEvents() {
	std::erase_if(creatureEvents, [](const auto &pair) {
		return pair.second->getScriptId() == 0;
	});
}

std::string CreatureEvent::getScriptTypeName() const {
	// Depending on the type script event name is different
	switch (type) {
		case CREATURE_EVENT_LOGIN:
			return "onLogin";

		case CREATURE_EVENT_LOGOUT:
			return "onLogout";

		case CREATURE_EVENT_THINK:
			return "onThink";

		case CREATURE_EVENT_PREPAREDEATH:
			return "onPrepareDeath";

		case CREATURE_EVENT_DEATH:
			return "onDeath";

		case CREATURE_EVENT_KILL:
			return "onKill";

		case CREATURE_EVENT_ADVANCE:
			return "onAdvance";

		case CREATURE_EVENT_MODALWINDOW:
			return "onModalWindow";

		case CREATURE_EVENT_TEXTEDIT:
			return "onTextEdit";

		case CREATURE_EVENT_HEALTHCHANGE:
			return "onHealthChange";

		case CREATURE_EVENT_MANACHANGE:
			return "onManaChange";

		case CREATURE_EVENT_EXTENDED_OPCODE:
			return "onExtendedOpcode";

		// NOVOS:
        case CREATURE_EVENT_SPELL:
            return "onSpellCast";
        case CREATURE_EVENT_ITEM_USE:
            return "onUseItem";
		case CREATURE_EVENT_DEALT_DAMAGE:
   			return "onDealtDamage";
		case CREATURE_EVENT_FIGHT_MODE_CHANGE:
    		return "onFightModeChange";
		case CREATURE_EVENT_DOMINIO_ACTION:
			return "onDominioAction";	

		case CREATURE_EVENT_NONE:
		default:
			return {};
	}
}

void CreatureEvent::executeOnDominioAction(const std::shared_ptr<Player>& player, uint16_t dominioId) const {
    if (!loaded) {
        return;
    }
    LuaScriptInterface* scriptInterface = getScriptInterface();
    if (!scriptInterface) {
        return;
    }
    lua_State* L = scriptInterface->getLuaState();
    if (!L) {
        return;
    }
    if (!scriptInterface->pushFunction(m_scriptId)) {
        return;
    }
    LuaScriptInterface::pushUserdata<Player>(L, player);
    LuaScriptInterface::setMetatable(L, -1, "Player");
    lua_pushinteger(L, dominioId);
    scriptInterface->callFunction(2);
}

void CreatureEvents::playerDominioAction(const std::shared_ptr<Player>& player, uint16_t dominioId) const {
    for (const auto& [name, event] : creatureEvents) {
        if (event->getEventType() == CREATURE_EVENT_DOMINIO_ACTION) {
            event->executeOnDominioAction(player, dominioId);
        }
    }
}

void CreatureEvent::copyEvent(const std::shared_ptr<CreatureEvent> &creatureEvent) {
	setScriptId(creatureEvent->getScriptId());
	loaded = creatureEvent->loaded;
}

void CreatureEvent::clearEvent() {
	setScriptId(0);
	loaded = false;
}

void CreatureEvent::executeOnFightModeChange(const std::shared_ptr<Player>& player, FightMode_t oldMode, FightMode_t newMode) const {
    if (!LuaScriptInterface::reserveScriptEnv()) {
        g_logger().error("[CreatureEvent::executeOnFightModeChange - Player {}] Call stack overflow.", player->getName());
        return;
    }
    ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
    env->setScriptId(getScriptId(), getScriptInterface());
    lua_State* L = getScriptInterface()->getLuaState();
    getScriptInterface()->pushFunction(getScriptId());

    LuaScriptInterface::pushUserdata(L, player);
    LuaScriptInterface::setMetatable(L, -1, "Player");
    lua_pushnumber(L, static_cast<lua_Number>(oldMode));
    lua_pushnumber(L, static_cast<lua_Number>(newMode));

    getScriptInterface()->callVoidFunction(3);
}

void CreatureEvent::executeOnSpell(const std::shared_ptr<Player>& player, const std::string& spellName) const {
    // onSpellCast(player, spellName)
    if (!LuaScriptInterface::reserveScriptEnv()) {
        g_logger().error("[CreatureEvent::executeOnSpell - Player {} spell {} event {}] "
                         "Call stack overflow. Too many lua script calls being nested.",
                         player->getName(), spellName, getName());
        return;
    }

    ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
    env->setScriptId(getScriptId(), getScriptInterface());

    lua_State* L = getScriptInterface()->getLuaState();
    getScriptInterface()->pushFunction(getScriptId());

    LuaScriptInterface::pushUserdata(L, player);
    LuaScriptInterface::setMetatable(L, -1, "Player");
    LuaScriptInterface::pushString(L, spellName);

    getScriptInterface()->callVoidFunction(2);
}

void CreatureEvent::executeOnItemUse(const std::shared_ptr<Player>& player, const std::shared_ptr<Item>& item) const {
    // onUseItem(player, item)
    if (!LuaScriptInterface::reserveScriptEnv()) {
        g_logger().error("[CreatureEvent::executeOnItemUse - Player {} item {} event {}] "
                         "Call stack overflow. Too many lua script calls being nested.",
                         player->getName(), item->getName(), getName());
        return;
    }

    ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
    env->setScriptId(getScriptId(), getScriptInterface());

    lua_State* L = getScriptInterface()->getLuaState();
    getScriptInterface()->pushFunction(getScriptId());

    LuaScriptInterface::pushUserdata(L, player);
    LuaScriptInterface::setMetatable(L, -1, "Player");
    LuaScriptInterface::pushThing(L, item);

    getScriptInterface()->callVoidFunction(2);
}

void CreatureEvents::playerSpell(const std::shared_ptr<Player>& player, const std::string& spellName) const {
    for (const auto& [name, event] : creatureEvents) {
        if (event->getEventType() == CREATURE_EVENT_SPELL) {
            event->executeOnSpell(player, spellName);
        }
    }
}

void CreatureEvents::playerItemUse(const std::shared_ptr<Player>& player, const std::shared_ptr<Item>& item) const {
    for (const auto& [name, event] : creatureEvents) {
        if (event->getEventType() == CREATURE_EVENT_ITEM_USE) {
            event->executeOnItemUse(player, item);
        }
    }
}

bool CreatureEvent::executeOnLogin(const std::shared_ptr<Player> &player) const {
	// onLogin(player)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeOnLogin - Player {} event {}]"
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 player->getName(), getName());
		return false;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();

	getScriptInterface()->pushFunction(getScriptId());
	LuaScriptInterface::pushUserdata(L, player);
	LuaScriptInterface::setMetatable(L, -1, "Player");
	return getScriptInterface()->callFunction(1);
}

bool CreatureEvent::executeOnLogout(const std::shared_ptr<Player> &player) const {
	// onLogout(player)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeOnLogout - Player {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 player->getName(), getName());
		return false;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();

	getScriptInterface()->pushFunction(getScriptId());
	LuaScriptInterface::pushUserdata(L, player);
	LuaScriptInterface::setMetatable(L, -1, "Player");
	return getScriptInterface()->callFunction(1);
}

bool CreatureEvent::executeOnThink(const std::shared_ptr<Creature> &creature, uint32_t interval) const {
	// onThink(creature, interval)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeOnThink - Creature {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 creature->getName(), getName());
		return false;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();

	getScriptInterface()->pushFunction(getScriptId());
	LuaScriptInterface::pushUserdata<Creature>(L, creature);
	LuaScriptInterface::setCreatureMetatable(L, -1, creature);
	lua_pushnumber(L, interval);

	return getScriptInterface()->callFunction(2);
}

bool CreatureEvent::executeOnPrepareDeath(const std::shared_ptr<Creature> &creature, const std::shared_ptr<Creature> &killer, int realDamage) const {
	// onPrepareDeath(creature, killer)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeOnPrepareDeath - Creature {} killer {}"
		                 " event {}] Call stack overflow. Too many lua script calls being nested.",
		                 creature->getName(), killer->getName(), getName());
		return false;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();

	getScriptInterface()->pushFunction(getScriptId());

	LuaScriptInterface::pushUserdata<Creature>(L, creature);
	LuaScriptInterface::setCreatureMetatable(L, -1, creature);

	if (killer) {
		LuaScriptInterface::pushUserdata<Creature>(L, killer);
		LuaScriptInterface::setCreatureMetatable(L, -1, killer);
	} else {
		lua_pushnil(L);
	}

	lua_pushnumber(L, realDamage);

	return getScriptInterface()->callFunction(3);
}

bool CreatureEvent::executeOnDeath(const std::shared_ptr<Creature> &creature, const std::shared_ptr<Item> &corpse, const std::shared_ptr<Creature> &killer, const std::shared_ptr<Creature> &mostDamageKiller, bool lastHitUnjustified, bool mostDamageUnjustified) const {
	// onDeath(creature, corpse, lasthitkiller, mostdamagekiller, lasthitunjustified, mostdamageunjustified)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeOnDeath - Creature {} killer {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 creature->getName(), killer->getName(), getName());
		return false;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();

	getScriptInterface()->pushFunction(getScriptId());
	LuaScriptInterface::pushUserdata<Creature>(L, creature);
	LuaScriptInterface::setCreatureMetatable(L, -1, creature);

	LuaScriptInterface::pushThing(L, corpse);

	if (killer) {
		LuaScriptInterface::pushUserdata<Creature>(L, killer);
		LuaScriptInterface::setCreatureMetatable(L, -1, killer);
	} else {
		lua_pushnil(L);
	}

	if (mostDamageKiller) {
		LuaScriptInterface::pushUserdata<Creature>(L, mostDamageKiller);
		LuaScriptInterface::setCreatureMetatable(L, -1, mostDamageKiller);
	} else {
		lua_pushnil(L);
	}

	LuaScriptInterface::pushBoolean(L, lastHitUnjustified);
	LuaScriptInterface::pushBoolean(L, mostDamageUnjustified);

	return getScriptInterface()->callFunction(6);
}

bool CreatureEvent::executeAdvance(const std::shared_ptr<Player> &player, skills_t skill, uint32_t oldLevel, uint32_t newLevel) const {
	// onAdvance(player, skill, oldLevel, newLevel)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeAdvance - Player {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 player->getName(), getName());
		return false;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();

	getScriptInterface()->pushFunction(getScriptId());
	LuaScriptInterface::pushUserdata(L, player);
	LuaScriptInterface::setMetatable(L, -1, "Player");
	lua_pushnumber(L, static_cast<uint32_t>(skill));
	lua_pushnumber(L, oldLevel);
	lua_pushnumber(L, newLevel);

	return getScriptInterface()->callFunction(4);
}

/**
 * @deprecated Prefer using registered onDeath events instead for better performance.
 */
void CreatureEvent::executeOnKill(const std::shared_ptr<Creature> &creature, const std::shared_ptr<Creature> &target, bool lastHit) const {
	// onKill(creature, target, lastHit)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeOnKill - Creature {} target {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 creature->getName(), target->getName(), getName());
		return;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();

	getScriptInterface()->pushFunction(getScriptId());
	LuaScriptInterface::pushUserdata<Creature>(L, creature);
	LuaScriptInterface::setCreatureMetatable(L, -1, creature);
	LuaScriptInterface::pushUserdata<Creature>(L, target);
	LuaScriptInterface::setCreatureMetatable(L, -1, target);
	LuaScriptInterface::pushBoolean(L, lastHit);
	getScriptInterface()->callVoidFunction(3);
}

void CreatureEvent::executeModalWindow(const std::shared_ptr<Player> &player, uint32_t modalWindowId, uint8_t buttonId, uint8_t choiceId) const {
	// onModalWindow(player, modalWindowId, buttonId, choiceId)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeModalWindow - "
		                 "Player {} modaw window id {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 player->getName(), modalWindowId, getName());
		return;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();
	getScriptInterface()->pushFunction(getScriptId());

	LuaScriptInterface::pushUserdata(L, player);
	LuaScriptInterface::setMetatable(L, -1, "Player");

	lua_pushnumber(L, modalWindowId);
	lua_pushnumber(L, buttonId);
	lua_pushnumber(L, choiceId);

	getScriptInterface()->callVoidFunction(4);
}

bool CreatureEvent::executeTextEdit(const std::shared_ptr<Player> &player, const std::shared_ptr<Item> &item, const std::string &text) const {
	// onTextEdit(player, item, text)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeTextEdit - Player {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 player->getName(), getName());
		return false;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();
	getScriptInterface()->pushFunction(getScriptId());

	LuaScriptInterface::pushUserdata(L, player);
	LuaScriptInterface::setMetatable(L, -1, "Player");

	LuaScriptInterface::pushThing(L, item);
	LuaScriptInterface::pushString(L, text);

	return getScriptInterface()->callFunction(3);
}

void CreatureEvent::executeHealthChange(const std::shared_ptr<Creature> &creature, const std::shared_ptr<Creature> &attacker, CombatDamage &damage) const {
	// onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeHealthChange - "
		                 "Creature {} attacker {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 creature->getName(), attacker->getName(), getName());
		return;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();
	getScriptInterface()->pushFunction(getScriptId());

	LuaScriptInterface::pushUserdata(L, creature);
	LuaScriptInterface::setCreatureMetatable(L, -1, creature);
	if (attacker) {
		LuaScriptInterface::pushUserdata(L, attacker);
		LuaScriptInterface::setCreatureMetatable(L, -1, attacker);
	} else {
		lua_pushnil(L);
	}

	LuaScriptInterface::pushCombatDamage(L, damage);

	if (LuaScriptInterface::protectedCall(L, 7, 4) != 0) {
		LuaScriptInterface::reportError(nullptr, LuaScriptInterface::popString(L));
	} else {
		damage.primary.value = std::abs(LuaScriptInterface::getNumber<int32_t>(L, -4));
		damage.primary.type = LuaScriptInterface::getNumber<CombatType_t>(L, -3);
		damage.secondary.value = std::abs(LuaScriptInterface::getNumber<int32_t>(L, -2));
		damage.secondary.type = LuaScriptInterface::getNumber<CombatType_t>(L, -1);

		lua_pop(L, 4);
		if (damage.primary.type != COMBAT_HEALING) {
			damage.primary.value = -damage.primary.value;
			damage.secondary.value = -damage.secondary.value;
		}
	}

	LuaScriptInterface::resetScriptEnv();
}

void CreatureEvent::executeManaChange(const std::shared_ptr<Creature> &creature, const std::shared_ptr<Creature> &attacker, CombatDamage &damage) const {
	// onManaChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeManaChange - "
		                 "Creature {} attacker {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 creature->getName(), attacker->getName(), getName());
		return;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();
	getScriptInterface()->pushFunction(getScriptId());

	LuaScriptInterface::pushUserdata(L, creature);
	LuaScriptInterface::setCreatureMetatable(L, -1, creature);
	if (attacker) {
		LuaScriptInterface::pushUserdata(L, attacker);
		LuaScriptInterface::setCreatureMetatable(L, -1, attacker);
	} else {
		lua_pushnil(L);
	}

	LuaScriptInterface::pushCombatDamage(L, damage);

	if (LuaScriptInterface::protectedCall(L, 7, 4) != 0) {
		LuaScriptInterface::reportError(nullptr, LuaScriptInterface::popString(L));
	} else {
		damage.primary.value = LuaScriptInterface::getNumber<int32_t>(L, -4);
		damage.primary.type = LuaScriptInterface::getNumber<CombatType_t>(L, -3);
		damage.secondary.value = LuaScriptInterface::getNumber<int32_t>(L, -2);
		damage.secondary.type = LuaScriptInterface::getNumber<CombatType_t>(L, -1);
		lua_pop(L, 4);
	}

	LuaScriptInterface::resetScriptEnv();
}

void CreatureEvent::executeDealtDamage(const std::shared_ptr<Player>& attacker, const std::shared_ptr<Creature>& target, int32_t damage, CombatType_t primaryType, CombatType_t secondaryType) {
    // onDealtDamage(player, target, damage, primaryType, secondaryType)
    if (!LuaScriptInterface::reserveScriptEnv()) {
        g_logger().error("[CreatureEvent::executeDealtDamage - "
                         "Player {} target {} event {}] "
                         "Call stack overflow. Too many lua script calls being nested.",
                         attacker->getName(), target->getName(), getName());
        return;
    }

    ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
    env->setScriptId(getScriptId(), getScriptInterface());

    lua_State* L = getScriptInterface()->getLuaState();
    getScriptInterface()->pushFunction(getScriptId());

    LuaScriptInterface::pushUserdata<Player>(L, attacker);
    LuaScriptInterface::setMetatable(L, -1, "Player");
    LuaScriptInterface::pushUserdata<Creature>(L, target);
    LuaScriptInterface::setCreatureMetatable(L, -1, target);
    lua_pushnumber(L, damage);
    lua_pushnumber(L, static_cast<lua_Number>(primaryType));
    lua_pushnumber(L, static_cast<lua_Number>(secondaryType));

    getScriptInterface()->callVoidFunction(5);
    // NÃO chamar resetScriptEnv aqui! callVoidFunction já o faz.
}

void CreatureEvents::playerOnDealtDamage(const std::shared_ptr<Player>& attacker, const std::shared_ptr<Creature>& target, int32_t damage, CombatType_t primaryType, CombatType_t secondaryType) const {
    for (const auto& [name, event] : creatureEvents) {
        if (event->getEventType() == CREATURE_EVENT_DEALT_DAMAGE) {
            event->executeDealtDamage(attacker, target, damage, primaryType, secondaryType);
        }
    }
}

void CreatureEvents::playerOnFightModeChange(const std::shared_ptr<Player>& player, FightMode_t oldMode, FightMode_t newMode) const {
    for (const auto& it : creatureEvents) {
        if (it.second->getEventType() == CREATURE_EVENT_FIGHT_MODE_CHANGE) {
            it.second->executeOnFightModeChange(player, oldMode, newMode);
        }
    }
}

void CreatureEvent::executeExtendedOpcode(const std::shared_ptr<Player> &player, uint8_t opcode, const std::string &buffer) const {
	// onExtendedOpcode(player, opcode, buffer)
	if (!LuaScriptInterface::reserveScriptEnv()) {
		g_logger().error("[CreatureEvent::executeExtendedOpcode - "
		                 "Player {} event {}] "
		                 "Call stack overflow. Too many lua script calls being nested.",
		                 player->getName(), getName());
		return;
	}

	ScriptEnvironment* env = LuaScriptInterface::getScriptEnv();
	env->setScriptId(getScriptId(), getScriptInterface());

	lua_State* L = getScriptInterface()->getLuaState();

	getScriptInterface()->pushFunction(getScriptId());

	LuaScriptInterface::pushUserdata<Player>(L, player);
	LuaScriptInterface::setMetatable(L, -1, "Player");

	lua_pushnumber(L, opcode);
	LuaScriptInterface::pushString(L, buffer);

	getScriptInterface()->callVoidFunction(3);
}
