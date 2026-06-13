/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (\251) 2019?present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "io/ioprey.hpp"

#include "config/configmanager.hpp"
#include "creatures/monsters/monsters.hpp"
#include "creatures/players/player.hpp"
#include "game/game.hpp"
#include "lib/di/container.hpp"
#include "lib/metrics/metrics.hpp"
#include "server/network/message/networkmessage.hpp"

// Prey class
PreySlot::PreySlot(PreySlot_t id) :
	id(id) {
	eraseBonus();
	reloadBonusValue();
	reloadBonusType();
	freeRerollTimeStamp = OTSYS_TIME() + g_configManager().getNumber(PREY_FREE_REROLL_TIME) * 1000;
}

void PreySlot::reloadBonusType() {
	if (bonusRarity == 10) {
		PreyBonus_t bonus_tmp = bonus;
		while (bonus_tmp == bonus) {
			bonus = static_cast<PreyBonus_t>(uniform_random(PreyBonus_First, PreyBonus_Last));
		}
		return;
	}

	bonus = static_cast<PreyBonus_t>(uniform_random(PreyBonus_First, PreyBonus_Last));
}

void PreySlot::reloadBonusValue() {
	if (bonusRarity >= 9) {
		bonusRarity = 10;
	} else {
		// Every time you roll it will increase the rarity (star)
		bonusRarity = static_cast<uint8_t>(uniform_random(bonusRarity + 1, 10));
	}
	if (bonus == PreyBonus_Damage) {
		bonusPercentage = 2 * bonusRarity + 5;
	} else if (bonus == PreyBonus_Defense) {
		bonusPercentage = 2 * bonusRarity + 10;
	} else {
		bonusPercentage = 3 * bonusRarity + 10;
	}
}

void PreySlot::reloadMonsterGrid(std::vector<uint16_t> blackList, uint32_t level) {
	raceIdList.clear();

	if (!g_configManager().getBoolean(PREY_ENABLED)) {
		return;
	}

	// Disabling prey system if the server have less then 36 registered monsters on bestiary because:
	// - Impossible to generate random lists without duplications on slots.
	// - Stress the server with unnecessary loops.
	const std::map<uint16_t, std::string> &bestiary = g_game().getBestiaryList();
	if (bestiary.size() < 36) {
		g_logger().error("[PreySlot::reloadMonsterGrid] - Bestiary size is less than 36, disabling prey system.");
		return;
	}

	uint8_t stageOne;
	uint8_t stageTwo;
	uint8_t stageThree;
	uint8_t stageFour;
	if (auto levelStage = static_cast<uint32_t>(std::floor(level / 100));
	    levelStage == 0) { // From level 0 to 99
		stageOne = 3;
		stageTwo = 3;
		stageThree = 2;
		stageFour = 1;
	} else if (levelStage <= 2) { // From level 100 to 299
		stageOne = 1;
		stageTwo = 3;
		stageThree = 3;
		stageFour = 2;
	} else if (levelStage <= 4) { // From level 300 to 499
		stageOne = 1;
		stageTwo = 2;
		stageThree = 3;
		stageFour = 3;
	} else { // From level 500 to ...
		stageOne = 1;
		stageTwo = 1;
		stageThree = 3;
		stageFour = 4;
	}

	uint8_t tries = 0;
	auto maxIndex = static_cast<int32_t>(bestiary.size() - 1);
	while (raceIdList.size() < 9) {
		uint16_t raceId = (*(std::next(bestiary.begin(), uniform_random(0, maxIndex)))).first;
		tries++;

		if (std::count(blackList.begin(), blackList.end(), raceId) != 0) {
			continue;
		}

		blackList.push_back(raceId);
		const auto mtype = g_monsters().getMonsterTypeByRaceId(raceId);
		if (!mtype || mtype->info.experience == 0 || !mtype->info.isPreyable || mtype->info.isPreyExclusive) {
			continue;
		} else if (stageOne != 0 && mtype->info.bestiaryStars <= 1) {
			raceIdList.push_back(raceId);
			--stageOne;
		} else if (stageTwo != 0 && mtype->info.bestiaryStars == 2) {
			raceIdList.push_back(raceId);
			--stageTwo;
		} else if (stageThree != 0 && mtype->info.bestiaryStars == 3) {
			raceIdList.push_back(raceId);
			--stageThree;
		} else if (stageFour != 0 && mtype->info.bestiaryStars >= 4) {
			raceIdList.push_back(raceId);
			--stageFour;
		} else if (tries >= 10) {
			raceIdList.push_back(raceId);
			tries = 0;
		}
	}
}

