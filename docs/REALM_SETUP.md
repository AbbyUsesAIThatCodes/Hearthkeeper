# Preparing the first realm

This preview prepares source identities; it does **not** install a playable realm.
The next PR will turn a proven build/data/configuration combination into a repeatable
launcher. The development container used for this PR lacks Docker/CMake and the
required game data, so no server build or in-game login is claimed.

## Candidate stack

Run `python -m hearthkeeper realm-plan` for the exact commits in the lock file.

| Component | Repository / branch |
| --- | --- |
| Core | mod-playerbots/azerothcore-wotlk / Playerbot |
| Bots | mod-playerbots/mod-playerbots / master |
| Progression | ZhengPeiRu21/mod-individual-progression / master |
| Client experiment | Kelsidavis/WoWee / master, WotLK profile |

Use original **3.3.5a build 12340** game data and a matching conventional client
as the reference. Modern Retail/Classic clients are not interchangeable with it.

For the first server experiment use a dedicated development VM with only the
project and necessary game data. The desktop client can run separately for GPU
performance; do not assume virtualized GPU/Vulkan support will work well for WoWee.
Connecting a desktop client to a VM is a later, deliberate network setup step.

## Fetch sources explicitly

This command makes outbound requests to GitHub and writes new source checkouts:

```sh
python -m hearthkeeper prepare-sources --directory var/sources --include-client
```

It creates a fresh destination, fetches the pinned commits, verifies each HEAD,
and puts Playerbots and Individual Progression into the core's modules folder.
It refuses an existing destination and leaves partial checkouts in place on
failure. Use a new destination to retry after inspecting the failure.

It does not install dependencies, initialize submodules, build software, extract
game assets, run shell scripts from the repositories, or start services. Follow
the matching upstream build guides for those steps, including WoWee's submodules.
Keep the lockfile's exact commit identities when recording the eventual working
stack; record changed pins explicitly when fixing compatibility.

## Build and data plan

1. Follow the [Playerbots installation guide](https://github.com/mod-playerbots/mod-playerbots/wiki/Installation)
   and [AzerothCore installation guide](https://www.azerothcore.org/wiki/installation).
   Confirm the exact guide path in the pinned README if upstream reorganizes it.
2. Build the selected core with its modules. Initialize separate realm databases
   and use distinct local realm credentials. Do not share production databases.
3. Supply client-derived server data for the same build; follow the upstream
   extractor/data instructions. Keep required assets outside Git.
4. Apply Individual Progression's install instructions for that revision. Record
   every optional SQL/client patch selected; back up before changing world data.
5. Build or install the selected WoWee version following its own guide, and extract
   matching data to its loose-file WotLK asset tree. It does not read MPQs at runtime.

**Don't blindly run upstream `docker compose up` on the everyday desktop.** The
candidate core's compose file publishes database/world/auth/SOAP ports and includes
a client-data initialization service. Our later launcher must choose explicit
bindings, credentials, service/data behavior, and mounts first. No compose launcher
is shipped in this preview, and no database port needs public internet exposure.

## Initial configuration decisions to review

These are proposed edits for the future realm's generated configs, not an automatic
patch applied by this preview:

```ini
# worldserver.conf: preserve module settings and allow IP's item-stat changes
EnablePlayerSettings = 1
DBC.EnforceItemAttributes = 0

# individualProgression.conf: retain the journey without restoring reduced quest XP
IndividualProgression.Enable = 1
IndividualProgression.QuestXPFix = 0
```

Do not disable the progression module expecting all its SQL world changes to
vanish. Keep a separate baseline database snapshot before installing it.
Start with a small party and no automatic difficulty multipliers. AH Bot and
AutoBalance are deferred until the basic play loop has been tested.

Optional IP patches must agree between client and server. Recipes are the clearest
test: the UI ingredients must match what the server actually consumes. WoWee needs
the patched files represented in its extracted asset tree too. Do not combine
mutually exclusive IP client patch variants.

## First live acceptance route

- Create an ordinary player character and a separate administrator account.
- Log in with both clients, one at a time; check character creation and relogging.
- Walk the Dun Morogh–Loch Modan–Wetlands route; test collision, camera and transport.
- Accept/finish a quest, learn a skill, craft an item, equip it, bank it, and mail it.
- Log out, capture the character, and inspect all those changes offline.
- Test one healer with four bots, including targeting/mouseover controls.
- Only then progress to disposable-realm restore validation and the 0.1.0 release.

Build success is not gameplay correctness; client login is not full addon
compatibility. Keep clear evidence for each completed gate.
