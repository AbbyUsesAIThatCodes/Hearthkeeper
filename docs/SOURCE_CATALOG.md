# Source catalog — First Campfire 0.1.0a3

Hearthkeeper now has a small source catalog and acquisition proof of concept. A
provider groups the offerings it actually publishes: clients, patches, emulator
source, modules, or world databases. Selecting a source never changes a realm.

## Use the desktop

1. Open **Sources**. The catalog is bundled and browsable offline.
2. Expand a provider or filter by source, era, or text. **Details** shows the
   client family, version/build, source review date, and limitations.
3. Choose **Archive location** if the default app-data folder is unsuitable.
   Large client downloads need space for an additional complete copy.
4. For a GitHub offering, **Save snapshot** downloads the current source branch
   after resolving its exact commit. It creates a new saved copy each time.
5. For client downloads or database releases, **Source page** opens the provider's
   site. Download the desired file there, then **Import file** to preserve it.
   ChromieCraft's page contains its direct link, mirrors, torrent/magnet options,
   and optional HD patches. Those external download endpoints are not scraped or
   silently followed by Hearthkeeper.
6. Under **Saved copies**, select a copy and **Verify selected copy** to detect
   changed bytes, or **Open selected folder** to inspect its files and manifest.

Imports do not inspect or certify a client build. Their catalog association is
user-supplied. A file can have a correct recorded checksum and still be the wrong
client. This preview does not unpack files, apply patches, rewrite a realmlist,
start a downloaded executable, import SQL, or install a catalog-selected core.

## Initial coverage

Provider pages and advertised targets were reviewed on **2026-09-13**. Live Git
branch checks confirmed 17 available source branches. A check records availability
at that time, not future reliability or a gameplay test.

| Provider | Catalog offerings | Acquisition in this preview |
| --- | --- | --- |
| [ChromieCraft](https://chromiecraft.com/en/downloads/) | Original Wrath 3.3.5a client and optional HD patches | Provider page, then explicit file import |
| [AzerothCore](https://github.com/azerothcore/azerothcore-wotlk) ecosystem | Standard Wrath core, [Playerbot flavor](https://github.com/mod-playerbots/azerothcore-wotlk), [Playerbots](https://github.com/mod-playerbots/mod-playerbots), [Individual Progression](https://github.com/ZhengPeiRu21/mod-individual-progression) | Exact-commit source snapshots |
| [CMaNGOS](https://github.com/cmangos) | Original Vanilla, Burning Crusade, and Wrath cores; matching world database repositories | Separate source snapshots for each core/database |
| [Cataclysm Preservation](https://github.com/The-Cataclysm-Preservation-Project/TrinityCore) | Original Cataclysm 4.3.4 / 15595 core and database release page | Source snapshot; explicit database-file import |
| [Project SkyFire](https://github.com/ProjectSkyfire/SkyFire_548) | Original Mists 5.4.8 / 18414 core and database release page | Source snapshot; explicit database-file import |
| [TrinityCore](https://github.com/TrinityCore/TrinityCore) | Original Wrath, Cataclysm Classic, and moving modern-client branches | Source snapshots; exact modern client target must be checked at the chosen revision |
| [AshamaneProject](https://github.com/AshamaneProject/AshamaneCore) | Historical Legion and Shadowlands branches; advertised BFA target as a historical reference | Legion/Shadowlands source snapshots; BFA source page only |

Ashamane's description advertises `bfa` / 8.3.7.35284, but its live branch list
contained only `ducktape`, `legion`, and `master` during review. The BFA offering
therefore has **no automated snapshot button**. A replacement repository or known
historical commit requires a separate review; an advertised target is not enough.

This is not full expansion coverage. Warlords, specific Dragonflight and The War
Within snapshots, and additional client providers remain gaps. A current modern
protocol branch does not imply that earlier expansion content is complete or that
it works with all earlier clients. Original Cataclysm and Cataclysm Classic are
separate families even though they share an expansion name.

A public private-server operator may offer a client but keep its server changes,
content database, and player data private. The catalog cannot reconstruct those
unpublished components. World database source contains world content; it does not
contain a public server's private characters or account records.

## What a saved copy contains

Each new directory contains `manifest.json` plus the preserved payload. The
manifest records the offering metadata as it was when saved, UTC acquisition time,
byte count, observed SHA-256, and acquisition route. GitHub snapshots also record
the repository, requested branch, resolved commit, and download URL. Imported files
record the original filename and the claimed provider page without recording the
user's full source path.

A source snapshot contains tracked source at one revision, not full Git history,
submodule contents, external/LFS assets, or all build dependencies. Some world
databases and patches are separate releases. Those limitations remain in the
manifest. A checksum detects changes to the saved bytes; it does not authenticate
the publisher or prove build success, compatibility, or content completeness.

Interrupted acquisitions have no completed manifest and retain `INCOMPLETE.txt`.
Retries create a new directory and do not replace an earlier copy. Automatic resume
and partial-copy cleanup are future work. Transfers stream in bounded chunks;
source downloads have a 1 GiB preview cap, a socket timeout, and restricted GitHub
redirect hosts. Completed file imports check available disk space and reject
common unfinished browser-download suffixes. Source operations honor the shared
stop request between chunks. Nothing starts on app launch.

The source archive is local to the computer running Hearthkeeper. Luna storage,
SSH transport, automatic client acquisition, and installation profiles will build
on this acquisition layer. The existing Realm installer still uses its original
pinned Playerbots/Individual Progression stack and local Docker context.

## Command-line equivalents

```sh
python -m hearthkeeper source-catalog --provider chromiecraft
python -m hearthkeeper source-catalog --search 18414
python -m hearthkeeper source-fetch individual-progression --directory /path/to/source-archive
python -m hearthkeeper source-import chromiecraft-client /path/to/download.zip --directory /path/to/source-archive
python -m hearthkeeper source-verify /path/to/source-archive/one-saved-copy
```

## Extending the catalog

`hearthkeeper/data/sources.catalog.json` is versioned data, not executable plugin
code. Each offering identifies its provider, type, era, client family/version/build,
reviewed source page, acquisition method, and installation/gameplay status. A
GitHub offering also gives a repository and reference. Add reviewed providers and
offerings there; the tree and filters populate automatically. Unknown acquisition
methods are rejected rather than interpreted as commands.

New hosting providers require an acquisition adapter in `hearthkeeper/sources.py`
plus tests for redirects, incomplete transfers, preservation, and provenance. New
realm installers are a different layer: each must establish core/database/module/
client agreement and a tested recovery workflow before it can deploy an offering.

## Validation for this preview

- 36 local unit tests passed, including nine catalog/preservation/failure tests.
- Native Qt acceptance passed at regular and 980 × 700 sizes, including filters,
  disabled acquisition controls, file import, saved-copy selection, and verification.
- A live download of Individual Progression resolved commit
  `977e2005bacf97f35e506eb27b8af6b2ea1136af`, saved 36,371,175 bytes, and passed
  checksum verification. The gzip tar was inspected without extraction and
  contained 266 entries including the upstream README.
- Windows source and packaged-executable CI is required on the PR; local Linux
  checks do not establish Windows packaging success. This change does not
  establish a playable realm or live Luna connection.
