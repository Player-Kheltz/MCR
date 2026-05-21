--[[
    Projeto MCR ? SPA v4.0 ? SkillTrees (Pacotes de Habilidades)
--]]

SPA.skillTrees = {}

function SPA.registerSkillTree(name, config)
    SPA.skillTrees[name] = config
end

function SPA.checkSkillTrees(player)
    for name, cfg in pairs(SPA.skillTrees) do
        if not player:getStorageValue(STORAGE.SKILLTREE_BASE + (cfg.id or 0)) then
            local meetsReqs = true
            for _, domId in ipairs(cfg.dominios or {}) do
                if getNivelPorAfinidade(player:getDominioAfinidade(domId)) < (cfg.nivelMin or 1) then
                    meetsReqs = false; break
                end
            end
            if meetsReqs then
                for _, habId in ipairs(cfg.habilidades or {}) do
                    aprenderHabilidade(player, habId)
                end
                player:setStorageValue(STORAGE.SKILLTREE_BASE + (cfg.id or 0), 1)
                enviarMsgColorida(player, "Você aprendeu o estilo " .. c(name, COR.RARIDADE_LENDARIO) .. "!")
            end
        end
    end
end

print("DEBUG: skilltree.lua v4.0 carregado.")