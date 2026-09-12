# Character archives

## Scope of the preview

The adapter targets AzerothCore-shaped character/world schemas. It captures one
selected character and known related records. Missing expected tables and existing
unsupported tables are listed in Coverage; unknown tables are never guessed at
or read wholesale. Unknown columns in captured rows are retained.

Captured families include character identity/state, inventory, item instances,
item definitions, learned spells/skills, quests and referenced quest definitions,
reputation, achievements, talents/glyphs, actions, homebind, settings, pets and their
spells/auras/cooldowns, and mail addressed to this character with its attachments.
Some families may be absent from a particular schema.

Inventory and addressed-mail references supplement item ownership when finding
item instances. An attachment may have `owner_guid = 0`; it must not vanish merely
because an ownership-only query misses it. Other characters' inventories, mail,
and module payloads are not exported. Other players' numeric IDs can still occur
in references, such as a mail sender; they are not a portable global identity.

`character_settings` is explicitly included. Its payload is preserved as-is;
understanding every module's serialized format is future adapter work. The demo
uses a fictional progression record, not a claim about the real module's encoding.

Not yet complete: account-level state, guild/social/group/instance data, auction
state, additional item auxiliary tables, bot databases, custom module tables,
spell/recipe DBC definitions, script code, and client assets. World table rows
are references, not a complete dependency closure. Realms can add other state
outside these lists. **This is not a complete backup or an import package.**

## MySQL capture (integration pending)

Use a disposable/offline copy of the realm for the first live test. Have a
separate database account with SELECT-only privileges on the character and world
databases (or the explicitly needed tables). Do not use the auth account, server
root account, or existing website credentials. The exporter does not create users
or grants and does not query the auth database.

Install the optional connector in a project virtual environment:

```sh
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS instead: . .venv/bin/activate
python -m pip install ".[mysql]"
```

Then, with the selected character logged out and maintenance/DDL paused:

```sh
python -m hearthkeeper capture-mysql --guid 7 --realm my-hearthkeeper --core-commit YOUR_40_CHARACTER_CORE_SHA --output var/archives/character-001.hearth
```

The password is prompted without echo and is not stored. Never put it into a
command line, issue, archive, or chat. Defaults are loopback port 3306,
`hearthkeeper_reader`, `acore_characters`, and `acore_world`. Customize with
`--host`, `--port`, `--user`, `--characters`, and `--world`. Non-loopback connections
require `--tls-ca` for certificate and hostname validation; an SSH tunnel to a
trusted host is another way to use a loopback endpoint.

Use a stable, unique `--realm` namespace for successive snapshots. The supplied
core SHA is provenance declared by the operator, not independently detected by
the exporter. If omitted, it is recorded as unknown. Lockfile pins do not prove
the running server uses those revisions.
The recorded client build is the adapter's target, not a negotiated client or an
independent server-version detection result.

The connection starts one REPEATABLE READ, READ ONLY transaction with a consistent
snapshot, spanning the character/world databases. Queried MySQL tables must use
InnoDB. The character must not be marked online. This captures persisted database
state, not unsaved worldserver memory; a quiet offline copy avoids login races and
schema changes during capture. Don't run server updates/DDL during export.

Review the generated archive before relying on it:

```sh
python -m hearthkeeper verify var/archives/character-001.hearth
python -m hearthkeeper render var/archives/character-001.hearth --output var/archives/character-001.html
```

No MySQL import/restore command is present. Retain normal private backups of auth,
characters, world, bot databases, configuration, scripts, and the exact content
versions independently. Character archives omit authentication secrets; whole-realm
recovery backups require different protection and a broader inventory.

## File format v1

A `.hearth` file is a data-only ZIP with exactly two members:

- `manifest.json`: format identifier `hearthkeeper.character/1`, app version,
  creation time, payload length, SHA-256, partial-completeness label, and unsigned flag.
- `snapshot.json`: source namespace/GUID/core revision, raw table rows, column
  metadata, coverage lists, and warnings.

The limit is 64 MiB uncompressed snapshot data and 100,000 rows per captured table.
The reader rejects duplicate ZIP members, unexpected paths, unknown format
versions, duplicate JSON keys, non-finite JSON values, and oversized payloads.
It never extracts ZIP paths onto disk and never evaluates SQL, Python, or scripts
from an archive. Writes use exclusive creation and do not replace existing files.

Integers remain integers (the HTML renderer renders text, avoiding JavaScript
integer rounding). Binary, Decimal, date/time, and timedelta database values use
`{"$type": "...", "value": "..."}` representations. Binary is base64; decimals
use decimal strings. A future importer must explicitly decode these types.

The `inspect` command derives a `hearthkeeper.character-view/1` JSON model. Its
IDs combine the source realm, entity kind, and original ID. Definitions have
fingerprints to detect differences; matching hashes alone do not prove equivalent
runtime behavior. Original rows remain the preservation record.

The archive checksum is not a signature. Anyone able to replace the payload and
manifest can produce another valid checksum. Real `.hearth` files and rendered
HTML can include private character mail/settings; neither format is encrypted.
