"""Read-only, explicit-table AzerothCore adapter; SQLite is a test fixture backend."""

import contextlib
import re
import sqlite3
from pathlib import Path

from .archive import ArchiveError, json_bytes

CHARACTER_TABLES = (
    "character_action", "character_achievement", "character_achievement_progress",
    "character_aura", "character_equipmentsets", "character_glyphs", "character_homebind",
    "character_inventory", "character_queststatus", "character_queststatus_daily",
    "character_queststatus_weekly", "character_queststatus_monthly",
    "character_queststatus_seasonal", "character_queststatus_rewarded",
    "character_reputation", "character_skills", "character_spell",
    "character_spell_cooldown", "character_talent", "character_settings",
)
PET_TABLES = ("pet_aura", "pet_spell", "pet_spell_cooldown")
WORLD_TABLES = ("item_template", "quest_template")
MAX_ROWS = 100_000


def identifier(value):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ArchiveError("Invalid SQL identifier")
    return "`" + value + "`"


class Reader:
    def __init__(self, connection, dialect, databases=None):
        self.connection = connection
        self.dialect = dialect
        self.databases = databases or {}
        self.placeholder = "?" if dialect == "sqlite" else "%s"
        self._table_cache = {}
        self._column_cache = {}

    def query(self, sql, parameters=()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, tuple(parameters))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def qualified(self, namespace, table):
        if self.dialect == "sqlite":
            return identifier(table)
        return identifier(self.databases[namespace]) + "." + identifier(table)

    def tables(self, namespace):
        if namespace not in self._table_cache:
            if self.dialect == "sqlite":
                rows = self.query("SELECT name FROM sqlite_master WHERE type = 'table'")
                names = {row["name"]: "SQLite" for row in rows}
                names = {name: engine for name, engine in names.items()
                         if (name in WORLD_TABLES) == (namespace == "world")}
            else:
                rows = self.query("SELECT TABLE_NAME AS name, ENGINE AS engine FROM "
                                  "information_schema.TABLES WHERE TABLE_SCHEMA = %s "
                                  "AND TABLE_TYPE = 'BASE TABLE'", (self.databases[namespace],))
                names = {row["name"]: row["engine"] for row in rows}
            self._table_cache[namespace] = names
        return self._table_cache[namespace]

    def columns(self, namespace, table):
        cache_key = (namespace, table)
        if cache_key not in self._column_cache:
            if self.dialect == "sqlite":
                rows = self.query(f"PRAGMA table_info({identifier(table)})")
                columns = [{"name": row["name"], "type": row["type"],
                            "nullable": not row["notnull"], "primary_key": bool(row["pk"])}
                           for row in rows]
            else:
                if self.tables(namespace).get(table) != "InnoDB":
                    raise ArchiveError("Consistent capture requires InnoDB tables; use an offline copy")
                rows = self.query("SELECT COLUMN_NAME AS name, COLUMN_TYPE AS type, "
                                  "IS_NULLABLE AS nullable, COLUMN_KEY AS column_key FROM "
                                  "information_schema.COLUMNS WHERE TABLE_SCHEMA = %s "
                                  "AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
                                  (self.databases[namespace], table))
                columns = [{"name": row["name"], "type": row["type"],
                            "nullable": row["nullable"] == "YES",
                            "primary_key": row["column_key"] == "PRI"} for row in rows]
            self._column_cache[cache_key] = columns
        return self._column_cache[cache_key]

    def select(self, namespace, table, key, values):
        if key not in {column["name"] for column in self.columns(namespace, table)}:
            raise ArchiveError(f"Unsupported schema: {namespace}.{table} requires {key}")
        values = sorted(set(values))
        rows = []
        for start in range(0, len(values), 400):
            chunk = values[start:start + 400]
            placeholders = ",".join([self.placeholder] * len(chunk))
            rows.extend(self.query(f"SELECT * FROM {self.qualified(namespace, table)} "
                                   f"WHERE {identifier(key)} IN ({placeholders}) LIMIT {MAX_ROWS + 1}", chunk))
            if len(rows) > MAX_ROWS:
                raise ArchiveError(f"Row limit exceeded for {table}")
        return rows


