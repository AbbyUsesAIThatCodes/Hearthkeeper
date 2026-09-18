# Hearthkeeper roadmap

The aim is a personal Azeroth that stays enjoyable and can be preserved. Releases
pair semantic versions with codenames. We work through PRs, local user testing,
feedback, and user merges.

## Agreed next milestones

The user has reported successfully starting the local realm, creating an account
and a gnome, entering the world, and fighting a wolf with the 0.1.0a3 setup.
This establishes user-reported first-login success. Companion play, broader game
systems, backup restoration, and remote deployment still need acceptance.

Keep the following five milestones in order. The current preview is **0.1.0a8 —
At the War Table**, preserved on **main** with a direct Windows release download.
The a5 client/Play safeguards, a6 Six Worlds presentation, and a7/a8 painted Home
are implemented. See [recovery and evidence](RECOVERY.md), [Home](HOME.md), and
[Home materials](HOME_MATERIALS.md). Live Windows/WoW acceptance remains to be
recorded; Luna migration and the later capabilities remain planned.

### Next reviewable work

The **0.1.0a9 — The Living Hearth** presentation pass implements compact Home,
separate tools/activity windows, optional motion, and scaling acceptance checks.
See [its guide](LIVING_HEARTH.md). PR/Windows user acceptance remains the gate;
this does not count as Luna migration or live gameplay verification.

1. **Accept the recovered a8 preview.** Open the existing realm, check all six
   pages and small-window readability, then verify Play with the realm initially
   stopped and already running. Log into the existing gnome. Record any visual
   changes still wanted before calling the first milestone complete.
2. **Prepare Luna migration.** Record the target host and access method, inventory
   the existing realm's exact versions, and implement a complete backup/restore
   rehearsal in a disposable destination before changing the working local realm.
3. **Prove continuity on Luna.** Add remote management and a client connection
   path, restore the complete realm, and verify the existing character in game.
   Keep the local realm until that acceptance succeeds.

Acquisition automation, additional eras, extensions, and the content workshop
follow in the agreed order. The repository repair does not count as migration or
live gameplay acceptance.

| Order | Milestone | Reviewable outcome |
| --- | --- | --- |
| 1 | Warcraft styling and everyday usability | A working native Hearthkeeper home screen with realm/era/host identity, honest readiness indicators, game-installation selection, and Play that starts the required services and launches the matching client. Extend the reviewed design to other screens. |
| 2 | Migrate the existing realm to Luna | Hearthkeeper and the game run on Windows; Luna hosts the realm services, database, and server data. Implement remote management, restore a complete backup, and log into the existing gnome on Luna before retiring the local server. Update setup and operating instructions. |
| 3 | Automate acquisition and installation | Support direct downloads and qBittorrent integration, track completion, verify completed files and client builds, then prepare and launch installations. Preserve exact versions and source information. |
| 4 | Test additional eras and realm profiles | Introduce one reproducible server/client/module combination at a time, with recorded compatibility and in-game checks. Distinguish discovered, downloaded, installed, and play-tested profiles. |
| 5 | Begin the integrated content workshop | Start with a searchable world browser and a small editable content pack: an NPC, dialogue, vendor inventory, and a short quest. Install and test the pack before expanding to settlements, instances, and terrain. |

### First visual milestone

Target the classic/Wrath interface vocabulary: carved stone, dark metal,
parchment, warm gold type, substantial red buttons, and framed ability-style
icons. Preserve readable text, clear focus and selection states, and comfortable
spacing. Keep the native Qt foundation and existing separation of UI and realm
operations.

The opening screen should answer: which world, which era, which host, whether
it is ready, and how to play. Provide clear access to characters, companions,
installations, and backups. Surface the reason and next action when Play is
unavailable. An operation's progress must describe real work.

A prior conversation mentioned an 0.1.0a4 “Hearth & Parchment” draft. The repository
recovery found no original unpublished a4/a6 implementation in either local copy
or the fetched history. Preserve that uncertainty; a5–a8 are the available,
verified implementations rather than a claim to have recovered those drafts.

### Downloads and extensions

Use qBittorrent's documented API as the initial torrent integration: submit a
selected torrent or magnet, track the transfer and destination, and import
completed payloads into the installation workflow. Distinguish transfer
completion, file verification, and actual game compatibility. Evaluate an
embedded torrent engine later if needed.

The extension browser below is an additional agreed capability. Reserve its
navigation and profile metadata during the first milestone; implement browsing
and installation alongside the later installation/profile work.

## 0.1.0a1 — First Campfire archive preview

- Fictional, offline character archive and viewer.
- AzerothCore adapter that explicitly includes `character_settings`.
- Raw records with source provenance, typed values, and table coverage.
- Checksum verification and snapshot comparisons.
- Candidate core/module/client source pins and local source-preparation command.

This is a development preview; restoration and a playable realm are not complete.

## 0.1.0a2 — First Campfire desktop preview

- Native Qt desktop application, Windows executable packaging, and a desktop icon.
- Managed installation from the selected source pins and user-supplied game files.
- Dedicated database initialization, progression/bot configuration, and data extraction.
- Start, stop, status, logs, ordinary/GM account creation, and rate/population settings.
- Native archives, managed character capture, and SQL/configuration backups.
- Automated build/SQL/authentication gate, plus native packaged-app checks.

The build gate has no game assets. Completing extraction, world startup, in-game
play, WoWee setup, and restoration still requires subsequent acceptance work.

## 0.1.0a3 — First Campfire source catalog preview

- Seven providers and 22 catalog offerings, with original/Classic client distinctions.
- GitHub source snapshots with exact commit identity, completed-file imports, and verification.
- Native source filters and saved-copy browsing; historical/unavailable source labeling.
- Next: the agreed Warcraft interface/usability milestone, followed by Luna migration.

See [the catalog guide](SOURCE_CATALOG.md) for coverage and acquisition limits.

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

## Extension browser — planned

Add an integrated browser in Hearthkeeper for discovering, comparing, selecting,
installing, and trying extensions. Explain the two categories in the interface:

| Type | Runs where | Example and installation implications |
| --- | --- | --- |
| Server module | Inside the realm server | Playerbots and gameplay modules. Compatibility depends on the server core and revision; installation can require compilation, database updates, and a realm restart. |
| In-game addon | Inside the selected WoW client | Companion controls such as MultiBot and other interface tools. Compatibility depends on the client build and addon API; files belong to that installation's addon folder and activation may require a UI reload or relog. |

For each entry, show its purpose, screenshots when available, upstream source,
version, supported core/client builds, dependencies, known conflicts, installed
state, and the evidence behind compatibility claims. Filter by realm profile,
era/build, category, and installed status. “Listed” must not imply “tested.”

Use the existing source catalog as the foundation for extension metadata and
saved versions. Show the target realm or game installation and the concrete
actions required before applying a change. Account for rebuilding, restarting,
and database migration where relevant. Track installed versions per profile and
offer recovery appropriate to that extension; do not promise that removing a
module's files reverses its database changes.

Start with a short curated selection and test one change at a time in a
disposable copy of the realm. An early companion-control experiment should try
MultiBot with the current Wrath/Playerbots combination and record setup,
reliability, and usability findings before selecting a default. The user's
experience with a previous Vanilla control addon was clunky and unreliable;
comfortable everyday control is an explicit acceptance criterion.

References:
- [Playerbots commands and MultiBot context](https://github.com/mod-playerbots/mod-playerbots/wiki/Playerbot-Commands)
- [qBittorrent WebUI API](https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-%28qBittorrent-5.0%29)

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
