# Hearthkeeper roadmap

The aim is a personal Azeroth that stays enjoyable and can be preserved. Releases
pair semantic versions with codenames. We work through PRs, local user testing,
feedback, and user merges.

## 0.1.0a1 — First Campfire preview (this PR)

- Fictional, offline character archive and viewer.
- AzerothCore adapter that explicitly includes `character_settings`.
- Raw records with source provenance, typed values, and table coverage.
- Checksum verification and snapshot comparisons.
- Candidate core/module/client source pins and local source-preparation command.

This is a development preview; restoration and a playable realm are not complete.

## 0.1.0 — First Campfire (release gate)

1. Build the pinned core/modules in the dedicated development environment.
2. Record the database revision, module revisions, server data, client data hashes,
   build dependencies, and configuration. Fix/pin any compatibility changes.
3. Connect using the matching conventional 3.3.5a client and WoWee. Test the
   Dun Morogh–Loch Modan–Wetlands walk, quests, crafting, bank/mail, travel, and relog.
4. Integration-test MySQL capture against that database, including progression
   settings and one deliberately modified item definition.
5. Implement restoration to a **disposable same-core realm** with collision-safe
   GUID allocation, dependency checks, a preflight report, and rollback/recovery.
6. Verify the restored character in game, not only by comparing SQL rows.

Keep conventional private realm backups in parallel. A partial character archive
does not replace database/configuration/content backups.

## Party and progression

Test one healer plus a tank and three damage bots. Tune controls and specific
encounters from play feedback. Add population, AH Bot, and AutoBalance only after
the small party works. Review XP and profession friction; don't automatically
restore chores that the player wanted to escape.

## Portable character records

Add DBC-backed recipe/spell definitions, account-wide records where relevant,
custom-module adapters, artifact signatures if needed, and transparent transfer
policies. Use stable source namespaces plus definition fingerprints. IDs are
local references, never a universal identity guarantee.

Support a second AzerothCore environment before a different core. Add CMaNGOS
adapters after a verified same-core round trip. Preserve unsupported records
without pretending they can already be imported. Never silently substitute an
unrelated custom item merely because its numeric entry matches.

## The content workshop — planned, not implemented

The long-term workshop should support the requested **towns, instances, and
regions**. It has three linked layers:

| Layer | Authoring work | Required output |
| --- | --- | --- |
| Town | Buildings/props, NPCs, schedules, vendors, dialogue, quests, spawns | Versioned world records, scripts, object-placement data, validation |
| Instance | Encounter phases, doors, triggers, loot, resets, objectives | Map/instance definitions, scripts, client data when needed, playtests |
| Region | Terrain, roads, water, zones, music, travel links, map presentation | Client terrain/assets/DBC changes plus matching server maps, collision, navigation and world data |

Start with a small original settlement on existing terrain. Then build one
instance using existing assets. New terrain comes after that pipeline works.
WoWee's editor is an exploratory candidate; evaluate its formats/export behavior
before adopting it as the workshop's permanent format.

Use human-readable content packs with `namespace`, `version`, target core/build,
dependencies, stable authored IDs, allocated server IDs, asset manifests/checksums,
license/provenance fields, schema version, and explicit install/remove migrations.
Separate authored source from generated SQL/client outputs. Dependencies belong
in a graph: an item may depend on a spell, script, display model, and texture.

Preview changes before installing them. Validate references and ID collisions,
then test in a disposable realm. Region/instance removal must account for saved
characters, homebinds, quests, and items that still refer to that content. Never
delete a content pack just because its visible buildings were removed.

The archive format should record content-pack identity so a future character can
explain which version of your own town, instance, or region it came from. Arbitrary
script behavior is preserved as a dependency; automatic cross-core translation
is not a promised capability.
