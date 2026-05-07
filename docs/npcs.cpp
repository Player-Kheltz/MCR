//////////////////////////////////////////////////////////////////////
// This file is part of Remere's Map Editor
//////////////////////////////////////////////////////////////////////
// Remere's Map Editor is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Remere's Map Editor is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.
//////////////////////////////////////////////////////////////////////

#include "main.h"

#include "gui.h"
#include "materials.h"
#include "brush.h"
#include "npcs.h"
#include "npc_brush.h"

#include <wx/dir.h>

#include "lua_parser.h"

NpcDatabase g_npcs;

static std::string latin1_to_utf8(const std::string &input) {
    std::string output;
    output.reserve(input.size());
    for (unsigned char c : input) {
        if (c < 0x80) {
            output.push_back(c);
        } else {
            output.push_back(0xC0 | (c >> 6));
            output.push_back(0x80 | (c & 0x3F));
        }
    }
    return output;
}

static std::string npcs_to_latin1(const std::string &str) {
    bool isUtf8 = true;
    size_t i = 0;
    while (i < str.size()) {
        unsigned char c = str[i];
        if (c <= 0x7F) { ++i; continue; }
        else if (c >= 0xC2 && c <= 0xDF) {
            if (i+1 >= str.size() || (str[i+1] & 0xC0) != 0x80) { isUtf8 = false; break; }
            i += 2;
        } else if (c >= 0xE0 && c <= 0xEF) {
            if (i+2 >= str.size() || (str[i+1] & 0xC0) != 0x80 || (str[i+2] & 0xC0) != 0x80) { isUtf8 = false; break; }
            i += 3;
        } else if (c >= 0xF0 && c <= 0xF4) {
            if (i+3 >= str.size() || (str[i+1] & 0xC0) != 0x80 || (str[i+2] & 0xC0) != 0x80 || (str[i+3] & 0xC0) != 0x80) { isUtf8 = false; break; }
            i += 4;
        } else {
            isUtf8 = false; break;
        }
    }
    if (!isUtf8) return str;

    std::string result;
    for (size_t j = 0; j < str.size(); ++j) {
        unsigned char c = str[j];
        if (c <= 0x7F) {
            result += c;
        } else if ((c & 0xE0) == 0xC0 && j+1 < str.size()) {
            unsigned char c2 = str[++j];
            uint16_t code = ((c & 0x1F) << 6) | (c2 & 0x3F);
            result += (code <= 0xFF) ? static_cast<char>(code) : '?';
        } else {
            result += '?';
        }
    }
    return result;
}

NpcType::NpcType() :
	isNpc(true),
	missing(false),
	in_other_tileset(false),
	standard(false),
	name(""),
	brush(nullptr) {
	////
}

NpcType::NpcType(const NpcType &npc) :
	isNpc(npc.isNpc),
	missing(npc.missing),
	in_other_tileset(npc.in_other_tileset),
	standard(npc.standard),
	name(npc.name),
	outfit(npc.outfit),
	brush(npc.brush) {
	////
}

NpcType &NpcType::operator=(const NpcType &npc) {
	isNpc = npc.isNpc;
	missing = npc.missing;
	in_other_tileset = npc.in_other_tileset;
	standard = npc.standard;
	name = npc.name;
	outfit = npc.outfit;
	brush = npc.brush;
	return *this;
}

NpcType::~NpcType() {
	////
}

NpcType* NpcType::loadFromOTXML(const FileName &filename, pugi::xml_document &doc, wxArrayString &warnings) {
	ASSERT(doc != nullptr);

	pugi::xml_node node;
	if (!(node = doc.child("npc"))) {
		warnings.push_back("This file is not a npc file");
		return nullptr;
	}

	pugi::xml_attribute attribute;
	if (!(attribute = node.attribute("name"))) {
		warnings.push_back("Couldn't read name tag of npc node.");
		return nullptr;
	}

	NpcType* npcType = newd NpcType();
	npcType->name = nstr(filename.GetName());

	for (pugi::xml_node optionNode = node.first_child(); optionNode; optionNode = optionNode.next_sibling()) {
		if (as_lower_str(optionNode.name()) != "look") {
			continue;
		}

		if ((attribute = optionNode.attribute("type"))) {
			npcType->outfit.lookType = attribute.as_int();
		}

		if ((attribute = optionNode.attribute("item")) || (attribute = optionNode.attribute("lookex")) || (attribute = optionNode.attribute("typeex"))) {
			npcType->outfit.lookItem = attribute.as_int();
		}

		if ((attribute = optionNode.attribute("addon"))) {
			npcType->outfit.lookAddon = attribute.as_int();
		}

		if ((attribute = optionNode.attribute("head"))) {
			npcType->outfit.lookHead = attribute.as_int();
		}

		if ((attribute = optionNode.attribute("body"))) {
			npcType->outfit.lookBody = attribute.as_int();
		}

		if ((attribute = optionNode.attribute("legs"))) {
			npcType->outfit.lookLegs = attribute.as_int();
		}

		if ((attribute = optionNode.attribute("feet"))) {
			npcType->outfit.lookFeet = attribute.as_int();
		}
	}
	return npcType;
}

NpcDatabase::NpcDatabase() {
	////
}

NpcDatabase::~NpcDatabase() {
	clear();
}

void NpcDatabase::clear() {
	for (NpcMap::iterator iter = npcMap.begin(); iter != npcMap.end(); ++iter) {
		delete iter->second;
	}
	npcMap.clear();
}

NpcType* NpcDatabase::operator[](const std::string &name) {
	NpcMap::iterator iter = npcMap.find(as_lower_str(name));
	if (iter != npcMap.end()) {
		return iter->second;
	}
	return nullptr;
}

