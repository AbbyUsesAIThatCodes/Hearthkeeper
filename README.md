# Hearthkeeper

**Current preview: 0.1.0a8 — At the War Table**

A desktop home for your personal Azeroth: install and manage a progression realm,
preserve character records, and eventually build your own towns, instances, and regions.
The main application uses native Qt windows. It does not run in a browser.

## Open the desktop app

### Windows — download and play

**[Download Hearthkeeper 0.1.0a8 for Windows](https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/releases/download/v0.1.0a8/Hearthkeeper-0.1.0a8-Windows.zip)**

1. Download the ZIP and choose **Extract All** into a new folder.
2. Open **Hearthkeeper.exe** inside that folder. Keep `_internal` beside it.
3. Choose **Open realm** to use your existing realm folder containing `realm.json`.

No Python installation or visit to Actions is needed. **Download-Windows-Preview.bat**
opens the [release page](https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/releases/tag/v0.1.0a8),
which includes the Windows ZIP, release notes, and checksums. Choose the Windows ZIP;
GitHub's automatic **Source code** downloads do not contain the executable.
Release downloads are preserved separately from expiring Actions artifacts.
Click **Desktop shortcut** in the app to create an icon. This preview is unsigned.

### Source code — use main

**GitHub Desktop / source:** fetch, select **main**, and pull the latest changes,
then run **Start-Hearthkeeper.bat**. This route needs Python **3.11–3.13**
(3.12 recommended). The launcher searches for an installed supported version even
when Windows defaults to Python 3.14 or another unsupported version. If none is
installed, use the packaged app or install a supported Python alongside your current
one; no uninstall or default-version change is required.
The first launch downloads the Qt toolkit into the repository's
own `.venv`; later launches reuse it. Nothing is installed into your system Python.
On Linux, run `sh start-hearthkeeper.sh` with Python's venv support installed.

**Start-Archive-Demo.bat** deliberately opens the earlier browser interface. It is
not the desktop launcher. To check source-launcher selection without installing
anything or opening the app, run `Start-Hearthkeeper.bat --check-python` in a terminal.

You can explore **Archives → Meet Brindle · demo** without Docker, game files,
or an account. This is the same fictional archive, now displayed in native widgets.

## Where to find things

| You want to… | Go here |
| --- | --- |
| Run the current Windows preview | [Download 0.1.0a8](https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/releases/download/v0.1.0a8/Hearthkeeper-0.1.0a8-Windows.zip) |
| Browse or work on the current code | **main**, the default branch |
| See what comes next | [Roadmap](docs/ROADMAP.md) |
| Understand the repository recovery | [Recovery record](docs/RECOVERY.md) |
| Review automated build evidence | [Actions](https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/actions) — for development checks |

Older feature branches preserve development history; you do not need to choose
between them to use Hearthkeeper. Current work continues from **main**, with pull
requests for changes. The a8 Home uses painted stone, wood, parchment, and the full
portal panorama; the other five pages retain their Six Worlds themes.

## Play from your new home screen

Open your existing realm on **Home**, then choose **Wow.exe** from your original
Windows Wrath installation. Hearthkeeper reads the executable's Windows version
metadata and checks for the expected game-data files and selected language folder.
It requires **3.3.5a / build 12340**. The selection is remembered per realm.

If needed, click **Connect to this realm**. The confirmation identifies the
realmlist file; Hearthkeeper saves its original bytes in a dated `.bak` beside
it before writing the local address. Then click **Play**: Hearthkeeper validates
again, starts the realm if needed, waits for healthy services, and launches WoW.
Sign in using your existing realm account. No account password is saved by Play.

**Realm tools** expands the existing install/resume, start/stop, status, settings,
and log controls. The **Companion guide** explains how to bring an alternate
character along. Sources, characters, archives, and backups use the new dark
metal/parchment theme. See [the home screen guide](docs/HOME.md).

Game launching is Windows-only in this preview. Linux retains its existing
realm and archive tools. Luna migration is the next milestone.

## Explore sources and preserve downloads

Open **Sources** without Docker or game files. Expand a provider to see its clients,
cores, modules, patches, or databases. Use the source, era, and search filters.
**Details** explains the target client and what remains unverified.

