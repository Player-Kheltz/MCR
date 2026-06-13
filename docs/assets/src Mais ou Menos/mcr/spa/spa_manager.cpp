#include "spa_manager.hpp"
#include "database/database.hpp"

bool SPAManager::registerDomain(int32_t id, const std::string& name, int32_t parentId) {
    if (m_domains.find(id) != m_domains.end()) {
        return false;
    }
    DomainDef def{id, name, parentId};
    m_domains[id] = def;

    Database::getInstance().executeQuery(
        fmt::format("INSERT INTO dominios_def (id, nome, parent_id) VALUES ({}, '{}', {}) ON DUPLICATE KEY UPDATE nome='{}', parent_id={}",
            id, name, parentId, name, parentId)
    );
    return true;
}

const DomainDef* SPAManager::getDomain(int32_t id) const {
    auto it = m_domains.find(id);
    return it != m_domains.end() ? &it->second : nullptr;
}

std::vector<int32_t> SPAManager::getChildren(int32_t parentId) const {
    std::vector<int32_t> children;
    for (const auto& [id, def] : m_domains) {
        if (def.parentId == parentId) {
            children.push_back(id);
        }
    }
    return children;
}

std::vector<int32_t> SPAManager::getAllDomainIds() const {
    std::vector<int32_t> ids;
    for (const auto& [id, _] : m_domains) {
        ids.push_back(id);
    }
    return ids;
}

void SPAManager::registerEvent(const std::string& name, EventCallback callback) {
    m_events[name].push_back(callback);
}

void SPAManager::dispatchEvent(const std::string& name, lua_State* L, int nargs) {
    auto it = m_events.find(name);
    if (it != m_events.end()) {
        for (auto& cb : it->second) {
            cb(L, nargs);
        }
    }
}

// ============================================================
// SISTEMA DE PETS
// ============================================================
bool SPAManager::registerPet(uint32_t playerId, uint32_t petId) {
    uint32_t current = getPetCount(playerId);
    uint32_t max = getPetMax(playerId);
    if (current >= max) return false;
    m_playerPets[playerId].push_back(petId);
    m_petMaster[petId] = playerId;
    m_petData[petId] = PetData{}; // default behavior/domain
    return true;
}

void SPAManager::unregisterPet(uint32_t playerId, uint32_t petId) {
    auto it = m_playerPets.find(playerId);
    if (it != m_playerPets.end()) {
        auto& vec = it->second;
        vec.erase(std::remove(vec.begin(), vec.end(), petId), vec.end());
        if (vec.empty()) m_playerPets.erase(it);
    }
    m_petMaster.erase(petId);
    m_petData.erase(petId);
}

std::vector<uint32_t> SPAManager::getPets(uint32_t playerId) const {
    auto it = m_playerPets.find(playerId);
    return (it != m_playerPets.end()) ? it->second : std::vector<uint32_t>{};
}

uint32_t SPAManager::getPetCount(uint32_t playerId) const {
    auto it = m_playerPets.find(playerId);
    return (it != m_playerPets.end()) ? static_cast<uint32_t>(it->second.size()) : 0;
}

void SPAManager::setPetMax(uint32_t playerId, uint32_t max) {
    m_playerPetMax[playerId] = max;
}

uint32_t SPAManager::getPetMax(uint32_t playerId) const {
    auto it = m_playerPetMax.find(playerId);
    return (it != m_playerPetMax.end()) ? it->second : 1;
}

bool SPAManager::isPet(uint32_t creatureId) const {
    return m_petMaster.find(creatureId) != m_petMaster.end();
}

uint32_t SPAManager::getPetMasterId(uint32_t creatureId) const {
    auto it = m_petMaster.find(creatureId);
    return (it != m_petMaster.end()) ? it->second : 0;
}

void SPAManager::setPetBehavior(uint32_t creatureId, uint32_t behavior) {
    m_petData[creatureId].behavior = behavior;
}

uint32_t SPAManager::getPetBehavior(uint32_t creatureId) const {
    auto it = m_petData.find(creatureId);
    return (it != m_petData.end()) ? it->second.behavior : 1;
}

void SPAManager::setPetDomain(uint32_t creatureId, uint32_t domain) {
    m_petData[creatureId].domain = domain;
}

uint32_t SPAManager::getPetDomain(uint32_t creatureId) const {
    auto it = m_petData.find(creatureId);
    return (it != m_petData.end()) ? it->second.domain : 28;
}