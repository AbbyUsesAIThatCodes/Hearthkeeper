"""Small, fictional relational fixture. Contains no Blizzard assets or user data."""

import sqlite3
from .archive import write_new


def create_fixture(path):
    write_new(path, b"")
    connection = sqlite3.connect(path)
    try:
        # This SQL is authored source, never supplied by an archive or user upload.
        connection.executescript("""
            CREATE TABLE characters (guid INTEGER PRIMARY KEY, account INTEGER, name TEXT,
                race INTEGER, class INTEGER, level INTEGER, money INTEGER, online INTEGER,
                map INTEGER, zone INTEGER, position_x REAL, position_y REAL, position_z REAL,
                totaltime INTEGER, custom_story_note TEXT);
            CREATE TABLE character_inventory (guid INTEGER, bag INTEGER, slot INTEGER,
                item INTEGER PRIMARY KEY);
            CREATE TABLE item_instance (guid INTEGER PRIMARY KEY, itemEntry INTEGER,
                owner_guid INTEGER, count INTEGER, durability INTEGER, enchantments TEXT);
            CREATE TABLE item_template (entry INTEGER PRIMARY KEY, name TEXT, Quality INTEGER,
                InventoryType INTEGER, description TEXT, ScriptName TEXT);
            CREATE TABLE character_skills (guid INTEGER, skill INTEGER, value INTEGER, max INTEGER);
            CREATE TABLE character_spell (guid INTEGER, spell INTEGER, active INTEGER, disabled INTEGER);
            CREATE TABLE character_queststatus (guid INTEGER, quest INTEGER, status INTEGER,
                explored INTEGER, timer INTEGER);
            CREATE TABLE character_queststatus_rewarded (guid INTEGER, quest INTEGER, active INTEGER);
            CREATE TABLE quest_template (ID INTEGER PRIMARY KEY, LogTitle TEXT, LogDescription TEXT);
            CREATE TABLE character_reputation (guid INTEGER, faction INTEGER, standing INTEGER, flags INTEGER);
            CREATE TABLE character_settings (guid INTEGER, source TEXT, data TEXT,
                PRIMARY KEY (guid, source));
            CREATE TABLE character_pet (id INTEGER PRIMARY KEY, owner INTEGER, name TEXT, level INTEGER);
            CREATE TABLE pet_spell (guid INTEGER, spell INTEGER, active INTEGER);
            CREATE TABLE pet_aura (guid INTEGER, spell INTEGER, effect_mask INTEGER);
            CREATE TABLE pet_spell_cooldown (guid INTEGER, spell INTEGER, time INTEGER);
            CREATE TABLE mail (id INTEGER PRIMARY KEY, receiver INTEGER, sender INTEGER, subject TEXT, body TEXT);
            CREATE TABLE mail_items (mail_id INTEGER, item_guid INTEGER, receiver INTEGER);
            CREATE TABLE custom_town_citizenship (character_guid INTEGER, town TEXT);
            CREATE TABLE account_private_fixture (id INTEGER, private_note TEXT);
        """)
        connection.executemany("INSERT INTO characters VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
            (7, 1, "Brindle", 3, 5, 24, 124506, 0, 0, 38, -5200.25, -2900.5, 300.0, 18420,
             "Fictional explorer. First camp: Copperleaf Crossing."),
            (8, 2, "OtherCharacter", 1, 1, 60, 999999, 0, 0, 0, 0, 0, 0, 10, "Not part of this export"),
        ])
        connection.executemany("INSERT INTO item_template VALUES (?,?,?,?,?,?)", [
            (900001, "Copperleaf Lantern", 2, 23, "A light for roads not yet mapped.", "hk_lantern_demo"),
            (900002, "Wayfarer's Wool Robe", 2, 20, "Mended after a long walk through the foothills.", ""),
            (900003, "Tinbound Field Journal", 1, 0, "Blank pages, waiting for a new region.", ""),
            (900004, "Bundle of River Reeds", 1, 0, "Fictional crafting material.", ""),
            (900005, "Copperleaf Satchel", 1, 18, "The first bag Brindle made.", ""),
        ])
        connection.executemany("INSERT INTO item_instance VALUES (?,?,?,?,?,?)", [
            (101, 900001, 7, 1, 35, ""), (102, 900002, 7, 1, 55, ""),
            (103, 900003, 7, 1, 0, ""), (104, 900004, 7, 12, 0, ""),
            (105, 900005, 7, 1, 0, ""),
            # An addressed attachment with no owner yet must still be captured.
            (106, 900004, 0, 3, 0, ""),
            (201, 900001, 8, 1, 35, "not-the-selected-character"),
        ])
        connection.executemany("INSERT INTO character_inventory VALUES (?,?,?,?)", [
            (7, 0, 16, 101), (7, 0, 4, 102), (7, 0, 23, 103),
            (7, 0, 39, 104), (7, 0, 19, 105), (8, 0, 16, 201),
        ])
        connection.executemany("INSERT INTO character_skills VALUES (?,?,?,?)", [(7, 202, 115, 150), (7, 197, 100, 150)])
        connection.executemany("INSERT INTO character_spell VALUES (?,?,?,?)", [(7, 910001, 1, 0), (7, 910002, 1, 0)])
        connection.executemany("INSERT INTO quest_template VALUES (?,?,?)", [
            (920001, "A Light Across the Water", "Bring the lantern to the crossing."),
            (920002, "A Place to Begin", "Find a quiet place to make camp."),
        ])
        connection.execute("INSERT INTO character_queststatus VALUES (7,920001,1,0,0)")
        connection.execute("INSERT INTO character_queststatus_rewarded VALUES (7,920002,1)")
        connection.execute("INSERT INTO character_reputation VALUES (7,930001,450,0)")
        connection.executemany("INSERT INTO character_settings VALUES (?,?,?)", [
            (7, "hearthkeeper.demo.progression", '{"completed_tier":0,"fictional":true}'),
            (7, "hearthkeeper.demo.journal", '{"first_camp":"Copperleaf Crossing"}'),
            (8, "private-other-character", "must not be exported"),
        ])
        connection.execute("INSERT INTO character_pet VALUES (301,7,'Thimble',24)")
        connection.execute("INSERT INTO pet_spell VALUES (301,910010,1)")
        connection.execute("INSERT INTO character_pet VALUES (302,8,'OtherPet',60)")
        connection.execute("INSERT INTO pet_spell VALUES (302,910099,1)")
        connection.execute("INSERT INTO mail VALUES (401,7,8,'Supplies for the road','Fictional mail for the sample explorer.')")
        connection.execute("INSERT INTO mail VALUES (402,8,7,'Private fixture mail','must not be exported')")
        connection.execute("INSERT INTO mail_items VALUES (401,106,7)")
        connection.execute("INSERT INTO custom_town_citizenship VALUES (7,'Copperleaf Crossing')")
        connection.execute("INSERT INTO account_private_fixture VALUES (1,'PRIVATE_FIXTURE_SENTINEL')")
        connection.commit()
    finally:
        connection.close()
    return path
