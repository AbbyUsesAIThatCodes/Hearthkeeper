"""Render an offline HTML document; all archived strings are escaped as text."""

import base64
import hashlib
from html import escape
import json
from pathlib import Path

from .archive import read_archive, write_new
from .model import normalized, records


def text(value):
    return escape(str(value), quote=True)


def table(headers, rows):
    rows = list(rows)
    if not rows:
        return '<p class="empty">No records were captured for this section. Check Coverage for missing tables.</p>'
    return '<div class="table-scroll"><table><thead><tr>' + ''.join(
        '<th scope="col">' + text(header) + '</th>' for header in headers
    ) + '</tr></thead><tbody>' + ''.join('<tr data-search-row>' + ''.join(
        '<td>' + text(value) + '</td>' for value in row) + '</tr>' for row in rows
    ) + '</tbody></table></div>'


def render_archive(archive_path, output_path):
    manifest, snapshot = read_archive(archive_path)
    model = normalized(snapshot)
    character = model["character"]
    assets = Path(__file__).parent / "assets"
    css = (assets / "viewer.css").read_text(encoding="utf-8")
    script = (assets / "viewer.js").read_text(encoding="utf-8")
    script_hash = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    name = text(character.get("name", "Unnamed explorer"))
    source = snapshot["source"]
    quests = {row["ID"]: row for row in records(snapshot, "world.quest_template")}
    quest_rows = []
    for key, state in (("character_queststatus", "In quest log"), ("character_queststatus_rewarded", "Rewarded")):
        for row in records(snapshot, "characters." + key):
            definition = quests.get(row["quest"], {})
            quest_rows.append([definition.get("LogTitle", f"Quest {row['quest']}"), state, row["quest"]])
    inventory = table(["Item", "Location", "Count", "Template ID"],
                      ([item["name"], item["location"], item["count"], item["entry"]] for item in model["items"]))
    skills = table(["Skill", "Current", "Maximum", "ID"],
                   ([row["name"], row.get("value"), row.get("max"), row["skill"]] for row in model["skills"]))
    spells = table(["Spell ID", "Active", "Disabled"],
                    ([row.get("spell"), row.get("active"), row.get("disabled")]
                     for row in records(snapshot, "characters.character_spell")))
    modules = ''.join('<details><summary>' + text(row.get("source", "Unnamed settings")) +
                      '</summary><pre>' + text(row.get("data", "")) + '</pre></details>'
                      for row in model["module_settings"])
    coverage = table(["Captured table", "Rows", "Columns"],
                     ([name, len(value["rows"]), len(value["columns"])]
                      for name, value in sorted(snapshot["tables"].items())))
    missing = ''.join('<li>' + text(name) + '</li>' for name in snapshot["coverage"]["missing_tables"])
    unhandled = ''.join('<li>' + text(name) + '</li>' for name in snapshot["coverage"]["unhandled_tables"])
    warnings = ''.join('<li>' + text(warning) + '</li>' for warning in snapshot["warnings"])
    raw = ''.join('<details><summary>' + text(name) + '</summary><pre>' +
                  text(json.dumps(value, ensure_ascii=False, indent=2)) + '</pre></details>'
                  for name, value in sorted(snapshot["tables"].items()))
    demo_label = '<div class="notice">FICTIONAL DEMO <span>Sample explorer and custom items. No connection to a WoW server.</span></div>' if source.get("fictional_demo") else ''
    copper = character.get("money", 0)
    money = f"{copper // 10000}g {(copper // 100) % 100}s {copper % 100}c" if type(copper) is int else "Unknown"
    stats = [('Items', len(model['items'])), ('Quests captured', len(quest_rows)),
             ('Skills', len(model['skills'])), ('Module records', len(model['module_settings']))]
    stat_cards = ''.join(f'<div class="stat"><strong>{count}</strong><span>{label}</span></div>' for label, count in stats)
    tabs = [("overview", "Overview"), ("inventory", "Equipment & bags"), ("journal", "Journal"),
            ("skills", "Skills & spells"), ("modules", "Module data"), ("coverage", "Coverage")]
    navigation = ''.join(f'<button type="button" role="tab" id="tab-{key}" aria-controls="{key}" aria-selected="{"true" if index == 0 else "false"}" data-tab="{key}">{label}</button>'
                         for index, (key, label) in enumerate(tabs))
    payload_hash = text(manifest["sha256"])
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{name} · Hearthkeeper</title><style>{css}</style></head><body>
<header class="masthead"><div class="brand"><span class="hearth-mark" aria-hidden="true">✦</span><span>Hearthkeeper<small>YOUR ADVENTURES, KEPT CLOSE</small></span></div><span class="version">FIRST CAMPFIRE <b>0.1.0a1</b></span></header>
<main>{demo_label}<div class="eyebrow">THE ARCHIVE DESK <span> / </span> CHARACTER RECORD</div>
<section class="hero"><div class="portrait" aria-hidden="true">{text(str(character.get('name', '?'))[:1])}</div><div class="hero-text"><span class="eyebrow">AN EXPLORER'S RECORD</span><h1>{name}</h1><p>Level {text(character.get('level'))} · {text(character['race_label'])} {text(character['class_label'])}</p><span class="realm">{text(source['realm'])}</span></div><div class="seal"><span class="seal-icon">✓</span><strong>Checksum verified</strong><span>Partial character archive</span></div></section>
<section class="stats" aria-label="Archive counts">{stat_cards}</section>
<div class="desk"><aside><nav role="tablist" aria-label="Character sections">{navigation}</nav><div class="aside-note"><span>✧</span><p>A place to return to.</p><small>This document works offline. Your server can be asleep.</small></div></aside>
<div class="paper"><div class="paper-top"><span>CHARACTER ARCHIVE</span><label class="search">Find in tables <input id="search" type="search" placeholder="Item, quest, or ID…" autocomplete="off"></label></div><p id="search-status" class="muted" role="status"></p>
<section id="overview" role="tabpanel" aria-labelledby="tab-overview"><h2>The journey so far</h2><p class="intro">The things carried, the skills learned, and the places still waiting.</p><div class="overview-grid"><article><h3>Recorded possessions</h3><p class="big-number">{text(money)}</p><p>Equipment, backpack, bank, and addressed mail references are followed into the item records.</p></article><article><h3>Preservation status</h3><p class="status-pill">PREVIEW · PARTIAL COVERAGE</p><p>Original captured rows are retained, including unknown columns. Unsupported tables and content dependencies still need adapters.</p></article></div><h3>Where this record came from</h3><dl><dt>Character identity</dt><dd>{text(model['identity'])}</dd><dt>Capture time</dt><dd>{text(manifest['created_utc'])}</dd><dt>Core revision</dt><dd>{text(source.get('core_commit'))}</dd><dt>Client protocol</dt><dd>3.3.5a · build 12340</dd><dt>Snapshot SHA-256</dt><dd class="hash">{payload_hash}</dd></dl><p class="footnote">A valid checksum detects damage relative to the manifest. It does not authenticate who created this unsigned archive. Restore and cross-server import are not implemented in this preview.</p></section>
<section id="inventory" role="tabpanel" aria-labelledby="tab-inventory" hidden><h2>Equipment & bags</h2><p class="intro">Every item keeps its original instance and template identifiers.</p>{inventory}<h3>Custom-content references</h3>{table(['Item', 'Script dependency'], ([item['name'], item['script']] for item in model['items'] if item['script']))}<p class="footnote">Script names are references. Their code and client assets are not embedded in this archive.</p></section>
<section id="journal" role="tabpanel" aria-labelledby="tab-journal" hidden><h2>The field journal</h2><p class="intro">Quest records and the definitions available at capture time.</p>{table(['Quest', 'Record', 'ID'], quest_rows)}<h3>Companions</h3>{table(['Name', 'Level', 'Pet ID'], ([row.get('name'), row.get('level'), row.get('id')] for row in records(snapshot, 'characters.character_pet')))}<h3>Addressed mail</h3>{table(['Subject', 'Mail ID'], ([row.get('subject'), row.get('id')] for row in records(snapshot, 'characters.mail')))}</section>
<section id="skills" role="tabpanel" aria-labelledby="tab-skills" hidden><h2>The work of your hands</h2><p class="intro">Profession and skill values, preserved as recorded.</p>{skills}<h3>Learned spell records</h3>{spells}<p class="footnote">Recipe learning is represented by spell IDs. Full recipe names, ingredients, and spell definitions require the matching client DBC data and a future adapter.</p></section>
<section id="modules" role="tabpanel" aria-labelledby="tab-modules" hidden><h2>What the modules remember</h2><p class="intro">Per-character settings from character_settings, retained without guessing their meaning.</p>{modules or '<p>No module settings were captured.</p>'}<p class="footnote">The fictional demo uses its own settings format. It does not pretend to reproduce Individual Progression's serialized payload.</p></section>
<section id="coverage" role="tabpanel" aria-labelledby="tab-coverage" hidden><h2>A transparent record</h2><p class="intro">What was captured, what was missing, and what still needs work.</p><ul class="warnings">{warnings}</ul>{coverage}<details><summary>Expected tables absent from this database ({len(snapshot['coverage']['missing_tables'])})</summary><ul>{missing}</ul></details><details><summary>Existing tables not captured ({len(snapshot['coverage']['unhandled_tables'])})</summary><ul>{unhandled}</ul></details><h3>Original captured records</h3>{raw}</section>
</div></div><footer>HEARTHKEEPER <span>First Campfire · a beginning worth keeping</span><span>Offline document · no remote assets</span></footer></main><script>{script}</script></body></html>'''
    return write_new(output_path, document.encode("utf-8"))
