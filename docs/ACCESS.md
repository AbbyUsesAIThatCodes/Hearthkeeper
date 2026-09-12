# Development access

Broad access to the everyday desktop account is unnecessary for this project.
The repository/PR workflow is the default: code is prepared in an isolated work
environment and you run the reviewed branch locally.

Personal mail, browser sessions, password stores, photos, and adult material are
outside the scope of Hearthkeeper. There is no need to describe, upload, move, or
expose those files to work on this project. No zero-risk claim is made about
unrestricted system access or third-party server/client software.

## If local agent access becomes useful

Use a dedicated development VM with a clean account. Copy only Hearthkeeper and
explicitly needed game data into it. Do not share the host home directory, browser
profile, password store, whole drives, or Docker socket; leave shared clipboard
and drag/drop disabled unless specifically needed. Keep ordinary personal account
sign-ins out of that guest. VM snapshots make recovery easier, but do not make a
VM an absolute security guarantee.

A container that has your home directory or Docker socket mounted is not this
separation. A separate OS account can also help, but its actual filesystem and
administrator permissions determine what it protects. A project working directory
and a promise to stay inside it do not themselves prevent broader reads.

Any future access should be limited to the development environment and the task.
Do not paste account passwords, browser cookies, or recovery codes into chat or
issues. Installation and administrator changes should be specific and reviewable.

## What this preview does

- `demo` writes its own fictional SQLite file, `.hearth` archive, and HTML under
  `var/demo/` by default; it opens the HTML only when `--open` is requested.
- `doctor` checks the Python version and whether Git is on PATH. It does not scan
  for clients, account data, personal folders, or installed games.
- `prepare-sources` is an explicit network operation that fetches only the pinned
  repositories into a new destination. It does not build or launch their code.
- `capture-mysql` queries selected character/world records using one read-only
  transaction and a password prompt. It never connects to the auth database.
- The offline HTML contains no remote fonts, scripts, images, analytics, or forms.
  Its content is escaped and its script is restricted with a CSP hash.

Real archives and their HTML views are private data, **not encrypted files**.
They can include character mail and module settings. Protect them like backups;
do not post them in the public repository. Checksums are not encryption or signatures.

For agent sandbox and approval behavior, consult the current
[official OpenAI sandbox documentation](https://learn.chatgpt.com/docs/sandboxing).
Available controls differ by execution environment; do not assume a sandbox's
write restrictions also prevent all reads.