// Task hunting class
TaskHuntingSlot::TaskHuntingSlot(PreySlot_t id) :
	id(id) {
	freeRerollTimeStamp = OTSYS_TIME() + g_configManager().getNumber(TASK_HUNTING_FREE_REROLL_TIME) * 1000;
}

void TaskHuntingSlot::reloadMonsterGrid(std::vector<uint16_t> blackList, uint32_t level) {
	raceIdList.clear();

	if (!g_configManager().getBoolean(TASK_HUNTING_ENABLED)) {
		return;
	}

	// Disabling task hunting system if the server have less then 36 registered monsters on bestiary because:
	// - Impossible to generate random lists without duplications on slots.
	// - Stress the server with unnecessary loops.
	const std::map<uint16_t, std::string> &bestiary = g_game().getBestiaryList();
	if (bestiary.size() < 36) {
		return;
	}

	uint8_t stageOne;
	uint8_t stageTwo;
	uint8_t stageThree;
	uint8_t stageFour;
	if (auto levelStage = static_cast<uint32_t>(std::floor(level / 100));
	    levelStage == 0) { // From level 0 to 99
		stageOne = 3;
		stageTwo = 3;
		stageThree = 2;
		stageFour = 1;
	} else if (levelStage <= 2) { // From level 100 to 299
		stageOne = 1;
		stageTwo = 3;
		stageThree = 3;
		stageFour = 2;
	} else if (levelStage <= 4) { // From level 300 to 499
		stageOne = 1;
		stageTwo = 2;
		stageThree = 3;
		stageFour = 3;
	} else { // From level 500 to ...
		stageOne = 1;
		stageTwo = 1;
		stageThree = 3;
		stageFour = 4;
	}

	uint8_t tries = 0;
	auto maxIndex = static_cast<int32_t>(bestiary.size() - 1);
	while (raceIdList.size() < 9) {
		uint16_t raceId = (*(std::next(bestiary.begin(), uniform_random(0, maxIndex)))).first;
		tries++;

		if (std::count(blackList.begin(), blackList.end(), raceId) != 0) {
			continue;
		}

		blackList.push_back(raceId);
		const auto mtype = g_monsters().getMonsterTypeByRaceId(raceId);
		if (!mtype || mtype->info.experience == 0 || !mtype->info.isPreyable || mtype->info.isPreyExclusive) {
			continue;
		} else if (stageOne != 0 && mtype->info.bestiaryStars <= 1) {
			raceIdList.push_back(raceId);
			--stageOne;
		} else if (stageTwo != 0 && mtype->info.bestiaryStars == 2) {
			raceIdList.push_back(raceId);
			--stageTwo;
		} else if (stageThree != 0 && mtype->info.bestiaryStars == 3) {
			raceIdList.push_back(raceId);
			--stageThree;
		} else if (stageFour != 0 && mtype->info.bestiaryStars >= 4) {
			raceIdList.push_back(raceId);
			--stageFour;
		} else if (tries >= 10) {
			raceIdList.push_back(raceId);
			tries = 0;
		}
	}
}

void TaskHuntingSlot::reloadReward() {
	if (!g_configManager().getBoolean(TASK_HUNTING_ENABLED)) {
		return;
	}

	if (rarity >= 4) {
		rarity = 5;
		return;
	}

	int32_t chance;
	if (rarity == 0) {
		chance = uniform_random(0, 100);
	} else if (rarity == 1) {
		chance = uniform_random(0, 70);
	} else if (rarity == 2) {
		chance = uniform_random(0, 45);
	} else if (rarity == 3) {
		chance = uniform_random(0, 20);
	} else {
		return;
	}

	if (chance <= 5) {
		rarity = 5;
	} else if (chance <= 20) {
		rarity = 4;
	} else if (chance <= 45) {
		rarity = 3;
	} else if (chance <= 70) {
		rarity = 2;
	} else {
		rarity = 1;
	}
}

