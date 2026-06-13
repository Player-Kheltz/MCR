#pragma once
#include <map>
#include <string>
#include <vector>
#include <cstdint>
#include <functional>

struct DomainDef {
    int32_t id;
    std::string name;
    int32_t parentId = 0;
};

struct PetData {
    uint32_t behavior = 1; // 1=defensive
    uint32_t domain = 28;  // Summon default
};

class SPAManager {
public:
    static SPAManager& getInstance() {
        static SPAManager instance;
        return instance;
    }

    bool registerDomain(int32_t id, const std::string& name, int32_t parentId = 0);
    const DomainDef* getDomain(int32_t id) const;
    std::vector<int32_t> getChildren(int32_t parentId) const;
    std::vector<int32_t> getAllDomainIds() const;

    using EventCallback = std::function<void(lua_State* L, int nargs)>;
    void registerEvent(const std::string& name, EventCallback callback);
    void dispatchEvent(const std::string& name, lua_State* L, int nargs);

    // Pets
    bool registerPet(uint32_t playerId, uint32_t petId);
    void unregisterPet(uint32_t playerId, uint32_t petId);
    std::vector<uint32_t> getPets(uint32_t playerId) const;
    uint32_t getPetCount(uint32_t playerId) const;
    void setPetMax(uint32_t playerId, uint32_t max);
    uint32_t getPetMax(uint32_t playerId) const;
    bool isPet(uint32_t creatureId) const;
    uint32_t getPetMasterId(uint32_t creatureId) const;

    // Comportamento e domínio do pet
    void setPetBehavior(uint32_t creatureId, uint32_t behavior);
    uint32_t getPetBehavior(uint32_t creatureId) const;
    void setPetDomain(uint32_t creatureId, uint32_t domain);
    uint32_t getPetDomain(uint32_t creatureId) const;

private:
    SPAManager() = default;
    std::map<int32_t, DomainDef> m_domains;
    std::map<std::string, std::vector<EventCallback>> m_events;

    std::map<uint32_t, std::vector<uint32_t>> m_playerPets;
    std::map<uint32_t, uint32_t> m_petMaster;
    std::map<uint32_t, uint32_t> m_playerPetMax;
    std::map<uint32_t, PetData> m_petData;  // comportamento, domínio, etc.
};