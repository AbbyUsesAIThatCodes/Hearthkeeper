# Changelog

## 0.1.0a3 — First Campfire source catalog preview — 2026-09-13

- Added a native Sources page with seven providers and 22 client, server, module,
  patch, database, and historical-reference offerings, plus provider/era/search filters.
- Added source snapshots resolved to exact GitHub commits, explicit downloaded-file
  imports, saved-copy browsing, and SHA-256 preservation checks.
- Recorded acquisition provenance and incomplete-copy state without executing,
  extracting, or installing the saved content.
- Kept original clients separate from Classic rereleases and moving modern targets.
- Marked Ashamane's advertised BFA branch as unavailable after checking live refs.
- Added nine preservation/failure tests and offline native catalog acceptance checks.

Remote Luna installation, client build inspection/configuration/launch, automatic
client downloads, alternate-core installers, and archive restoration remain future work.

## 0.1.0a2 — First Campfire desktop preview — 2026-09-12

- Began the new preview version before adding the native desktop feature set.
- Added Qt windows, setup form, service controls, account creation, native archives,
  background progress, Windows executable packaging, and desktop shortcuts.
- Added a local Docker realm installer with pinned core/modules, generated
  configuration, dedicated databases, supplied-data extraction, and backups.
- Added original 3.3.5a SRP account registration and a real authserver protocol test.
- Added checks for realm operation locks, failures, data boundaries, and desktop packaging.
- Retained command-line tools and optional standalone HTML archive export.
- Fixed Windows source-launcher selection when the default Python is unsupported;
  added a Python-free download shortcut and browser sign-in/artifact instructions.
- Fixed the worldserver runtime's missing ncurses library and checked shared
  libraries for the server binaries and extraction tools during image construction.

Game data extraction, world startup, in-game play, WoWee installation, and
restoration still need live acceptance testing. See PR checks for build evidence.

## 0.1.0a1 — First Campfire preview — 2026-09-12

- Added fictional character demo and offline archive desk with searchable tables.
- Added explicit-table, read-only AzerothCore capture with module settings, item
  definitions, ownerless mail-attachment traversal, and coverage reporting.
- Added bounded data-only archives, checksums, raw typed rows, and table-level diffs.
- Added candidate source pins and explicit source preparation without installing
  dependencies, assets, or services.
- Added Windows/Linux launchers, automated tests, CI, access guidance, and the
  future town/instance/region content-workshop roadmap.

Live realm setup, MySQL integration, restoration, and cross-core transfer are not
complete. Final 0.1.0 awaits verified login and restoration in a disposable realm.