IOPrey &IOPrey::getInstance() {
	return inject<IOPrey>();
}

// Prey/Task hunting global class
void IOPrey::checkPlayerPreys(const std::shared_ptr<Player> &player, uint8_t amount) const {
	if (!player) {
		return;
	}

	for (uint8_t slotId = PreySlot_First; slotId <= PreySlot_Last; slotId++) {
		if (const auto &slot = player->getPreySlotById(static_cast<PreySlot_t>(slotId));
		    slot && slot->isOccupied()) {
			if (slot->bonusTimeLeft <= amount) {
				if (slot->option == PreyOption_AutomaticReroll) {
					if (player->usePreyCards(static_cast<uint16_t>(g_configManager().getNumber(PREY_BONUS_REROLL_PRICE)))) {
						slot->reloadBonusType();
						slot->reloadBonusValue();
						slot->bonusTimeLeft = static_cast<uint16_t>(g_configManager().getNumber(PREY_BONUS_TIME));
						player->sendTextMessage(MESSAGE_STATUS, "Seu tipo e tempo de b\364nus de presa foram redefinidos com sucesso.");
						player->reloadPreySlot(static_cast<PreySlot_t>(slotId));
						continue;
					}

					player->sendTextMessage(MESSAGE_STATUS, "Voc\352 n\343o tem cartas de presa suficientes para ativar o reroll autom\341tico quando seu slot expirar.");
				} else if (slot->option == PreyOption_Locked) {
					if (player->usePreyCards(static_cast<uint16_t>(g_configManager().getNumber(PREY_SELECTION_LIST_PRICE)))) {
						slot->bonusTimeLeft = static_cast<uint16_t>(g_configManager().getNumber(PREY_BONUS_TIME));
						player->sendTextMessage(MESSAGE_STATUS, "Seu tempo de b\364nus de presa foi redefinido com sucesso.");
						player->reloadPreySlot(static_cast<PreySlot_t>(slotId));
						continue;
					}

					player->sendTextMessage(MESSAGE_STATUS, "Voc\352 n\343o tem cartas de presa suficientes para bloquear monstros e b\364nus quando o slot expirar.");
				} else {
					slot->reloadMonsterGrid(player->getPreyBlackList(), player->getLevel());
					player->sendTextMessage(MESSAGE_STATUS, "Seu b\364nus de presa expirou.");
				}

				slot->eraseBonus();
				player->reloadPreySlot(static_cast<PreySlot_t>(slotId));
			} else {
				slot->bonusTimeLeft -= amount;
				player->sendPreyTimeLeft(slot);
			}
		}
	}
}

