# Installing and managing the first realm

The native desktop now contains an installer and lifecycle controls. This guide
describes the workflow, not a claim that a live world has passed acceptance.
Check PR validation for the actual core/module build and database/authentication results.

## Prerequisites

- Windows with Docker Desktop running Linux containers, or a local Linux Docker
  Engine with Compose v2. Remote Docker/SSH contexts are rejected.
- A working local Docker context. The selected context is recorded with the realm.
- A matching original **3.3.5a build 12340** client folder, or extracted
  AzerothCore `dbc`, `maps`, `vmaps`, `mmaps` and, when available, `Cameras` data.
  Modern Retail and modern Classic files are not substitutes.
- A new folder dedicated to this realm, separate from the selected game folder.
  Roughly 8 GB of memory allocated to Docker and 60 GB of free storage are sensible
  starting allowances, not hard guarantees. Build caches, recovery copies, data,
  and backups grow over time. The app reports Docker memory; it does not measure
  free capacity inside Docker Desktop's virtual disk.

Hearthkeeper does not install Docker/WSL, enable virtualization, change firewall
rules, or download game assets. The Docker setup link opens its official guide.
The installed application itself needs no browser.

## Installation

**New realm** opens the setup form. Choose:

- Name and new destination.
- Client root containing `Data/lichking.MPQ` and `Data/patch-3.MPQ`, or an
  extracted server-data folder. Linux extraction expects conventional filename casing.
- XP multiplier for kills, quests, and exploration.
- Random bots (default zero; your alternate characters can still act as bots).
- Build/extraction workers (default two).

The installer performs these steps in a background worker:

1. Verify the local Linux Docker context and Compose.
2. Build a dedicated image from the pinned core, Playerbots, and Individual Progression.
3. Generate core/module settings and unique local database credentials.
4. Start a new MySQL volume and create the four realm databases plus service identities.
5. Run the compiled database importer for core and module SQL, then register the realm.
6. Copy supplied prepared data, or run the compiled terrain/DBC/camera extractor,
   model extractor, vmap assembler, and mmap generator against the read-only client mount.
7. Check required data files/headers and mark the installation complete.

Zero random bots avoids the upstream default population of hundreds. Increasing the
setting allows a small population without automatically adding AH Bot or AutoBalance.
Individual Progression enables player settings, disables enforced DBC item attributes,
and retains normal quest XP instead of its optional historical quest-XP reduction.
Optional progression SQL/DBC/client patches are deliberately not selected automatically.

## Progress, retry, and shutdown

Keep the application open while an operation runs; it can be minimized.
**Stop after current step** waits for the current command to finish. It does not
kill a compiler, extractor, or SQL import midway. Closing the UI does not stop a
running realm after setup has completed.

On failure, read Activity and use **Install / Resume** on the existing realm.
Compilation reuses Docker's available layer cache; the SQL updater tracks applied
updates. Completed extraction stages have checkpoints. An unfinished model/vmap/mmap
stage starts clean and retains its prior output in a timestamped `*-incomplete-*`
directory. This uses additional disk space. A power failure during SQL import can
still require recovery; there is no claim of transactional rollback of all upstream SQL.

**Start realm** waits for auth/world port health checks. **Stop realm** gives those
processes time to shut down before stopping the database. No volume deletion is
performed. A lock prevents two Hearthkeeper processes from changing the same realm
at once. The desktop currently manages one selected realm at a time, with fixed
local ports, so two realms cannot run simultaneously on this host.

## Accounts and connection

Create an ordinary account for playing; optionally create a separate GM account.
These are local realm accounts, unrelated to a Blizzard account. Passwords follow
the original client's 16-character ASCII limit and are sent over stdin to the
local management container, not placed in command-line arguments or saved in logs.
The auth database stores SRP salt/verifier records.

For a conventional original 3.3.5a client, edit its language-specific
`Data/<locale>/realmlist.wtf` to contain `set realmlist 127.0.0.1`, preserving
a copy of its previous contents. Launch the game's executable directly. The app
does not rewrite client files or install WoWee in this preview.

Only `127.0.0.1:3724` and `127.0.0.1:8085` are published. The database and
administration endpoints are not published. A desktop manager inside a dedicated
VM therefore needs its client inside that VM for this initial local-only mode;
connecting from the host or a remote machine needs a future deliberate network
configuration feature.

## Backups, character capture, and settings

**Stop realm & back up** stops auth/world, starts the database if necessary, and
streams a compressed SQL dump of auth, characters, world, and playerbots. The
backup includes configuration, local credentials, source pins, and file hashes.
Successful output is renamed from `.incomplete`; auth and world remain stopped.
The backup excludes game assets and the Docker image. Keep those separately.
Automatic restoration and a verified recovery drill are still future work.

Account creation, character listing, and capture can start the database while
leaving gameplay stopped. Select a logged-out character to capture an archive;
the native archive viewer opens the result. The capture account has SELECT-only
grants to character/world tables, not auth. Use the Coverage view.

Stop the realm before editing XP/bot settings. Managed settings are regenerated
on save; other configuration fields are retained. Update/removal/migration
automation is not present. A different source lock requires its matching version
of Hearthkeeper rather than silently updating an existing realm.

## First in-game acceptance

Verify creation/relog, the Dun Morogh–Loch Modan–Wetlands walk, collision and travel,
quests, crafting, equipment, bank/mail, and a healer with four companions. Then
capture the logged-out character and compare what the archive recorded. Repeat
with WoWee once its separate client setup is ready. Finally implement and test
restoration in a disposable realm before the final 0.1.0 release.
