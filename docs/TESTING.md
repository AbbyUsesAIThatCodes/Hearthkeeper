# Test the current desktop preview

The current version is **0.1.0a8 — At the War Table**, available from **main** and
the [Windows release](https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/releases/tag/v0.1.0a8).
See [the recovery record](RECOVERY.md) for the exact restored commit and build
evidence. Packaging checks do not establish live gameplay readiness.

## Without Docker or game files

1. Run the packaged **Hearthkeeper.exe**, or use **Start-Hearthkeeper.bat** in
   GitHub Desktop with Python 3.11–3.13.
2. Confirm it opens a desktop window and leaves server services untouched.
3. Open **Archives → Meet Brindle · demo**.
4. Inspect Overview, select **Equipment & bags**, search for `Lantern`, then clear it.
   Six item rows should return, including the addressed mail attachment.
5. Inspect **Module data** and **Coverage**. The custom-town table is intentionally
   unsupported; fictional module settings are retained without decoding them as real IP data.
6. Resize the window and move between the sidebar pages.
7. Use **Desktop shortcut** and launch through the resulting icon.

The fixture is fictional and incomplete. It contains no game assets. The native
viewer works offline. The original HTML demo remains available through
**Start-Archive-Demo.bat**.

## Source catalog proof of concept

Follow [Sources → catalog and saved copies](SOURCE_CATALOG.md). Try ChromieCraft’s
source page, filter SkyFire to Mists, save an Individual Progression source snapshot,
and import a small file before trying a large client archive. Verify the saved copy
and confirm that no realm started or changed. Imported files are associated with a
catalog offering by your selection; their client builds are not inspected yet.

## With Docker and matching files

Follow [realm setup](REALM_SETUP.md). Record the first failed stage and its final
Activity lines if setup stops. Do not post credentials, real archives, SQL dumps,
or private mail in the public repository.

Check New realm → installation → account creation → Start → client connection.
Test Stop and Start again. Check settings changes only while stopped, the backup
folder, and character capture after logout. An `.incomplete` backup is not a
successful backup. Keep normal realm backups until restoration is tested.

## Automated evidence

- 66 unit tests cover archive preservation, artwork integrity, ownership boundaries, damaged files,
  local-only Compose bindings, read-only game mounts, incomplete data, failed-import
  state, concurrent-operation locks, remote Docker rejection, and password redaction.
- The native Qt smoke test checks startup without processes/browser calls, archive
  search, module/coverage views, literal text handling, and background work.
- Windows CI repeats the native checks inside the packaged executable.
- Windows CI also reproduces a Python 3.14 default with Python 3.12 installed
  alongside it, then checks that the BAT source launcher selects the supported one.
- The real-source build gate compiles the selected stack, imports upstream SQL,
  verifies an SRP exchange against authserver, and checks backup creation.
- The runtime image checks shared libraries for the core and all extraction tools;
  the world binary must initialize its databases before rejecting absent game maps.
- Existing Windows/Linux archive, Chromium HTML-viewer, and fictional MySQL checks remain.

Run the dependency-free suite with `python -m unittest discover -s tests -v`.
In a supported Python 3.11–3.13 environment with `.[desktop]` installed, run
`python -m hearthkeeper.six_worlds --smoke-test var/native-source` with
`QT_QPA_PLATFORM=offscreen`. The Windows package accepts the same `--smoke-test`
argument. Acceptance writes `result.json`, `six-worlds-result.json`, and
`home-art-result.json`; all three must report `passed: true`.

Game data extraction, world startup, in-game behavior, and restore remain separate
acceptance gates. CI's placeholder data is never passed to a worldserver.

## Home and Play acceptance

See [HOME.md](HOME.md) for the first-run path. Automated native acceptance uses
fictional game files, a patched metadata reader, and mocked realm/process calls;
no game binary or Docker service is launched. It exercises selection, refusing
and accepting the connection change, original-byte backup, saved selection,
healthy-realm launch, duplicate requests, failure reporting, and 980 × 700 layout.
Unit tests cover stopped-realm startup, health failure, cancellation, wrong builds,
multiple locales, missing files, backup failure, and the launch working directory.
Windows unit tests read the real Python executable's version to exercise Win32 APIs.

For live acceptance, use the existing realm and matching Windows client. Verify
that Play launches it with the server initially stopped, and again with the realm
already healthy. Verify the existing character after logging in. Confirm that a
second Play click is disabled while this app's launched game is still running.
Quit WoW and verify that Play becomes available again. Closing Hearthkeeper should
leave the game and running realm alone. Keep the connection `.bak` if this client
was previously pointed at a different server.