void IOPrey::parsePreyAction(const std::shared_ptr<Player> &player, PreySlot_t slotId, PreyAction_t action, PreyOption_t option, int8_t index, uint16_t raceId) const {
	const auto &slot = player->getPreySlotById(slotId);
	if (!slot || slot->state == PreyDataState_Locked) {
		player->sendMessageDialog("Para desbloquear este slot de presa primeiro voc\352 deve compr\341-lo na loja.");
		return;
	}

	if (action == PreyAction_ListReroll) {
		if (slot->freeRerollTimeStamp > OTSYS_TIME() && !g_game().removeMoney(player, player->getPreyRerollPrice(), 0, true)) {
			player->sendMessageDialog("Voc\352 n\343o tem dinheiro suficiente para rolar novamente o slot de presa.");
			return;
		} else if (slot->freeRerollTimeStamp <= OTSYS_TIME()) {
			slot->freeRerollTimeStamp = OTSYS_TIME() + g_configManager().getNumber(PREY_FREE_REROLL_TIME) * 1000;
		} else {
			g_metrics().addCounter("balance_decrease", player->getPreyRerollPrice(), { { "player", player->getName() }, { "context", "prey_reroll" } });
		}

		slot->eraseBonus(true);
		if (slot->bonus != PreyBonus_None) {
			slot->state = PreyDataState_SelectionChangeMonster;
		}
		slot->reloadMonsterGrid(player->getPreyBlackList(), player->getLevel());
	} else if (action == PreyAction_ListAll_Cards) {
		if (!player->usePreyCards(static_cast<uint16_t>(g_configManager().getNumber(PREY_SELECTION_LIST_PRICE)))) {
			player->sendMessageDialog("Voc\352 n\343o tem cartas de presa suficientes para escolher um monstro da lista.");
			return;
		}

		slot->bonusTimeLeft = 0;
		slot->selectedRaceId = 0;
		slot->state = PreyDataState_ListSelection;
	} else if (action == PreyAction_ListAll_Selection) {
		const auto mtype = g_monsters().getMonsterTypeByRaceId(raceId);
		if (slot->isOccupied()) {
			player->sendMessageDialog("Voc\352 j\341 tem um monstro ativo neste slot de presa.");
			return;
		} else if (!slot->canSelect() || slot->state != PreyDataState_ListSelection) {
			player->sendMessageDialog("Ocorreu um erro ao processar sua a\347\343o. Por favor, tente reabrir a janela de presa.");
			return;
		} else if (player->getPreyWithMonster(raceId)) {
			player->sendMessageDialog("Esta criatura j\341 est\341 selecionada em outro espa\347o.");
			return;
		} else if (mtype && !mtype->info.isPreyable) {
			player->sendMessageDialog("This creature can't be select on prey. Please choose another one.");
			return;
		}

		if (slot->bonus == PreyBonus_None) {
			slot->reloadBonusType();
			slot->reloadBonusValue();
		}

		slot->state = PreyDataState_Active;
		slot->selectedRaceId = raceId;
		slot->removeMonsterType(raceId);
		slot->bonusTimeLeft = static_cast<uint16_t>(g_configManager().getNumber(PREY_BONUS_TIME));
	} else if (action == PreyAction_BonusReroll) {
		if (!slot->isOccupied()) {
			player->sendMessageDialog("Voc\352 n\343o tem nenhum monstro ativo neste slot de presa.");
			return;
		} else if (!player->usePreyCards(static_cast<uint16_t>(g_configManager().getNumber(PREY_BONUS_REROLL_PRICE)))) {
			player->sendMessageDialog("Voc\352 n\343o tem cartas de presa suficientes para rolar novamente este tipo de b\364nus de slot de presa.");
			return;
		}

		slot->reloadBonusType();
		slot->reloadBonusValue();
		slot->bonusTimeLeft = static_cast<uint16_t>(g_configManager().getNumber(PREY_BONUS_TIME));
	} else if (action == PreyAction_MonsterSelection) {
		if (slot->isOccupied()) {
			player->sendMessageDialog("Voc\352 j\341 tem um monstro ativo neste slot de presa.");
			return;
		} else if (!slot->canSelect() || index == -1 || (index + 1) > slot->raceIdList.size()) {
			player->sendMessageDialog("Ocorreu um erro ao processar sua a\347\343o. Por favor, tente reabrir a janela de presa.");
			return;
		} else if (player->getPreyWithMonster(slot->raceIdList[index])) {
			player->sendMessageDialog("Esta criatura j\341 est\341 selecionada em outro espa\347o.");
			return;
		}

		if (slot->bonus == PreyBonus_None) {
			slot->reloadBonusType();
			slot->reloadBonusValue();
		}
		slot->state = PreyDataState_Active;
		slot->selectedRaceId = slot->raceIdList[index];
		slot->removeMonsterType(slot->selectedRaceId);
		slot->bonusTimeLeft = static_cast<uint16_t>(g_configManager().getNumber(PREY_BONUS_TIME));
	} else if (action == PreyAction_Option) {
		if (option == PreyOption_AutomaticReroll && player->getPreyCards() < static_cast<uint64_t>(g_configManager().getNumber(PREY_BONUS_REROLL_PRICE))) {
			player->sendMessageDialog("Voc\352 n\343o tem cartas de presa suficientes para ativar o reroll autom\341tico quando seu slot expirar.");
			return;
		} else if (option == PreyOption_Locked && player->getPreyCards() < static_cast<uint64_t>(g_configManager().getNumber(PREY_SELECTION_LIST_PRICE))) {
			player->sendMessageDialog("Voc\352 n\343o tem cartas de presa suficientes para bloquear monstros e b\364nus quando o slot expirar.");
			return;
		}

		slot->option = option;
	} else {
		g_logger().warn("[IOPrey::parsePreyAction] - Unknown prey action: {}", fmt::underlying(action));
		return;
	}

	player->reloadPreySlot(slotId);
}

