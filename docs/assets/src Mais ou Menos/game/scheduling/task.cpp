/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (\251) 2019?present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "game/scheduling/task.hpp"

#include "lib/metrics/metrics.hpp"

#include "utils/tools.hpp"

std::atomic_uint_fast64_t Task::LAST_EVENT_ID = 0;

Task::Task(uint32_t expiresAfterMs, std::function<void(void)> &&f, std::string_view context) :
	func(std::move(f)), context(context), utime(OTSYS_TIME()),
	expiration(expiresAfterMs > 0 ? OTSYS_TIME() + expiresAfterMs : 0) {
	if (this->context.empty()) {
		g_logger().error("[{}]: o contexto da tarefa n\343o pode estar vazio!", __FUNCTION__);
		return;
	}

	assert(!this->context.empty() && "O contexto n\343o pode estar vazio!");
}

Task::Task(std::function<void(void)> &&f, std::string_view context, uint32_t delay, bool cycle /* = false*/, bool log /*= true*/) :
	func(std::move(f)), context(context), utime(OTSYS_TIME() + delay), delay(delay),
	cycle(cycle), log(log) {
	if (this->context.empty()) {
		g_logger().error("[{}]: o contexto da tarefa n\343o pode estar vazio!", __FUNCTION__);
		return;
	}

	assert(!this->context.empty() && "O contexto n\343o pode estar vazio!");
}

[[nodiscard]] bool Task::hasExpired() const {
	return expiration != 0 && expiration < OTSYS_TIME();
}

bool Task::execute() const {
	metrics::task_latency measure(context);
	if (isCanceled()) {
		return false;
	}

	if (hasExpired()) {
		g_logger().info("A tarefa '{}' expirou, n\343o foi executada em {}.", getContext(), expiration - utime);
		return false;
	}

	if (log) {
		if (hasTraceableContext()) {
			g_logger().trace("Executando tarefa {}.", getContext());
		} else {
			g_logger().debug("Executando tarefa {}.", getContext());
		}
	}

	func();
	return true;
}

void Task::updateTime() {
	utime = OTSYS_TIME() + delay;
}
