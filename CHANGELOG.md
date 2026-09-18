# Changelog

## Repository recovery — 2026-09-17

- Reunited the preserved development history on main, which had still shown only
  the initial README; retained the older branches as recovery references.
- Identified 0.1.0a8 as the current preview and replaced outdated branch/Actions
  download instructions with a versioned Windows release and checksums.
- Updated the roadmap and testing guide to distinguish completed implementation,
  successful automated checks, and remaining user acceptance.

## 0.1.0a8 — At the War Table

- Painted stone, wood, vellum, map details, framed controls, and icon medallions
  on the native Home widgets, with verified bundled material assets.
- Full portal panorama fitted without cropping, native wrapping captions, and
  Windows font/layout fixes; existing Play and realm safeguards retained.
- Source and packaged Windows acceptance for Home materials, all six themes,
  archive and client workflows, and missing-art fallback.

## 0.1.0a7 — The Portal Awakens

- Bundled painterly Home artwork, native launch desk, and responsive layout.
- Preserved artwork provenance and checksums, with vector fallback.

## 0.1.0a6 — Six Worlds, One Hearth

- Reconstructed the six themed pages from the preserved a5 implementation.
- Kept realm operations and original Wrath compatibility separate from decoration.
- Added theme integrity and native six-page acceptance checks.

## 0.1.0a5 — Through the Gates

- Native Warcraft-inspired home screen, winter-gate vector artwork, framed navigation icons,
  dark metal controls, parchment game card, and clear Play readiness messaging.
- Windows Wow.exe selection stored per realm, version-resource inspection for 3.3.5a/12340,
  locale selection, required-file checks, and explicit local connection setup with an exact-byte backup.
- Play revalidates the client, starts services when needed, checks their health, and launches
  the game with its own working directory. Failed/cancelled startup does not launch it.
- Companion command guide; existing realm operations remain under expandable Realm tools.
- Unit coverage for client/connection/startup behavior and native smoke coverage for the full
  button flow, saved selection, failed startup, duplicate clicks, and small-window layout.
- The earlier a4 draft mentioned in conversation could not be verified in the repository;
  a5 avoids reusing its version. Luna, automated downloads, and extension installation remain planned.


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