void IOPrey::parseTaskHuntingAction(const std::shared_ptr<Player> &player, PreySlot_t slotId, PreyTaskAction_t action, bool upgrade, uint16_t raceId) const {
	const auto &slot = player->getTaskHuntingSlotById(slotId);
	if (!slot || slot->state == PreyTaskDataState_Locked) {
		player->sendMessageDialog("Para desbloquear este slot de ca\347a de tarefas, primeiro voc\352 deve compr\341-lo na loja.");
		return;
	}

	if (action == PreyTaskAction_ListReroll) {
		if (slot->disabledUntilTimeStamp >= OTSYS_TIME()) {
			std::ostringstream ss;
			ss << "Voc\352 precisa esperar " << ((slot->disabledUntilTimeStamp - OTSYS_TIME()) / 60000) << " minutes to select a new creature on task.";
			player->sendMessageDialog(ss.str());
			return;
		} else if (slot->freeRerollTimeStamp > OTSYS_TIME() && !g_game().removeMoney(player, player->getTaskHuntingRerollPrice(), 0, true)) {
			player->sendMessageDialog("Voc\352 n\343o tem dinheiro suficiente para rolar novamente o slot de busca de tarefas.");
			return;
		} else if (slot->freeRerollTimeStamp <= OTSYS_TIME()) {
			slot->freeRerollTimeStamp = OTSYS_TIME() + g_configManager().getNumber(TASK_HUNTING_FREE_REROLL_TIME) * 1000;
		} else {
			g_metrics().addCounter("balance_decrease", player->getTaskHuntingRerollPrice(), { { "player", player->getName() }, { "context", "hunting_task_reroll" } });
		}

		slot->eraseTask();
		slot->reloadReward();
		slot->state = PreyTaskDataState_Selection;
		slot->reloadMonsterGrid(player->getTaskHuntingBlackList(), player->getLevel());
	} else if (action == PreyTaskAction_RewardsReroll) {
		if (!player->usePreyCards(static_cast<uint16_t>(g_configManager().getNumber(TASK_HUNTING_BONUS_REROLL_PRICE)))) {
			player->sendMessageDialog("Voc\352 n\343o tem cartas de presa suficientes para rolar novamente a raridade da recompensa da sua tarefa.");
			return;
		}

		slot->reloadReward();
	} else if (action == PreyTaskAction_ListAll_Cards) {
		if (slot->disabledUntilTimeStamp >= OTSYS_TIME()) {
			std::ostringstream ss;
			ss << "Voc\352 precisa esperar " << ((slot->disabledUntilTimeStamp - OTSYS_TIME()) / 60000) << " minutes to select a new creature on task.";
			player->sendMessageDialog(ss.str());
			return;
		} else if (!player->usePreyCards(static_cast<uint16_t>(g_configManager().getNumber(TASK_HUNTING_SELECTION_LIST_PRICE)))) {
			player->sendMessageDialog("Voc\352 n\343o tem cartas de presa suficientes para escolher uma criatura na lista para seu slot de ca\347a de tarefas.");
			return;
		}

		slot->selectedRaceId = 0;
		slot->state = PreyTaskDataState_ListSelection;
	} else if (action == PreyTaskAction_MonsterSelection) {
		if (slot->disabledUntilTimeStamp >= OTSYS_TIME()) {
			std::ostringstream ss;
			ss << "Voc\352 precisa esperar " << ((slot->disabledUntilTimeStamp - OTSYS_TIME()) / 60000) << " minutes to select a new creature on task.";
			player->sendMessageDialog(ss.str());
			return;
		} else if (!slot->canSelect()) {
			player->sendMessageDialog("Ocorreu um erro ao processar sua a\347\343o. Tente reabrir a janela de tarefas.");
			return;
		} else if (slot->isOccupied()) {
			player->sendMessageDialog("Voc\352 j\341 tem um monstro ativo neste slot de ca\347a de tarefas.");
			return;
		} else if (slot->state == PreyTaskDataState_Selection && !slot->isCreatureOnList(raceId)) {
			player->sendMessageDialog("Ocorreu um erro ao processar sua a\347\343o. Tente reabrir a janela de tarefas.");
			return;
		} else if (player->getTaskHuntingWithCreature(raceId)) {
			player->sendMessageDialog("Esta criatura j\341 est\341 selecionada em outro espa\347o.");
			return;
		}

		if (const auto mtype = g_monsters().getMonsterTypeByRaceId(raceId)) {
			slot->currentKills = 0;
			slot->selectedRaceId = raceId;
			slot->removeMonsterType(raceId);
			slot->state = PreyTaskDataState_Active;
			slot->upgrade = upgrade && player->isCreatureUnlockedOnTaskHunting(mtype);
		}
	} else if (action == PreyTaskAction_Cancel) {
		if (!g_game().removeMoney(player, player->getTaskHuntingRerollPrice(), 0, true)) {
			player->sendMessageDialog("Voc\352 n\343o tem dinheiro suficiente para cancelar sua busca de tarefas atual.");
			return;
		}

		g_metrics().addCounter("balance_decrease", player->getTaskHuntingRerollPrice(), { { "player", player->getName() }, { "context", "hunting_task_cancel" } });
		slot->eraseTask();
		slot->reloadReward();
		slot->state = PreyTaskDataState_Selection;
		slot->reloadMonsterGrid(player->getTaskHuntingBlackList(), player->getLevel());
	} else if (action == PreyTaskAction_Claim) {
		if (!slot->isOccupied()) {
			player->sendMessageDialog("Voc\352 n\343o pode reivindicar sua recompensa de tarefa com um espa\347o de ca\347a de tarefa vazio.");
			return;
		}

		if (const auto &option = getTaskRewardOption(slot)) {
			uint64_t reward;
			int32_t boostChange = uniform_random(0, 100);
			if (slot->rarity >= 4 && boostChange <= 5) {
				boostChange = 20;
			} else if (slot->rarity >= 4 && boostChange <= 10) {
				boostChange = 15;
			} else {
				boostChange = 10;
			}

			if (slot->upgrade && slot->currentKills >= option->secondKills) {
				reward = option->secondReward;
			} else if (!slot->upgrade && slot->currentKills >= option->firstKills) {
				reward = option->firstReward;
			} else {
				player->sendMessageDialog("Ocorreu um erro ao processar sua recompensa de ca\347a \340 tarefa. Por favor, tente reabrir a janela.");
				return;
			}

			std::ostringstream ss;
			reward = static_cast<uint64_t>(std::ceil((reward * boostChange) / 10));
			ss << "Parab\351ns! Voc\352 ganhou " << reward;
			if (boostChange == 20) {
				ss << " Pontos de tarefa de ca\347a incluindo um b\364nus de 100%.";
			} else if (boostChange == 15) {
				ss << " Pontos de tarefa de ca\347a incluindo um b\364nus de 50%.";
			} else {
				ss << " Pontos de tarefa de ca\347a.";
			}

			slot->eraseTask();
			slot->reloadReward();
			slot->state = PreyTaskDataState_Inactive;
			player->addTaskHuntingPoints(reward);
			player->sendMessageDialog(ss.str());
			slot->reloadMonsterGrid(player->getTaskHuntingBlackList(), player->getLevel());
			slot->disabledUntilTimeStamp = OTSYS_TIME() + g_configManager().getNumber(TASK_HUNTING_LIMIT_EXHAUST) * 1000;
		}
	} else {
		g_logger().warn("[IOPrey::parseTaskHuntingAction] - Unknown task action: {}", fmt::underlying(action));
		return;
	}
	player->reloadTaskSlot(slotId);
}

