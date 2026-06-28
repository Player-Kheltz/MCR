```lua
-- Brunak, the Legendary Blacksmith of Eridanus

local npcHandler = NpcHandler()
npcHandler:addModule(FocusModule())

function onSay(cid, words)
	if words:lower() == "hello" or words:lower() == "hi" then
		selfSay("Greetings! I am Brunak, the legendary blacksmith of Eridanus. Welcome to my forge!", cid)
	elseif words:lower() == "bye" or words:lower() == "farewell" then
		selfSay("Farewell! May your journey be safe and prosperous.", cid)
	else
		npcHandler:onSay(cid, words)
	end
end

function onBuy(cid, itemid, amount, fromPosition)
	local price = getItemPrice(itemid) * amount
	if getPlayerMoney(cid) < price then
		selfSay("I'm sorry, but you don't have enough gold to buy that.", cid)
	else
		doPlayerRemoveMoney(cid, price)
		doPlayerAddNPC(cid, itemid, amount)
		selfSay("Here is your " .. getArticle(itemid) .. " " .. getItemName(itemid), cid)
	end
end

function onSell(cid, itemid, amount, toPosition)
	local price = getItemPrice(itemid) * amount
	doPlayerRemoveNPC(cid, itemid, amount)
	doPlayerAddMoney(cid, price)
	selfSay("Thank you for your business! Here is your gold.", cid)
end

npcHandler:addCallback(CALLBACK_MESSAGE_DEFAULT, onSay)
npcHandler:addCallback(CALLBACK_SELL, onSell)
npcHandler:addCallback(CALLBACK_BUY, onBuy)

npcHandler:setMessage(MESSAGE_GREET, "Greetings! I am Brunak, the legendary blacksmith of Eridanus. Welcome to my forge!")
npcHandler:setMessage(MESSAGE_FAREWELL, "Farewell! May your journey be safe and prosperous.")
npcHandler:setMessage(MESSAGE_TRADE, "I can sell you various weapons and armors. What would you like?")
npcHandler:setMessage(MESSAGE_BUY, "Thank you for your purchase!")
npcHandler:setMessage(MESSAGE_SELL, "Thank you for selling to me!")

npcHandler:addModule(ShopModule({
	["sword"] = {id = 2460, price = 150},
	["shield"] = {id = 2478, price = 100},
	["helmet"] = {id = 2493, price = 120}
}))

npcHandler:addModule(InfoModule({
	text = "I am Brunak, the legendary blacksmith of Eridanus. I learned my craft from the anoes of Khaz-Durin. My weapons and armors are forged with the finest materials."
}))
```