@contextlib.contextmanager
def sqlite_reader(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        yield Reader(connection, "sqlite")
    finally:
        connection.rollback()
        connection.close()


@contextlib.contextmanager
def mysql_reader(*, host, port, user, password, characters, world, tls_ca=None):
    identifier(characters)
    identifier(world)
    if host not in ("127.0.0.1", "::1", "localhost") and not tls_ca:
        raise ArchiveError("Use a loopback connection or supply --tls-ca for verified remote TLS")
    try:
        import pymysql
    except ImportError as error:
        raise ArchiveError('MySQL support requires: python -m pip install ".[mysql]"') from error
    connection = None
    try:
        options = dict(host=host, port=port, user=user, password=password,
                       charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
                       connect_timeout=10, read_timeout=60, write_timeout=30,
                       autocommit=False, local_infile=False)
        if tls_ca:
            options.update(ssl_ca=str(tls_ca), ssl_verify_cert=True, ssl_verify_identity=True)
        connection = pymysql.connect(**options)
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
        yield Reader(connection, "mysql", {"characters": characters, "world": world})
    except pymysql.MySQLError as error:
        # Do not expose connection parameters or server messages in logs/archives.
        raise ArchiveError("Database operation failed; check connectivity, SELECT grants, and schema") from error
    finally:
        if connection is not None:
            connection.rollback()
            connection.close()


def capture(reader, guid, realm, core_commit="unrecorded", demo=False):
    if type(guid) is not int or guid <= 0:
        raise ArchiveError("Character GUID must be a positive integer")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", realm):
        raise ArchiveError("Use a stable realm identifier of 1-80 letters, numbers, dots, dashes, or underscores")
    if core_commit != "unrecorded" and not re.fullmatch(r"[0-9a-f]{40}", core_commit):
        raise ArchiveError("Core commit must be a full lowercase Git SHA or unrecorded")
    tables, missing = {}, []
    warnings = [
        "Partial character archive: not a complete realm backup or a ready-to-import character.",
        "Custom scripts, DBC/assets, account-wide data, guild banks, auction state, and bot databases are not captured.",
        "Learned spell IDs are preserved; recipe names and full spell definitions need a future DBC adapter.",
        "World rows are references, not a complete custom-content dependency package.",
    ]

    def take(namespace, table, key, values):
        name = namespace + "." + table
        if table not in reader.tables(namespace):
            missing.append(name)
            return []
        rows = reader.select(namespace, table, key, values)
        tables[name] = {"columns": reader.columns(namespace, table),
                        "rows": sorted(rows, key=json_bytes)}
        return rows

    character = take("characters", "characters", "guid", [guid])
    if len(character) != 1:
        raise ArchiveError("Expected exactly one character with this GUID")
    if "online" not in character[0]:
        raise ArchiveError("Unsupported characters schema: online field is required")
    if character[0]["online"]:
        raise ArchiveError("Log this character out before capture so its state is saved")
    for table in CHARACTER_TABLES:
        take("characters", table, "guid", [guid])
    pets = take("characters", "character_pet", "owner", [guid])
    for table in PET_TABLES:
        take("characters", table, "guid", [pet["id"] for pet in pets])
    mail = take("characters", "mail", "receiver", [guid])
    attachments = take("characters", "mail_items", "mail_id", [letter["id"] for letter in mail])
    inventory = tables.get("characters.character_inventory", {}).get("rows", [])
    item_ids = {row["item"] for row in inventory} | {row["item_guid"] for row in attachments}
    owned_items = take("characters", "item_instance", "owner_guid", [guid])
    if "characters.item_instance" in tables:
        linked_items = reader.select("characters", "item_instance", "guid", item_ids)
        by_guid = {row["guid"]: row for row in owned_items + linked_items}
        if len(by_guid) > MAX_ROWS:
            raise ArchiveError("Too many item instances")
        tables["characters.item_instance"]["rows"] = sorted(by_guid.values(), key=json_bytes)
        items = list(by_guid.values())
    else:
        items = []
    templates = take("world", "item_template", "entry", [row["itemEntry"] for row in items])
    quest_ids = {row["quest"] for table in CHARACTER_TABLES if table.startswith("character_queststatus")
                 for row in tables.get("characters." + table, {}).get("rows", [])}
    take("world", "quest_template", "ID", quest_ids)
    missing_items = item_ids - {row["guid"] for row in items}
    if missing_items:
        warnings.append(f"Unresolved inventory/mail references: {len(missing_items)} item instances missing.")
    missing_templates = {row["itemEntry"] for row in items} - {row["entry"] for row in templates}
    if missing_templates:
        warnings.append(f"Missing item definitions: {len(missing_templates)} template IDs unresolved.")
    if core_commit == "unrecorded":
        warnings.append("Source core commit was not recorded; exact version compatibility is unknown.")
    unhandled = sorted(namespace + "." + name for namespace in ("characters", "world")
                       for name in reader.tables(namespace) if namespace + "." + name not in tables)
    source = {"realm": realm, "character_guid": guid, "core": "azerothcore-wotlk",
              "core_commit": core_commit, "client_build": 12340, "adapter": "azerothcore-preview/1",
              "client_build_basis": "adapter target, not independently detected",
              "backend": reader.dialect, "fictional_demo": demo,
              "consistency": "single-read-transaction; persisted database state"}
    return {"source": source, "tables": tables, "warnings": warnings,
            "coverage": {"missing_tables": sorted(missing), "unhandled_tables": unhandled}}
