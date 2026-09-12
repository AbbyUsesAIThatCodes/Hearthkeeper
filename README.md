# Hearthkeeper

**0.1.0a1 — First Campfire · development preview**

A local archive desk for your characters, a reproducible foundation for a personal
WoW realm, and eventually a workshop for your own towns, instances, and regions.

This first PR delivers a working fictional demo, a read-only character exporter,
an offline archive viewer, checksum verification, snapshot comparison, and pinned
candidate server/client source checkouts. **It does not yet deliver a playable
realm, a complete backup, character restoration, or a world editor.**

## Try it on Windows

1. Install **Python 3.11 or newer** from [python.org](https://www.python.org/downloads/windows/)
   if needed. GitHub Desktop supplies the repository workflow; the demo itself
   only needs Python. No administrator privileges are needed to run the demo.
2. In GitHub Desktop, fetch and select the PR branch
   `feature/first-campfire-preview`.
3. Double-click **Start-Hearthkeeper.bat** in the repository folder.
4. The offline character record opens in your browser. Try **Equipment & bags**,
   search for `Lantern`, then inspect **Module data** and **Coverage**.

The sample character Brindle, Copperleaf items, quests, and module payloads are
fictional. No Blizzard assets, server connection, account sign-in, folder scanning,
or extra Python package is required. Every run creates a new folder under
`var/demo/`; existing files are never replaced. Keep the console open if an error
appears. If the browser does not open, open the printed `brindle.html` path manually.

On Linux/macOS: `sh start-hearthkeeper.sh`, or on any supported system:

```sh
python -m hearthkeeper demo
```

Use `python3` instead of `python` where that is your Python command. Add `--open`
to open the generated HTML automatically. The HTML can be opened directly with
no local web server and no internet connection.

## Commands

```sh
python -m hearthkeeper doctor
python -m hearthkeeper realm-plan
python -m hearthkeeper verify path/to/brindle.hearth
python -m hearthkeeper inspect path/to/brindle.hearth
python -m hearthkeeper render path/to/brindle.hearth --output var/record.html
python -m hearthkeeper diff path/to/earlier.hearth path/to/later.hearth
python -m unittest discover -s tests -v
```

`inspect` prints the derived character model as JSON. `diff` identifies changed
tables, including changed values when row counts stay equal; it does not yet
produce an item-by-item narrative. Comparisons require the same realm namespace
and character GUID. A checksum proves consistency with the embedded manifest,
not the author's identity or that every relevant record was captured.

## Working with a realm

- [Realm preparation and the first login test](docs/REALM_SETUP.md)
- [Read-only SQL capture, coverage, and limitations](docs/ARCHIVES.md)
- [Access boundaries and private data](docs/ACCESS.md)
- [Roadmap, including the content workshop](docs/ROADMAP.md)
- [PR testing instructions](docs/TESTING.md)
- [Source references and pin rationale](docs/SOURCES.md)

The candidate core is the **Playerbot branch** of
`mod-playerbots/azerothcore-wotlk`, with Playerbots and Individual Progression,
using original **3.3.5a / build 12340** and WoWee's `wotlk` profile. Source revisions
are pinned in `hearthkeeper/data/realm.lock.json`. These are recorded source
identities, **not a claim that the combined stack has passed build or gameplay tests**.

## Current validation

The standard-library tests exercise relational capture, cross-character isolation,
ownerless mail attachments, raw module payload retention, read-only SQLite access,
damaged archives, HTML escaping, non-overwrite behavior, and the offline demo.
CI runs these checks on Windows and Linux with Python 3.11 and 3.13.

The MySQL adapter and actual realm/client still need live integration testing.
SQLite is a deliberately small test fixture, not the server's production database
format. See the PR for the checks that actually ran in its environment.

## Development agreement

Work lands in reviewable PRs. You test the branch locally, report observations,
and merge when satisfied. Follow-up issues track defects and the next milestone.
The final **0.1.0** label is reserved for verified live login, capture, and
restoration; this preview is **0.1.0a1**.

This repository is public. Keep real character archives, SQL backups, credentials,
and game data out of commits. Generated files live under ignored `var/`. An ignore
rule is a convenience, not a confidentiality boundary. Hearthkeeper is not
affiliated with Blizzard Entertainment or the emulator projects.
