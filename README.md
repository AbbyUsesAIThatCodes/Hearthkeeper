# Hearthkeeper

**0.1.0a2 — First Campfire · native desktop development preview**

A desktop home for your personal Azeroth: install and manage a progression realm,
preserve character records, and eventually build your own towns, instances, and regions.
The main application uses native Qt windows. It does not run in a browser.

## Open the desktop app

**Packaged Windows app (no Python):** run **Download-Windows-Preview.bat**, or open
[Native desktop builds](https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/actions/workflows/desktop.yml?query=branch%3Afeature%2Fdesktop-realm-manager).
Sign into GitHub **in your browser**; GitHub Desktop's sign-in is separate.
Open a successful run for `feature/desktop-realm-manager`, scroll to **Artifacts**,
and select **Hearthkeeper-0.1.0a2-Windows**. Extract the entire ZIP, then open
**Hearthkeeper.exe**. Keep the accompanying `_internal` folder beside it.
No Python installation is needed. Click **Desktop shortcut** once to create an icon.
This development build is unsigned; a signed distribution is a later packaging step.
Artifacts expire after 30 days. A direct artifact link can show a 404 when you are
signed out, lack access, or the artifact has expired; use the build list above.

**GitHub Desktop / source:** fetch and select `feature/desktop-realm-manager`,
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

## Install your realm

1. Install and start **Docker Desktop** with Linux containers on Windows.
   Its system prerequisites, including WSL/virtualization and any restart, require
   the normal Docker installer. Hearthkeeper does not silently change them.
2. Open **Realm → New realm**. Choose a new realm folder and either an original
   **3.3.5a / build 12340** client folder or matching extracted AzerothCore server data.
3. Choose XP rates, random-bot population, and build workers. Click **Install realm**.
4. After installation, create a private-realm account under **Characters**, then
   click **Start realm**. Use the matching client with realmlist `127.0.0.1`.

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
| Realm | Install/resume, start, stop, status, logs, XP and random-bot settings |
| Characters | Create ordinary or GM accounts, list characters, capture a logged-out character |
| Archives | Native viewer, search, checksum validation, module records, coverage, snapshot comparison |
| Backups | Stop gameplay and save SQL databases, configuration, credentials, and source pins |
| Workshop | Roadmap for towns, instances, and regions; authoring tools are planned |

The command-line archive tools and optional offline HTML export remain available.
**Start-Archive-Demo.bat** opens the earlier HTML demo.

## Validation and remaining gates

The project has 27 unit tests covering archive behavior and realm boundaries.
The native acceptance check exercises actual Qt widgets, including archive search,
module/coverage views, literal archived text, and background work. Windows CI builds
and tests the packaged executable.

A separate CI gate compiles the actual pinned core and modules, imports their SQL,
creates a game account, and attempts a build-12340 SRP authentication exchange
with the real authserver. See the PR for the results at its exact commit.

**No matching game files are available in the development environment.** Extraction,
world startup, in-game login/play, and restoration still require live acceptance
testing. Authserver authentication alone does not establish a playable world.
WoWee compilation/installation and optional client patches are not automated yet.
Runtime Ubuntu/MySQL tags and apt dependencies are not fully locked by digest.

## Read more

- [Desktop and server architecture](docs/DESKTOP.md)
- [Installation and client connection](docs/REALM_SETUP.md)
- [How to test this PR](docs/TESTING.md)
- [Archive capture and limitations](docs/ARCHIVES.md)
- [Access boundaries](docs/ACCESS.md)
- [Roadmap and content workshop](docs/ROADMAP.md)
- [Upstream source references](docs/SOURCES.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

Work lands in reviewable PRs for local user testing and user merges. The final
0.1.0 milestone still requires verified live login, capture, and disposable-realm
restoration. The archive-only 0.1.0a1 remains the preceding preview.

Real archives, backups, credentials, and game data belong outside this public
repository. Character archives and realm backups are not encrypted. Hearthkeeper
is not affiliated with Blizzard Entertainment or the emulator projects.
