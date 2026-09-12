"""Small derived view; original records remain authoritative in the archive."""

from .archive import json_bytes
import hashlib

RACES = {1: "Human", 2: "Orc", 3: "Dwarf", 4: "Night Elf", 5: "Undead", 6: "Tauren",
         7: "Gnome", 8: "Troll", 10: "Blood Elf", 11: "Draenei"}
CLASSES = {1: "Warrior", 2: "Paladin", 3: "Hunter", 4: "Rogue", 5: "Priest", 6: "Death Knight",
           7: "Shaman", 8: "Mage", 9: "Warlock", 11: "Druid"}
SKILLS = {164: "Blacksmithing", 165: "Leatherworking", 171: "Alchemy", 182: "Herbalism",
          186: "Mining", 197: "Tailoring", 202: "Engineering", 333: "Enchanting",
          393: "Skinning", 755: "Jewelcrafting", 773: "Inscription"}
SLOTS = ["Head", "Neck", "Shoulders", "Shirt", "Chest", "Waist", "Legs", "Feet", "Wrists",
         "Hands", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2", "Back", "Main hand",
         "Off hand", "Ranged", "Tabard"]


def records(snapshot, name):
    return snapshot["tables"].get(name, {}).get("rows", [])


def normalized(snapshot):
    character = records(snapshot, "characters.characters")[0]
    realm = snapshot["source"]["realm"]
    instances = {row["guid"]: row for row in records(snapshot, "characters.item_instance")}
    templates = {row["entry"]: row for row in records(snapshot, "world.item_template")}
    items = []
    inventory = {row["item"]: row for row in records(snapshot, "characters.character_inventory")}
    mail_ids = {row["item_guid"] for row in records(snapshot, "characters.mail_items")}
    for item_guid in sorted(set(instances) | set(inventory) | mail_ids):
        item = instances.get(item_guid, {})
        entry = item.get("itemEntry")
        template = templates.get(entry, {})
        location = inventory.get(item_guid)
        if location:
            bag, slot = location.get("bag", 0), location.get("slot", -1)
            if bag:
                place = f"Bag {bag}, slot {slot}"
            elif type(slot) is int and 0 <= slot < len(SLOTS):
                place = SLOTS[slot]
            elif type(slot) is int and 19 <= slot <= 22:
                place = f"Bag slot {slot}"
            elif type(slot) is int and 23 <= slot <= 38:
                place = f"Backpack · {slot}"
            elif type(slot) is int and 39 <= slot <= 73:
                place = f"Bank · {slot}"
            else:
                place = f"Slot {slot}"
        else:
            place = "Mail attachment" if item_guid in mail_ids else "Other owned item"
        items.append({"identity": f"{realm}:item-instance:{item_guid}", "guid": item_guid,
                      "entry": entry, "name": template.get("name", f"Unresolved item {entry or item_guid}"),
                      "count": item.get("count", "?"), "location": place,
                      "definition_sha256": hashlib.sha256(json_bytes(template)).hexdigest() if template else None,
                      "description": template.get("description", ""),
                      "script": template.get("ScriptName", "")})
    return {
        "format": "hearthkeeper.character-view/1",
        "identity": f"{realm}:character:{character['guid']}",
        "character": {**character, "race_label": RACES.get(character.get("race"), f"Race {character.get('race')}"),
                      "class_label": CLASSES.get(character.get("class"), f"Class {character.get('class')}")},
        "items": items,
        "skills": [{**row, "name": SKILLS.get(row.get("skill"), f"Skill {row.get('skill')}")}
                   for row in records(snapshot, "characters.character_skills")],
        "module_settings": records(snapshot, "characters.character_settings"),
    }
