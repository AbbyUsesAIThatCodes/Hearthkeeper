# Repository recovery — 2026-09-17

## What happened

GitHub's default branch, `main`, still pointed at initial commit `92f1e47`,
whose only file was README.md. The application had accumulated on a stack of
feature branches. The local active checkout was a6 (`db83178`), and another
local copy was at `a48022e`. Public-facing instructions still named a2/a5
downloads and an older feature branch. No Git object corruption was found in
either local repository; this inspection does not establish an outage as the cause.

## Recovered baseline

The complete latest merged implementation is **0.1.0a8 — At the War Table**,
commit `9fc68b75c5968a1691caf14cea4fd47b2d2a8aa5` on the former integration
branch `feature/source-catalog`. It includes the archive desk, realm manager,
source catalog, client/Play safeguards, six themed pages, and painted Home.

The repair brings that existing history forward to **main** and corrects the
front page, launcher guidance, version history, and roadmap. Historical branches
are retained. Future development starts from main and uses reviewed PRs; users
download the Windows ZIP from **Releases**, without selecting an Actions run.

Before repair, both original local directories, including their `.git` history,
were copied into a separate local recovery folder. That checkpoint and a Git
bundle of the fetched history are kept outside the public source tree. Live
realm databases, accounts, characters, client installations, and settings were
not part of this repository recovery.

## Evidence

- `git fsck --full --no-reflogs` found no errors or unreachable recoverable objects
  in either original local repository. The fetched recovery checkout also passes
  `git fsck --full`.
- All **66 unit tests passed locally on Windows / Python 3.14**. This is evidence
  for the dependency-free tests; the source GUI still requires Python 3.11–3.13.
- [Native desktop run 35288669492](https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/actions/runs/35288669492)
  succeeded for the exact recovered baseline, including source and packaged app
  acceptance and Windows Python selection.
- [Cross-platform checks 35288669398](https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/actions/runs/35288669398)
  succeeded at that same commit, including the archive, browser, and MySQL fixtures.
- Downloaded source and packaged results each report `passed: true` for the
  functional suite, six-page suite, and Home artwork suite. The Home reports
  show zero horizontal overflow at all four tested sizes.
- The downloaded Windows executable also passed all three acceptance suites
  locally, hidden/offscreen with fictional fixtures. Its rendered small-window
  Home was inspected. No live realm or game process was used.

The release's Windows executable is the unchanged successful artifact from
`9fc68b7`, promoted out of temporary Actions storage. Release notes identify its
source and checksums. Documentation and build-discovery changes do not relabel
the application as a new a9 release.

## Limits and next step

The unpublished original a4/a6 drafts and original full art concepts were not
found in these repositories. Their reconstructed code, runtime artwork, asset
manifests, and preserved history are available. We do not claim to have recovered
unpublished material or to have verified live character/realm data.

Review a8 with the existing realm using [the testing guide](TESTING.md), then
continue with the [Luna migration milestone](ROADMAP.md). Live gameplay,
complete backup restoration, and remote migration remain separate acceptance work.