- **Source page** opens the provider website, including ChromieCraft’s client and mirror choices.
- **Save snapshot** resolves an available GitHub branch and downloads its exact source commit.
- **Import file** copies one completed download into the selected archive location.
- **Saved copies → Verify selected copy** checks the recorded SHA-256 and byte count.

This is a source catalog and preservation proof of concept. It does not add SSH
installation, automatically download/install game clients, or launch alternate
cores. A catalog entry is not a playability certification. Ashamane’s advertised
BFA branch is retained as a historical reference because the branch is unavailable.
See [the source catalog guide](docs/SOURCE_CATALOG.md).

## Install your realm

1. Install and start **Docker Desktop** with Linux containers on Windows.
   Its system prerequisites, including WSL/virtualization and any restart, require
   the normal Docker installer. Hearthkeeper does not silently change them.
2. Open **Home → New realm**. Choose a new realm folder and either an original
   **3.3.5a / build 12340** client folder or matching extracted AzerothCore server data.
3. Choose XP rates, random-bot population, and build workers. Click **Install realm**.
4. After installation, create a private-realm account under **Characters**, then
   choose the client on Home, connect it to the realm, and click **Play**.

Hearthkeeper builds the pinned Playerbot core with Playerbots and Individual
Progression, creates dedicated databases and credentials, imports core/module SQL,
applies progression settings, and prepares the supplied data. The first build and
navigation extraction can take hours. Activity shows the current work; completed
extraction stages are retained. **Install / Resume** retries an unfinished install.

The initial target is one realm on the same computer as the client. Auth/world
ports bind to loopback; the database has no published port. Docker images and the
database volume use the selected local Docker context. See [setup details](docs/REALM_SETUP.md).

## What the desktop manages

| Area | Available in this preview |
| --- | --- |
| Home | Windows client selection, version checks, backed-up connection setup, Play, and expandable realm tools |
| Characters | Create ordinary or GM accounts, list characters, capture a logged-out character |
| Archives | Native viewer, search, checksum validation, module records, coverage, snapshot comparison |
| Backups | Stop gameplay and save SQL databases, configuration, credentials, and source pins |
| Sources | Browse seven providers, preserve exact GitHub source snapshots, import completed downloads, and verify saved copies |
| Workshop | Roadmap for towns, instances, and regions; authoring tools are planned |

The command-line archive tools and optional offline HTML export remain available.
**Start-Archive-Demo.bat** opens the earlier HTML demo.

## Validation and remaining gates

The project has 66 unit tests covering archives, realm boundaries, source
preservation, client safeguards, themes, and verified artwork.
The native acceptance check exercises actual Qt widgets, including archive search,
module/coverage views, literal archived text, and background work. Windows CI builds
and tests the packaged executable.

A separate CI gate compiles the actual pinned core and modules, imports their SQL,
creates a game account, and attempts a build-12340 SRP authentication exchange
with the real authserver. See the PR for the results at its exact commit.

The user has reported a successful first login and brief play in the preceding
local build. **No matching game files are available in the development environment.**
The new Play flow is tested with fictional files and mocked services/processes;
launching the actual WoW executable and broader gameplay still require user
acceptance. Windows CI also checks the version reader against a real executable.
Restoration remains a separate gate.
WoWee compilation/installation and optional client patches are not automated yet.
Runtime Ubuntu/MySQL tags and apt dependencies are not fully locked by digest.

## Read more

- [Desktop and server architecture](docs/DESKTOP.md)
- [Installation and client connection](docs/REALM_SETUP.md)
- [How to test this PR](docs/TESTING.md)
- [Archive capture and limitations](docs/ARCHIVES.md)
- [Access boundaries](docs/ACCESS.md)
- [Roadmap and content workshop](docs/ROADMAP.md)
- [Source catalog and saved copies](docs/SOURCE_CATALOG.md)
- [Upstream source references](docs/SOURCES.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

Work lands in reviewable PRs for local user testing and user merges. The final
0.1.0 milestone still requires verified live login, capture, and disposable-realm
restoration. The archive-only 0.1.0a1 remains the preceding preview.

Real archives, backups, credentials, and game data belong outside this public
repository. Character archives and realm backups are not encrypted. Hearthkeeper
is not affiliated with Blizzard Entertainment or the emulator projects.