void IOPrey::initializeTaskHuntOptions() {
	if (!g_configManager().getBoolean(TASK_HUNTING_ENABLED)) {
		return;
	}

	// Move it to config.lua

	// Kill stage is the multiplier for kills and rewards on task hunting
	uint8_t killStage = 25;

	// This is hardcoded on client but i'm saving it in case that they change it in the future
	uint8_t limitOfStars = 5;
	uint16_t kills = killStage;
	NetworkMessage msg;
	for (uint8_t difficulty = PreyTaskDifficult_First; difficulty <= PreyTaskDifficult_Last; ++difficulty) { // Difficulties of creatures on bestiary.
		auto reward = static_cast<uint16_t>(std::round((10 * kills) / killStage));
		// Amount of task stars on task hunting
		for (uint8_t star = 1; star <= limitOfStars; ++star) {
			const auto &option = taskOption.emplace_back(std::make_unique<TaskHuntingOption>());

			option->difficult = static_cast<PreyTaskDifficult_t>(difficulty);
			option->rarity = star;

			option->firstKills = kills;
			option->firstReward = reward;

			option->secondKills = kills * 2;
			option->secondReward = reward * 2;

			reward = static_cast<uint16_t>(std::round((reward * (115 + (difficulty * limitOfStars))) / 100));
		}

		kills *= 4;
	}

	msg.addByte(0xBA);
	const std::map<uint16_t, std::string> &bestiaryList = g_game().getBestiaryList();
	msg.add<uint16_t>(static_cast<uint16_t>(bestiaryList.size()));
	std::for_each(bestiaryList.begin(), bestiaryList.end(), [&msg](auto mType) {
		const auto mtype = g_monsters().getMonsterType(mType.second);
		if (!mtype) {
			return;
		}

		msg.add<uint16_t>(mtype->info.raceid);
		if (mtype->info.bestiaryStars <= 1) {
			msg.addByte(0x01);
		} else if (mtype->info.bestiaryStars <= 3) {
			msg.addByte(0x02);
		} else {
			msg.addByte(0x03);
		}
	});

	msg.addByte(static_cast<uint8_t>(taskOption.size()));
	std::for_each(taskOption.begin(), taskOption.end(), [&msg](const std::unique_ptr<TaskHuntingOption> &option) {
		msg.addByte(static_cast<uint8_t>(option->difficult));
		msg.addByte(option->rarity);
		msg.add<uint16_t>(option->firstKills);
		msg.add<uint16_t>(option->firstReward);
		msg.add<uint16_t>(option->secondKills);
		msg.add<uint16_t>(option->secondReward);
	});
	m_baseDataMessage = msg;
}

NetworkMessage IOPrey::getTaskHuntingBaseDate() const {
	return m_baseDataMessage;
}

const std::unique_ptr<TaskHuntingOption> &IOPrey::getTaskRewardOption(const std::unique_ptr<TaskHuntingSlot> &slot) const {
	if (!slot) {
		return TaskHuntingOptionNull;
	}

	const auto mtype = g_monsters().getMonsterTypeByRaceId(slot->selectedRaceId);
	if (!mtype) {
		return TaskHuntingOptionNull;
	}

	PreyTaskDifficult_t difficult;
	if (mtype->info.bestiaryStars <= 1) {
		difficult = PreyTaskDifficult_Easy;
	} else if (mtype->info.bestiaryStars <= 3) {
		difficult = PreyTaskDifficult_Medium;
	} else {
		difficult = PreyTaskDifficult_Hard;
	}

	auto it = std::find_if(taskOption.begin(), taskOption.end(), [difficult, &slot](const std::unique_ptr<TaskHuntingOption> &optionIt) {
		return optionIt->difficult == difficult && optionIt->rarity == slot->rarity;
	});

	if (it != taskOption.end()) {
		return *it;
	}

	return TaskHuntingOptionNull;
}
