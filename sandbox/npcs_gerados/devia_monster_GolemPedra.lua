-- monster: GolemPedra
local monster = Monster("GolemPedra")

monster:setSpeed(30)
monster:setOutfit({type = 12, head = 0, body = 0, legs = 0, feet = 0, addons = 0})
monster:setMaster(Player("NomeDoJogador"))
monster:setMaxHealth(500)
monster:addHealth(500)
monster:setCustomName("Golem de Pedra")
monster:setDropLoot({
    {id = 268, count = 1},
    {id = 374, count = 1}
})
monster:setPetBehavior()

print("monster GolemPedra carregado.")