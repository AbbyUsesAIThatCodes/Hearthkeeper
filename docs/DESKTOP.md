# Desktop architecture

Hearthkeeper uses **PySide6 / Qt Widgets** for the desktop. There is no embedded
browser, webview, localhost HTTP application, Electron runtime, or Node dependency.
Qt provides native windows, dialogs, file pickers, tables, keyboard focus, and a
background-worker boundary for long operations.

The existing archive/database/model code remains separate from the UI. The same
`.hearth` file can be read by the native viewer or exported as standalone HTML.
Original records remain authoritative; neither viewer silently translates
unknown custom-module state into invented game semantics.

The server layer has two parts:

- **Host controller:** validates a selected local Docker context, writes a small
  controlled build context, and runs argument-list subprocess commands. It manages
  per-realm identity, state, locks, and progress. It does not use `shell=True`.
- **Realm container:** compiles/runs upstream code and performs configuration,
  SQL initialization, extraction, account registration, capture, and backup tasks.
  Runtime auth/world services receive only their configuration, extracted data,
  log, and temporary directories. No Docker socket is mounted into them.

The database uses a dedicated named volume. Unique service passwords are stored
with private local realm metadata; there are no shared default realm credentials.
The server has database privileges for its own schemas, while character capture
uses a separate SELECT-only identity. MySQL is reachable only within the Compose
network. SQL connections are not configured for verified TLS; this initial design
assumes a trusted local Docker environment.

The desktop does not need to run as administrator. Installing Docker or enabling
its Windows prerequisites is a separate system operation. Docker access itself is
powerful: container mounts are not an access boundary that constrains the host
controller or an unrestricted agent. A dedicated development VM remains an option
for stronger separation from personal accounts and files.

## Extend this foundation

Next additions should use the same operation/progress/error interfaces:

1. Complete the real-client, extracted-data, and world startup acceptance gate.
2. Add WoWee setup and explicit client/server patch agreement.
3. Add tested backup recovery and disposable same-core character restoration.
4. Add reviewed updates and configurable networking/remote-server connection.
5. Add content packs and a small town editor, followed by instances and terrain.

The first version deliberately uses a single selected local realm with fixed
ports. There is no generic remote shell, arbitrary command textbox, silent
upgrade, automatic content removal, or database-volume deletion button.

## Packaging and artwork

The Windows build is a PyInstaller directory distribution. The executable and its
`_internal` folder travel together; a shortcut points to the executable. Source
launchers prepare a repository-local virtual environment. The packaged executable
is itself tested in CI, including resource loading and archive interaction.

The initial original vector hearth icon and green/parchment palette can grow into
a more WoW-like visual style. Player-provided local art can be supported later
without making the application depend on downloaded game graphics.

Qt and its libraries remain separately distributed with notices and upstream
source references. See [third-party notices](../THIRD_PARTY_NOTICES.md).

## Through the Gates home screen

`client.py` owns Windows executable metadata inspection, client/locale validation,
local realmlist preparation, service-health gating, and game launch. It uses the
standard-library Windows version API and never executes a file to identify it.
The file version and expected-file checks establish structural compatibility;
they do not authenticate an executable or verify the full MPQ contents.

`desktop.py` stores the chosen executable/locale in QSettings per realm path.
Play uses the existing Worker and ManagedRealm start path, then launches WoW in
its installation directory. Only a process launched by this application instance
is tracked to prevent duplicate clicks. No external game processes are scanned.
The UI never starts services merely by opening the home screen.

Original vector artwork and the shared QSS theme are packaged with the app.
`__ASSETS__` is resolved at runtime for both source and PyInstaller installations.
No remote artwork or browser runtime is required.
