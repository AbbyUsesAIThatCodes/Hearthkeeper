# Test this PR in GitHub Desktop

1. Fetch origin and select `feature/first-campfire-preview`.
2. Open the repository in Explorer and run `Start-Hearthkeeper.bat`.
3. If Python is missing or too old, install Python 3.11+ and rerun. No WoW client,
   Docker, MySQL, or game assets are needed for this preview.

## What should happen

- A browser document displays **Brindle**, a fictional level 24 dwarf priest,
  with a clear fictional-demo notice and partial-coverage label.
- Equipment & bags shows six item records, including an ownerless addressed mail
  attachment, a bank stack, and the Copperleaf Lantern.
- Searching `Lantern` filters table rows; clearing the search restores them.
- Module data expands to show the fictional progression/journal payloads exactly.
- Coverage identifies missing tables and an unsupported custom-town table.
- The document continues working offline. Each demo run has its own output folder.
- Running the BAT again does not overwrite the first archive or HTML file.

The sample fixtures are deliberately incomplete. Missing tables are expected.
Demo progression payloads are marked fictional and are not the serialized format
of Individual Progression.

## Optional command-line checks

In a terminal opened in the repository, replace the example archive path with
the one printed by your demo:

```sh
python -m hearthkeeper verify var/demo/YOUR-RUN/brindle.hearth
python -m hearthkeeper inspect var/demo/YOUR-RUN/brindle.hearth
python -m hearthkeeper realm-plan
python -m unittest discover -s tests -v
```

`verify` should report valid checksums and structure while still describing the
archive as partial and unsigned. `realm-plan` displays exact candidate commits
and does not download, build, or launch anything.

## Useful feedback

Report whether the BAT opens the viewer, whether the layout feels readable, and
whether equipment/search/module/coverage views behave as described. Copy an error
message rather than attaching private files. If all looks good, merge the PR.

CI additionally checks a disposable MySQL service with fictional fixture tables
and exercises the viewer in Chromium. Live-server build, login, capture against
full upstream schemas, healing with bots, and restoration belong to the next
acceptance gate; passing these fixture checks does not establish them.
