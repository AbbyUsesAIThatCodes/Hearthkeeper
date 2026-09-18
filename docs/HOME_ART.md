# 0.1.0a7 — The Portal Awakens

Historical implementation notes. **0.1.0a8** supersedes this preview; use the
[current download](../README.md) and [Home materials guide](HOME_MATERIALS.md).

A Home-only painterly pass over the merged a6 build. This is an implementation of the visual direction, not a pixel-for-pixel copy of the generated mockup.

## What is real

Home uses a cropped, painted portal scene from the concept generated in this conversation. Its fake service statuses, character count, backup date, and controls are excluded from the artwork crop. Headings, status cards, client selection, Play, shortcuts, and realm tools remain native Qt widgets. The application does not report the mockup's fictional readiness or backup history.

The Home presentation adds bronze frames, a dark stone-colored sidebar, a parchment installation panel, a red/gold Play control, and a launch desk that stacks when the available width is under 850 logical pixels. The other five tabs retain their a6 artwork. The actual realm remains original Wrath 3.3.5a/build 12340; Burning Crusade is the decorative Home theme, not a realm switch.

`home_art.py` rearranges the existing controls and paints scenery. It does not implement or replace realm operations, Play state logic, backup handling, accounts, or client changes. The existing client and Play widgets are reused, including their existing signals and confirmation behavior. Disabled Play stays visibly disabled. No live realm, character, account, client, or Luna data was accessed to develop this change.

## Asset preservation

`assets/home-art.json` records the original concept's SHA-256, exact crop, runtime resolution, and decoded raster checksum. The runtime WebP is stored in three ASCII base64 parts to preserve its exact bytes through the connected repository API. `art_assets.read_home_art()` concatenates the fixed filenames, decodes in memory, and verifies the SHA-256 before use. It does not download or write files. Missing or corrupt artwork falls back to the existing vector scene with an explanatory native caption.

The 736 × 260 runtime crop is compact, not a new high-resolution painting. The full 1536 × 1024 source concept and a larger crop are preserved in the downloadable art/source checkpoint. The manifest references that source; it does not imply the original full concept is bundled with the app. No font files are added.

## Validation

Local validation covers the changed-file staging directory, not a full repository checkout: twelve standard-library tests pass (six Home asset/boundary tests plus six existing theme tests), and available Python files compile. The decoded raster was inspected. Local Qt and full baseline application execution were unavailable.

The Native desktop workflow runs the existing functional suite against the themed window, the six-page checks, and new Home checks at 1440 × 1000, 1240 × 880, and 980 × 700. Home checks require the actual raster, verify its checksum and size, assert inherited Play behavior and honest initial statuses, exercise responsive layout and scrolling to Play/tools, test other-page style isolation, and exercise missing-art fallback. All checks repeat in the Windows executable. A Windows artifact is accepted only after `home-art-result.json` is present alongside the original two result files.

Refer to the PR for current CI results; configuring these checks is not evidence they passed. Actual game launch and full visual acceptance still require the user's Windows playtest. Mocked processes and fictional data do not establish live gameplay.

## Try the preview after successful CI

Use the Native desktop workflow linked from this PR, download `Hearthkeeper-0.1.0a7-Windows`, extract the entire ZIP into a new folder, and open Hearthkeeper.exe. Keep the previous app as a fallback. Explore Home without a realm first; then choose **Open realm** for the existing folder containing `realm.json`. Do not create a replacement realm to test the artwork.

Source route: branch `feature/home-portal-art`, `Start-Hearthkeeper.bat` or `python -m hearthkeeper.six_worlds` in the installed environment. The legacy `hearthkeeper.desktop` module remains the older diagnostic interface.

Baseline: merged a6 commit `db83178b205f829c6ef9424a285347f4acd03dd0`, targeting `feature/source-catalog`, not main. Luna migration, new expansion support, update checking, and extra mockup-only buttons are not implemented by this art pass.
