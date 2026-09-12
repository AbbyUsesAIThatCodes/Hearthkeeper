# Test the desktop PR

This branch is `feature/desktop-realm-manager` and the version is **0.1.0a2**.
It builds on the still-separate archive preview PR. The PR description records
the exact commit and CI outcomes; do not infer gameplay readiness from packaging checks.

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

## With Docker and matching files

Follow [realm setup](REALM_SETUP.md). Record the first failed stage and its final
Activity lines if setup stops. Do not post credentials, real archives, SQL dumps,
or private mail in the public repository.

Check New realm → installation → account creation → Start → client connection.
Test Stop and Start again. Check settings changes only while stopped, the backup
folder, and character capture after logout. An `.incomplete` backup is not a
successful backup. Keep normal realm backups until restoration is tested.

## Automated evidence

- 26 unit tests cover archive preservation, ownership boundaries, damaged files,
  local-only Compose bindings, read-only game mounts, incomplete data, failed-import
  state, concurrent-operation locks, remote Docker rejection, and password redaction.
- The native Qt smoke test checks startup without processes/browser calls, archive
  search, module/coverage views, literal text handling, and background work.
- Windows CI repeats the native checks inside the packaged executable.
- The real-source build gate compiles the selected stack, imports upstream SQL,
  verifies an SRP exchange against authserver, and checks backup creation.
- Existing Windows/Linux archive, Chromium HTML-viewer, and fictional MySQL checks remain.

Game data extraction, world startup, in-game behavior, and restore remain separate
acceptance gates. CI's placeholder data is never passed to a worldserver.
