# 0.1.0a6 — Six Worlds, One Hearth

Historical implementation notes. For the current **0.1.0a8** download and source
branch, use [README.md](../README.md). The original instructions below describe a6.

This is a new reconstruction from the saved a5 release, not the missing original a6 files. The decorative headers are new, stylized vector illustrations rather than recovered painterly artwork. No Blizzard assets or fonts were copied.

## What changes

Six distinct scenes follow the approved mapping: a portal for Home (Burning Crusade), heraldry for Characters (Legion), a jade library for Archives (Mists), an icy vault for Backups (Wrath), an expedition camp for Sources (Warlords), and a forge for Workshop (Cataclysm). Text remains native, selectable by accessibility tools, and separate from the artwork. Ornamental borders, navigation accents, and scrollable pages preserve the familiar controls.

The persistent sidebar label states the actual managed realm compatibility: original Wrath 3.3.5a / build 12340. Artwork never changes the selected realm or claims that other eras are installed. Workshop remains planned, not a working content editor.

`hearthkeeper.six_worlds.MainWindow` subclasses the existing realm window. Play, character capture, account handling, realmlist confirmation, cancellation, source acquisition, and backups retain their existing implementations. The original live realm and client were not accessed during reconstruction. This update does not migrate to Luna.

## Launch routes

- Packaged Windows preview: use the successful Native desktop run for this PR, download **Hearthkeeper-0.1.0a6-Windows**, extract the whole ZIP, and open Hearthkeeper.exe. Do not treat an in-progress or failed run as a published build.
- Source: choose `feature/six-worlds-recovery` in GitHub Desktop and run `Start-Hearthkeeper.bat`. The bootstrap refreshes editable metadata when pyproject.toml changes, including the GUI entry point.
- Installed environment: `hearthkeeper-desktop` or `python -m hearthkeeper.six_worlds`.
- The old `python -m hearthkeeper.desktop` command remains an unthemed diagnostic fallback; it is no longer the primary launcher.

Existing desktop shortcuts are deliberately not overwritten. New source shortcuts target the themed module; old source shortcuts can still open the fallback interface.

## Validation and acceptance

Six new standard-library tests cover the exact mapping, distinct deterministic self-contained SVGs, internal SVG references, unknown-theme errors, text-palette contrast, and the realm/workshop disclaimers. During reconstruction, these six tests and Python syntax compilation passed locally; all six scenes were rendered with CairoSVG and visually inspected. This environment did not have Qt or the full baseline checkout, so this was not a local complete-app test.

The Native desktop workflow runs the existing functional acceptance suite against the themed subclass, then checks all six tabs at 1240 × 880 and 980 × 700, disabled Play without a realm, wrapping header text, scrolling, and the realm-tools toggle. It repeats acceptance in the packaged executable and requires `six-worlds-result.json` as well as the existing result file. PNGs and result JSONs are uploaded as workflow artifacts. Its result must be confirmed separately; defining these checks does not mean they passed.

Actual game launch and live gameplay still require a Windows user playtest. Mock service/process tests are not evidence of a live world. Text palette checks are not a whole-application accessibility certification.

## Continuity

The recovery branch begins at a5 merge `57d3800d340511b2283721d46ffb87420632e5ef`, based on `feature/source-catalog`, not main. `docs/SIX_WORLDS_RECOVERY.md` preserves the original design before implementation. Keep incremental commits and a current PR status; do not rely on a conversation or an unpublished local directory as the only copy.
