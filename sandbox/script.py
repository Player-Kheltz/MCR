import os

# Define the path where the Lua script will be created
lua_script_path = r'E:\Projeto MCR\sandbox\testes_extensivos\output\test_npc.lua'

# Create the Lua script content
lua_content = """
-- test_npc.lua

function onNPCSpawn(npc)
    print("NPC spawned: " .. npc.name)
end

function onNPCDeath(npc)
    print("NPC died: " .. npc.name)
end

function onPlayerInteract(player, npc)
    print("Player interacted with NPC: " .. npc.name)
end
"""

# Write the Lua script to the specified path
with open(lua_script_path, 'w') as lua_file:
    lua_file.write(lua_content)

print(f"Lua script created at {lua_script_path}")

import os

# Define the path where the Lua script will be created
lua_script_path = r'E:\Projeto MCR\sandbox\testes_extensivos\output\test_npc.lua'

# Create the Lua script content
lua_content = """
-- test_npc.lua

function onNPCSpawn(npc)
    print("NPC spawned: " .. npc.name)
end

function onNPCDeath(npc)
    print("NPC died: " .. npc.name)
end

function onPlayerInteract(player, npc)
    print("Player interacted with NPC: " .. npc.name)
end
"""

# Write the Lua script to the specified path
with open(lua_script_path, 'w') as lua_file:
    lua_file.write(lua_content)

print(f"Lua script created at {lua_script_path}")