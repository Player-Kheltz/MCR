/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (\251) 2019?present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */
#include "lib/di/soft_singleton.hpp"

#include "utils/tools.hpp"

SoftSingleton::SoftSingleton(std::string id) :
	id(std::move(id)) { }

void SoftSingleton::increment() {
	instance_count++;
	if (instance_count > 1) {
		logger.warn(
			"{} inst\342ncias criadas para {}. Este \351 um singleton suave, voc\352 provavelmente desejar\341 usar g_{}.",
			instance_count,
			id,
			asLowerCaseString(id)
		);
	}
}

void SoftSingleton::decrement() {
	instance_count--;
}

SoftSingletonGuard::SoftSingletonGuard(SoftSingleton &t) :
	tracker(t) {
	tracker.increment();
}

SoftSingletonGuard::~SoftSingletonGuard() {
	tracker.decrement();
}