NpcType* NpcDatabase::addMissingNpcType(const std::string &name) {
	assert((*this)[name] == nullptr);

	NpcType* npcType = newd NpcType();
	npcType->name = name;
	npcType->missing = true;
	npcType->outfit.lookType = 130;

	npcMap.insert(std::make_pair(as_lower_str(name), npcType));
	return npcType;
}

NpcType* NpcDatabase::addNpcType(const std::string &name, const Outfit &outfit) {
	assert((*this)[name] == nullptr);

	NpcType* npcType = newd NpcType();
	npcType->name = name;
	npcType->missing = false;
	npcType->outfit = outfit;

	npcMap.insert(std::make_pair(as_lower_str(name), npcType));
	return npcType;
}

bool NpcDatabase::hasMissing() const {
	for (NpcMap::const_iterator iter = npcMap.begin(); iter != npcMap.end(); ++iter) {
		if (iter->second->missing) {
			return true;
		}
	}
	return false;
}

bool NpcDatabase::importXMLFromOT(const FileName &filename, wxString &error, wxArrayString &warnings) {
	pugi::xml_document doc;
	pugi::xml_parse_result result = doc.load_file(filename.GetFullPath().mb_str());
	if (!result) {
		error = "Couldn't open file \"" + filename.GetFullName() + "\", invalid format?";
		return false;
	}

	pugi::xml_node node;
	if ((node = doc.child("npc"))) {
		NpcType* npcType = NpcType::loadFromOTXML(filename, doc, warnings);
		if (npcType) {
			NpcType* current = (*this)[npcType->name];

			if (current) {
				*current = *npcType;
				delete npcType;
			} else {
				npcMap[as_lower_str(npcType->name)] = npcType;

				Tileset* tileSet = nullptr;
				tileSet = g_materials.tilesets["NPCs"];
				ASSERT(tileSet != nullptr);

				Brush* brush = newd NpcBrush(npcType);
				g_brushes.addBrush(brush);

				TilesetCategory* tileSetCategory = tileSet->getCategory(TILESET_NPC);
				tileSetCategory->brushlist.push_back(brush);
			}
		}
	} else {
		error = "This is not valid OT npc data file.";
		return false;
	}
	return true;
}

bool NpcDatabase::saveToXML(const FileName &filename) {
	pugi::xml_document doc;

	pugi::xml_node decl = doc.prepend_child(pugi::node_declaration);
	decl.append_attribute("version") = "1.0";

	pugi::xml_node npcNodes = doc.append_child("npcs");
	for (const auto &npcEntry : npcMap) {
		NpcType* npcType = npcEntry.second;
		if (!npcType->standard) {
			pugi::xml_node npcNode = npcNodes.append_child("npc");

			npcNode.append_attribute("name") = npcType->name.c_str();
			npcNode.append_attribute("type") = "npc";

			const Outfit &outfit = npcType->outfit;
			npcNode.append_attribute("looktype") = outfit.lookType;
			npcNode.append_attribute("lookitem") = outfit.lookItem;
			npcNode.append_attribute("lookaddon") = outfit.lookAddon;
			npcNode.append_attribute("lookhead") = outfit.lookHead;
			npcNode.append_attribute("lookbody") = outfit.lookBody;
			npcNode.append_attribute("looklegs") = outfit.lookLegs;
			npcNode.append_attribute("lookfeet") = outfit.lookFeet;
		}
	}
	return doc.save_file(filename.GetFullPath().mb_str(), "\t", pugi::format_default, pugi::encoding_utf8);
}

wxArrayString NpcDatabase::getMissingNpcNames() const {
	wxArrayString missingNpcs;
	for (const auto &ncpEntry : npcMap) {
		if (ncpEntry.second->missing) {
			missingNpcs.Add(ncpEntry.second->name);
		}
	}
	return missingNpcs;
}

bool NpcDatabase::loadFromLuaDir(const wxString &directory, wxString &error, wxArrayString &warnings) {
    if (directory.IsEmpty() || !wxDir::Exists(directory)) {
        return true;
    }

    wxArrayString luaFiles;
    wxDir::GetAllFiles(directory, &luaFiles, "*.lua", wxDIR_FILES | wxDIR_DIRS | wxDIR_HIDDEN);

    int fileCount = 0;
    for (const auto &filePath : luaFiles) {
        if (++fileCount % 50 == 0) {
            wxSafeYield();
        }
        std::string rawContent = LuaParser::readFileContent(filePath.ToStdString());
		std::string content = latin1_to_utf8(rawContent);
        if (content.empty()) {
            warnings.push_back("Could not open: " + filePath);
            continue;
        }

        std::string name = LuaParser::parseCreateCall(content, "Game.createNpcType");
        if (name.empty()) {
            name = LuaParser::parseLocalString(content, "internalNpcName");
        }
        if (name.empty()) {
            continue;
        }
        // Converte o nome para Latin-1
        name = npcs_to_latin1(name);

        NpcType* existing = (*this)[name];
        if (existing) {
            if (!existing->missing) {
                continue;
            }
            if (LuaParser::parseOutfit(content, existing->outfit)) {
                existing->missing = false;
            }
            continue;
        }

        NpcType* npcType = newd NpcType();
        npcType->name = name;
        npcType->outfit.name = name;
        npcType->standard = false;

        if (!LuaParser::parseOutfit(content, npcType->outfit)) {
            delete npcType;
            continue;
        }

        npcMap[as_lower_str(npcType->name)] = npcType;
    }
    return true;
}
