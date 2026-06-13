/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (\251) 2019?present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "game/scheduling/save_manager.hpp"

#include "config/configmanager.hpp"
#include "creatures/players/grouping/guild.hpp"
#include "game/game.hpp"
#include "io/ioguild.hpp"
#include "io/iologindata.hpp"
#include "kv/kv.hpp"
#include "lib/di/container.hpp"
#include "creatures/players/player.hpp"

SaveManager::SaveManager(ThreadPool &threadPool, KVStore &kvStore, Logger &logger, Game &game) :
	threadPool(threadPool), kv(kvStore), logger(logger), game(game) { }

SaveManager &SaveManager::getInstance() {
	return inject<SaveManager>();
}

void SaveManager::saveAll() {
	Benchmark bm_saveAll;
	logger.info("Salvando servidor...");
	Benchmark bm_players;
	const auto &players = game.getPlayers();
	std::vector<std::pair<std::future<void>, std::string>> pending;
	const auto asyncSave = g_configManager().getBoolean(TOGGLE_SAVE_ASYNC);
	logger.info("Salvando {} jogadores... (Ass\355ncrono: {})", players.size(), asyncSave ? "Enabled" : "Disabled");
	std::vector<std::future<void>> futures;
	for (const auto &[_, player] : players) {
		player->loginPosition = player->getPosition();

		auto fut = threadPool.submit_task([this, player] {
			doSavePlayer(player);
		});
		pending.emplace_back(std::move(fut), player->getName());
	}

	for (auto &[future, name] : pending) {
		try {
			future.get();
		} catch (const std::exception &e) {
			logger.error("Falha ao salvar o jogador {}: {}", name, e.what());
		}
	}

	double duration_players = bm_players.duration();
	if (duration_players > 1000.0) {
		logger.info("Jogadores salvos em {:.2f} segundos.", duration_players / 1000.0);
	} else {
		logger.info("Jogadores salvos em {} milissegundos.", duration_players);
	}

	Benchmark bm_guilds;
	const auto &guilds = game.getGuilds();
	for (const auto &[_, guild] : guilds) {
		saveGuild(guild);
	}
	double duration_guilds = bm_guilds.duration();
	if (duration_guilds > 1000.0) {
		logger.info("Guildas salvas em {:.2f} segundos.", duration_guilds / 1000.0);
	} else {
		logger.info("Guildas salvas em {} milissegundos.", duration_guilds);
	}

	saveMap();
	saveKV();

	double duration_saveAll = bm_saveAll.duration();
	if (duration_saveAll > 1000.0) {
		logger.info("Servidor salvo em {:.2f} segundos.", duration_saveAll / 1000.0);
	} else {
		logger.info("Servidor salvo em {} milissegundos.", duration_saveAll);
	}
}

void SaveManager::scheduleAll() {
	auto scheduledAt = std::chrono::steady_clock::now();
	m_scheduledAt = scheduledAt;

	// Disable save async if the config is set to false
	if (!g_configManager().getBoolean(TOGGLE_SAVE_ASYNC)) {
		saveAll();
		return;
	}

	threadPool.detach_task([this, scheduledAt]() {
		if (m_scheduledAt.load() != scheduledAt) {
			logger.warn("Ignorando o salvamento do servidor porque outro salvamento foi agendado.");
			return;
		}
		saveAll();
	});
}

void SaveManager::schedulePlayer(std::weak_ptr<Player> playerPtr) {
	auto playerToSave = playerPtr.lock();
	if (!playerToSave) {
		logger.debug("Ignorando o salvamento do jogador porque o jogador n\343o est\341 mais online.");
		return;
	}

	// Disable save async if the config is set to false
	if (!g_configManager().getBoolean(TOGGLE_SAVE_ASYNC)) {
		if (g_game().getGameState() == GAME_STATE_NORMAL) {
			logger.debug("Salvando o jogador {}.", playerToSave->getName());
		}
		doSavePlayer(playerToSave);
		return;
	}

	logger.debug("Agendando o jogador {} para salvar.", playerToSave->getName());
	auto scheduledAt = std::chrono::steady_clock::now();
	m_playerMap[playerToSave->getGUID()] = scheduledAt;
	threadPool.detach_task([this, playerPtr, scheduledAt]() {
		auto player = playerPtr.lock();
		if (!player) {
			logger.debug("Ignorando o salvamento do jogador porque o jogador n\343o est\341 mais online.");
			return;
		}
		if (m_playerMap[player->getGUID()] != scheduledAt) {
			logger.warn("Ignorando o salvamento do jogador porque outro salvamento foi agendado.");
			return;
		}
		doSavePlayer(player);
	});
}

bool SaveManager::doSavePlayer(std::shared_ptr<Player> player) {
	if (!player) {
		logger.debug("Falha ao salvar o jogador porque o jogador \351 nulo.");
		return false;
	}

	Benchmark bm_savePlayer;
	Player::PlayerLock lock(player);
	m_playerMap.erase(player->getGUID());
	if (g_game().getGameState() == GAME_STATE_NORMAL) {
		logger.debug("Salvando o jogador {}.", player->getName());
	}

	bool saveSuccess = IOLoginData::savePlayer(player);
	if (!saveSuccess) {
		logger.error("Falha ao salvar o jogador {}.", player->getName());
	}

	auto duration = bm_savePlayer.duration();
	logger.debug("Salvar o jogador {} levou {} milissegundos.", player->getName(), duration);
	return saveSuccess;
}

bool SaveManager::savePlayer(std::shared_ptr<Player> player) {
	if (player->isOnline() && g_game().getGameState() != GAME_STATE_SHUTDOWN) {
		schedulePlayer(player);
		return true;
	}
	return doSavePlayer(player);
}

void SaveManager::saveGuild(std::shared_ptr<Guild> guild) {
	if (!guild) {
		logger.debug("Falha ao salvar a guilda porque a guilda \351 nula.");
		return;
	}

	Benchmark bm_saveGuild;
	logger.debug("Salvando guilda {}...", guild->getName());
	IOGuild::saveGuild(guild);

	auto duration = bm_saveGuild.duration();
	logger.debug("Salvar a guilda {} levou {} milissegundos.", guild->getName(), duration);
}

void SaveManager::saveMap() {
	Benchmark bm_saveMap;
	logger.debug("Salvando mapa...");
	bool saveSuccess = Map::save();
	if (!saveSuccess) {
		logger.error("Falha ao salvar o mapa.");
	}

	auto duration = bm_saveMap.duration();
	logger.debug("Mapa salvo em {} milissegundos.", duration);
}

void SaveManager::saveKV() {
	Benchmark bm_saveKV;
	logger.debug("Salvando armazenamento de valores-chave...");
	bool saveSuccess = kv.saveAll();
	if (!saveSuccess) {
		logger.error("Falha ao salvar o armazenamento de valores-chave.");
	}

	auto duration = bm_saveKV.duration();
	logger.debug("Armazenamento de valores-chave salvo em {} milissegundos.", duration);
}
