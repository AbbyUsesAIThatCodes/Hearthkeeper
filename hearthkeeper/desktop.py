"""Native Qt desktop application. No web view or local HTTP server."""
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import sys
import uuid

from PySide6.QtCore import Qt, QSettings, QStandardPaths, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .client import (ClientError, LOCALES, inspect_client, realm_address_matches,
                     prepare_realmlist, start_for_play, launch_client, services_ready)
from . import CODENAME, __version__
from .archive import compare_archives, read_archive, write_archive
from .database import capture, sqlite_reader
from .demo import create_fixture
from .model import normalized, records, RACES, CLASSES
from .server.manager import ManagedRealm, RealmError, Runner, create_realm, local_docker
from .sources import (load_catalog, offerings, client_target, fetch_snapshot,
                      import_file, list_saved, verify_saved)

ASSETS = Path(__file__).parent / "assets"


def label(text, style=None):
    widget = QLabel(str(text))
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(True)
    if style:
        widget.setObjectName(style)
    return widget


def button(text, callback, primary=False):
    widget = QPushButton(text)
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(callback)
    return widget


def text_view(text=""):
    widget = QPlainTextEdit()
    widget.setReadOnly(True)
    widget.setPlainText(str(text))
    return widget


def data_table(headers, rows):
    rows = list(rows)
    widget = QTableWidget(len(rows), len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    widget.setAlternatingRowColors(True)
    widget.verticalHeader().hide()
    for index, row in enumerate(rows):
        for column, value in enumerate(row):
            widget.setItem(index, column, QTableWidgetItem(str(value)))
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    widget.horizontalHeader().setStretchLastSection(True)
    return widget


def page(title, description):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(28, 22, 28, 18)
    layout.setSpacing(15)
    layout.addWidget(label(f"{CODENAME.upper()}  /  {__version__}", "eyebrow"))
    layout.addWidget(label(title, "title"))
    layout.addWidget(label(description, "muted"))
    return widget, layout


class Worker(QThread):
    line = Signal(str)

    def __init__(self, function):
        super().__init__()
        self.function = function
        self.runner = Runner(self.line.emit)
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.function(self.runner)
        except Exception as error:
            self.error = str(error)


class RealmDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Install your realm")
        self.setMinimumWidth(630)
        layout = QVBoxLayout(self)
        layout.addWidget(label("Give your Azeroth a home", "title"))
        layout.addWidget(label("Hearthkeeper will build the pinned server and modules, create its own database, and prepare the game data you select. The first build and navigation extraction can take hours."))
        form = QFormLayout()
        self.name = QLineEdit("First Campfire")
        self.destination = QLineEdit(str(Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "Realms" / "FirstCampfire"))
        self.source = QLineEdit()
        self.kind = QComboBox()
        self.kind.addItem("Original 3.3.5a client folder (build 12340)", "client")
        self.kind.addItem("Already extracted AzerothCore server data", "prepared")
        self.xp = QSpinBox(); self.xp.setRange(1, 10); self.xp.setSuffix(" ×"); self.xp.setValue(1)
        self.bots = QSpinBox(); self.bots.setRange(0, 100); self.bots.setValue(0)
        self.jobs = QSpinBox(); self.jobs.setRange(1, 8); self.jobs.setValue(2)
        form.addRow("Realm name", self.name)
        form.addRow("New realm folder", self.picker(self.destination, new=True))
        form.addRow("Game-data format", self.kind)
        form.addRow("Game-data folder", self.picker(self.source))
        form.addRow("Quest / kill / exploration XP", self.xp)
        form.addRow("Random bots online", self.bots)
        form.addRow("Build / extraction workers", self.jobs)
        layout.addLayout(form)
        layout.addWidget(label("Docker Desktop must be running Linux containers. Allow roughly 8 GB of Docker memory and 60 GB of free space for the build, data, and future backups. Two workers keep the initial build modest; more workers use more memory.", "muted"))
        layout.addWidget(label("The selected game files are mounted read-only. Realm ports are available only on this computer. With zero random bots, you can still use your own alternate characters as companions.", "muted"))
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        install = controls.addButton("Install realm", QDialogButtonBox.ButtonRole.AcceptRole)
        install.setObjectName("primary")
        controls.accepted.connect(self.accept)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def picker(self, target, new=False):
        container = QWidget()
        row = QHBoxLayout(container); row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(target)
        def choose():
            chosen = QFileDialog.getExistingDirectory(self, "Choose parent for a new realm folder" if new else "Choose game-data folder")
            if chosen:
                target.setText(str(Path(chosen) / "FirstCampfire") if new else chosen)
        row.addWidget(button("Browse…", choose))
        return container

    def values(self):
        return {"name": self.name.text().strip(), "data_path": self.source.text().strip(),
                "data_kind": self.kind.currentData(), "xp_rate": self.xp.value(),
                "random_bots": self.bots.value(), "build_jobs": self.jobs.value()}


class AccountDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Create a realm account")
        layout = QVBoxLayout(self)
        layout.addWidget(label("An account for this private realm", "title"))
        layout.addWidget(label("This is separate from your Blizzard account. Original 3.3.5a uses account names and passwords of at most 16 characters."))
        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirmation = QLineEdit(); self.confirmation.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin = QCheckBox("Administrator (GM level 3)")
        form.addRow("Account name", self.username); form.addRow("Password", self.password)
        form.addRow("Repeat password", self.confirmation); form.addRow(self.admin)
        layout.addLayout(form)
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(self.validate); controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def validate(self):
        from .server.accounts import registration
        try:
            registration(self.username.text(), self.password.text())
            if self.password.text() != self.confirmation.text():
                raise ValueError("The passwords do not match.")
        except ValueError as error:
            QMessageBox.information(self, "Check account details", str(error))
            return
        self.accept()


class ArchivePanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        self.heading = label("Open an archive, or meet Brindle in the fictional demo.", "status")
        self.search = QLineEdit(); self.search.setPlaceholderText("Find an item, quest, skill, or ID…")
        self.search.setClearButtonEnabled(True)
        self.tabs = QTabWidget()
        self.tables = []
        self.path = None
        layout.addWidget(self.heading); layout.addWidget(self.search); layout.addWidget(self.tabs, 1)
        self.search.textChanged.connect(self.filter_rows)

    def load(self, path):
        manifest, snapshot = read_archive(path)
        model = normalized(snapshot)
        character = model["character"]
        self.path = Path(path)
        notice = "FICTIONAL DEMO · " if snapshot["source"].get("fictional_demo") else ""
        self.heading.setText(f"{notice}{character.get('name')} · Level {character.get('level')} {character['race_label']} {character['class_label']}\nChecksum verified · partial, unsigned archive")
        while self.tabs.count():
            old = self.tabs.widget(0); self.tabs.removeTab(0); old.deleteLater()
        self.tables = []
        overview = QWidget(); summary = QVBoxLayout(overview)
        summary.setContentsMargins(22, 20, 22, 20)
        summary.addWidget(label(character.get("name", "Unnamed explorer"), "title"))
        summary.addWidget(label(f"Level {character.get('level')} · {character['race_label']} {character['class_label']}", "muted"))
        copper = character.get("money", 0)
        if type(copper) is int:
            summary.addWidget(label(f"Carried wealth: {copper // 10000} gold, {(copper // 100) % 100} silver, {copper % 100} copper"))
        summary.addWidget(label(f"{len(model['items'])} item records · {len(model['skills'])} skills · {len(model['module_settings'])} module records"))
        summary.addWidget(label("Recorded on " + manifest["created_utc"] + "\nRealm: " + snapshot["source"]["realm"], "muted"))
        summary.addWidget(label("This partial archive keeps the original captured records. Coverage explains missing data. A checksum detects damage; it does not prove authorship or guarantee restoration.", "status"))
        summary.addStretch()
        self.tabs.addTab(overview, "Overview")
        self.add_table("Equipment && bags", ["Item", "Location", "Count", "ID"],
            ([item["name"], item["location"], item["count"], item["entry"]] for item in model["items"]))
        quests = {row["ID"]: row for row in records(snapshot, "world.quest_template")}
        quest_rows = []
        for name, status in (("character_queststatus", "In quest log"), ("character_queststatus_rewarded", "Rewarded")):
            for row in records(snapshot, "characters." + name):
                quest_rows.append([quests.get(row["quest"], {}).get("LogTitle", "Unknown quest"), status, row["quest"]])
        self.add_table("Journal", ["Quest", "Status", "ID"], quest_rows)
        self.add_table("Skills", ["Skill", "Current", "Maximum"],
            ([row["name"], row.get("value"), row.get("max")] for row in model["skills"]))
        self.tabs.addTab(text_view(json.dumps(model["module_settings"], indent=2, ensure_ascii=False)), "Module data")
        self.tabs.addTab(text_view(json.dumps({"warnings": snapshot["warnings"], **snapshot["coverage"],
            "captured_tables": {name: len(table["rows"]) for name, table in snapshot["tables"].items()}}, indent=2)), "Coverage")
        self.tabs.addTab(text_view(json.dumps(snapshot["tables"], indent=2, ensure_ascii=False)), "Original records")
        self.search.clear()

    def add_table(self, name, headers, rows):
        table = data_table(headers, rows)
        self.tables.append(table)
        self.tabs.addTab(table, name)

    def filter_rows(self, text):
        for table in self.tables:
            for row in range(table.rowCount()):
                words = " ".join(table.item(row, column).text() for column in range(table.columnCount()))
                table.setRowHidden(row, text.casefold() not in words.casefold())


class MainWindow(QMainWindow):
    def __init__(self, *, remember=True):
        super().__init__()
        self.setWindowTitle(f"Hearthkeeper · {CODENAME} {__version__}")
        self.setWindowIcon(QIcon(str(ASSETS / "hearthkeeper.svg")))
        self.resize(1240, 880); self.setMinimumSize(980, 700)
        self.preferences = QSettings("Hearthkeeper", "Desktop") if remember else None
        self.realm_path = None
        self.pending_path = None
        self.worker = None
        self.actions = []
        self.client_choices = {}
        self.client = None
        self.game_process = None
        self.game_realm_path = None
        self.operation_title = ""
        self.pages = QStackedWidget()
        root = QWidget(); root.setObjectName("root"); root_layout = QHBoxLayout(root); root_layout.setContentsMargins(0, 0, 0, 0); root_layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(212)
        navigation = QVBoxLayout(sidebar); navigation.setContentsMargins(18, 28, 18, 22); navigation.setSpacing(9)
        emblem = QLabel(); emblem.setPixmap(QIcon(str(ASSETS / "hearthkeeper.svg")).pixmap(64, 64))
        navigation.addWidget(emblem)
        brand = label("Hearthkeeper", "brand")
        navigation.addWidget(brand)
        brand.ensurePolished()
        sidebar.setFixedWidth(max(212, brand.fontMetrics().horizontalAdvance(brand.text()) + 44))
        navigation.addWidget(label("YOUR OWN AZEROTH", "brandSub")); navigation.addSpacing(28)
        self.nav_buttons = []
        for index, title in enumerate(("Home", "Characters", "Archives", "Backups", "Sources", "Workshop")):
            item = QPushButton(title); item.setObjectName("nav"); item.setCheckable(True)
            item.setIcon(QIcon(str(ASSETS / ("nav-" + ("home", "characters", "archives", "backups", "sources", "workshop")[index] + ".svg"))))
            item.clicked.connect(lambda checked=False, index=index: self.navigate(index))
            navigation.addWidget(item); self.nav_buttons.append(item)
        navigation.addStretch()
        navigation.addWidget(label(CODENAME + "\n" + __version__, "brandSub"))
        navigation.addWidget(button("Desktop shortcut", self.shortcut))
        root_layout.addWidget(sidebar)
        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(self.pages)
        activity = QWidget(); activity_layout = QVBoxLayout(activity); activity_layout.setContentsMargins(18, 5, 18, 12)
        activity_row = QHBoxLayout(); activity_row.addWidget(label("ACTIVITY", "eyebrow")); activity_row.addStretch()
        self.stop_step = button("Stop after current step", self.request_stop); self.stop_step.setEnabled(False)
        activity_row.addWidget(self.stop_step); activity_layout.addLayout(activity_row)
        self.progress = QProgressBar(); self.progress.setRange(0, 1); self.progress.setValue(0); self.progress.setTextVisible(False)
        activity_layout.addWidget(self.progress)
        self.activity = text_view("Welcome. Opening Hearthkeeper does not start a server or install anything.")
        self.activity.setObjectName("activity"); self.activity.document().setMaximumBlockCount(1800)
        activity_layout.addWidget(self.activity)
        right.addWidget(activity); right.setSizes([740, 100]); root_layout.addWidget(right, 1)
        self.setCentralWidget(root)
        self.build_realm_page(); self.build_characters_page(); self.build_archives_page(); self.build_backups_page(); self.build_sources_page(); self.build_workshop_page()
        self.navigate(0)
        if self.preferences:
            recent = self.preferences.value("last_realm", "")
            if recent and (Path(recent) / "realm.json").is_file():
                try:
                    self.select_realm(recent)
                except Exception as error:
                    self.activity.appendPlainText("Could not reopen the previous realm: " + str(error))

    def action(self, text, callback, primary=False):
        result = button(text, callback, primary)
        self.actions.append(result)
        return result

    def build_realm_page(self):
        content = QWidget()
        layout = QVBoxLayout(content); layout.setContentsMargins(24, 20, 24, 20); layout.setSpacing(16)
        hero = QFrame(); hero.setObjectName("hero"); hero.setMinimumHeight(218)
        inside = QVBoxLayout(hero); inside.setContentsMargins(28, 24, 28, 24)
        inside.addWidget(label("WRATH OF THE LICH KING", "eyebrow"))
        inside.addWidget(label("Your next adventure\nbegins here.", "heroTitle"))
        inside.addWidget(label("A familiar world. A hearth of your own.", "heroSubtitle"))
        inside.addStretch(); layout.addWidget(hero)
        cards = QHBoxLayout(); cards.setSpacing(12); self.card_values = []
        for title, value in (("YOUR REALM", "Choose a realm"), ("INSTALLATION", "Not selected"), ("SERVICES", "Not checked")):
            card = QFrame(); card.setObjectName("card"); inside = QVBoxLayout(card); inside.setContentsMargins(16, 13, 16, 13)
            inside.addWidget(label(title, "cardTitle")); item = label(value, "cardValue"); inside.addWidget(item)
            cards.addWidget(card, 1); self.card_values.append(item)
        layout.addLayout(cards)
        self.realm_notice = label("Open your existing realm, or create a new home for your adventures.", "muted")
        layout.addWidget(self.realm_notice)
        row = QHBoxLayout()
        row.addWidget(self.action("Open realm…", self.open_realm)); row.addWidget(self.action("New realm…", self.new_realm))
        row.addStretch(); layout.addLayout(row)
        parchment = QFrame(); parchment.setObjectName("parchment")
        inside = QVBoxLayout(parchment); inside.setContentsMargins(20, 16, 20, 16); inside.setSpacing(10)
        inside.addWidget(label("YOUR GAME INSTALLATION", "eyebrow"))
        self.client_title = label("Bring your adventurer home", "clientTitle"); inside.addWidget(self.client_title)
        self.client_notice = label("Choose your original Wrath client: Wow.exe, version 3.3.5a / build 12340.")
        self.client_notice.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        inside.addWidget(self.client_notice)
        row = QHBoxLayout()
        self.choose_client_button = self.action("Choose Wow.exe…", self.choose_client)
        self.connect_client_button = self.action("Connect to this realm", self.connect_client)
        row.addWidget(self.choose_client_button); row.addWidget(self.connect_client_button); row.addStretch(); inside.addLayout(row)
        layout.addWidget(parchment)
        row = QHBoxLayout()
        self.play_button = self.action("PLAY", self.play); self.play_button.setObjectName("play")
        self.play_button.setMinimumWidth(180)
        row.addWidget(self.play_button)
        self.play_notice = label("Open or create a realm to begin.", "muted"); row.addWidget(self.play_notice, 1)
        layout.addLayout(row)
        shortcuts = QGridLayout()
        shortcuts.addWidget(button("Characters && accounts", lambda: self.navigate(1)), 0, 0)
        shortcuts.addWidget(button("Companion guide", self.companion_guide), 0, 1)
        shortcuts.addWidget(button("Realm backups", lambda: self.navigate(3)), 1, 0)
        layout.addLayout(shortcuts)
        tools_toggle = button("Realm tools ▸", lambda: None); tools_toggle.setCheckable(True)
        layout.addWidget(tools_toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        tools = QWidget(); tools.setObjectName("realmTools")
        tool_layout = QGridLayout(tools); tool_layout.setContentsMargins(0, 0, 0, 0)
        actions = [
            ("Install / Resume", lambda: self.realm_job("Installing realm", lambda realm: realm.install())),
            ("Start realm", lambda: self.realm_job("Starting realm", lambda realm: realm.start())),
            ("Stop realm", lambda: self.realm_job("Stopping realm", lambda realm: realm.stop())),
            ("Refresh status", self.refresh_status),
            ("Realm settings…", self.realm_settings),
            ("Check Docker", self.prerequisites),
            ("Server logs", lambda: self.realm_job("Reading server logs", lambda realm: realm.compose("logs", "--tail", "120", "auth", "world"))),
        ]
        for index, (title, callback) in enumerate(actions):
            tool_layout.addWidget(self.action(title, callback), index // 2, index % 2)
        tools.hide(); layout.addWidget(tools)
        tools_toggle.toggled.connect(tools.setVisible)
        tools_toggle.toggled.connect(lambda checked: tools_toggle.setText("Realm tools ▾" if checked else "Realm tools ▸"))
        self.realm_tools_toggle = tools_toggle
        layout.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(content)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pages.addWidget(scroll)
        self.update_play_state()

    def client_key(self):
        return "game_clients/" + hashlib.sha256(str(self.realm_path).encode("utf-8")).hexdigest()

    def load_client_choice(self):
        self.client = None
        if not self.realm_path:
            return
        key = self.client_key()
        choice = self.preferences.value(key, "") if self.preferences else self.client_choices.get(key, "")
        if choice:
            try:
                value = json.loads(choice)
                self.client = inspect_client(value["executable"], value["locale"])
            except (ValueError, KeyError, OSError, TypeError) as error:
                self.client_notice.setText("Choose the game again: " + str(error))
                self.client_title.setText("Installation needs attention")

    def choose_client(self):
        if not self.realm_path:
            QMessageBox.information(self, "Choose a realm", "Open or create a realm first. The game selection is saved for that realm.")
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Choose the original Wow.exe", "", "World of Warcraft (Wow.exe wow.exe)")
        if not filename:
            return
        try:
            available = [name for name in LOCALES if (Path(filename).parent / "Data" / name).is_dir()]
            locale = available[0] if len(available) == 1 else None
            if len(available) > 1:
                locale, accepted = QInputDialog.getItem(self, "Game language", "Select the language you use in this installation", available, 0, False)
                if not accepted:
                    return
            client = inspect_client(filename, locale)
            self.client = client
            choice = json.dumps({"executable": str(client.executable), "locale": client.locale})
            if self.preferences:
                self.preferences.setValue(self.client_key(), choice)
            else:
                self.client_choices[self.client_key()] = choice
        except (ClientError, OSError) as error:
            QMessageBox.warning(self, "Check the game installation", str(error))
        self.update_play_state()

    def connect_client(self):
        if not self.client:
            return
        try:
            self.client = inspect_client(self.client.executable, self.client.locale)
            if not realm_address_matches(self.client):
                message = ("Connect this game installation to 127.0.0.1?\n\n" + str(self.client.realmlist) +
                           "\n\nThe existing file will be saved beside it with a dated .bak name before the connection is changed. Other realms using this game installation share this setting.")
                if QMessageBox.question(self, "Connect your game", message) != QMessageBox.StandardButton.Yes:
                    return
                backup = prepare_realmlist(self.client)
                self.activity.appendPlainText("Local connection prepared." + (" Previous file: " + str(backup) if backup else ""))
        except (ClientError, OSError) as error:
            QMessageBox.warning(self, "Could not connect the game", str(error))
        self.update_play_state()

    def update_play_state(self):
        if not hasattr(self, "play_button"):
            return
        busy = self.worker is not None
        phase, realm_error = None, None
        if self.realm_path:
            try:
                phase = ManagedRealm(self.realm_path).config["phase"]
            except (ValueError, KeyError, OSError, RealmError) as error:
                realm_error = str(error)
        running = self.game_process is not None and self.game_process.poll() is None
        self.choose_client_button.setEnabled(not busy and not running and self.realm_path is not None)
        connected = self.client is not None and realm_address_matches(self.client)
        self.connect_client_button.setEnabled(not busy and not running and self.client is not None and not connected)
        self.connect_client_button.setText("Connected locally" if connected else "Connect to this realm")
        self.play_button.setEnabled(False)
        if self.client:
            self.client_title.setText("Wrath of the Lich King · 3.3.5a")
            location = str(self.client.executable.parent)
            self.client_notice.setText("Build 12340 · " + self.client.locale + "\n" + (location if len(location) < 90 else "…" + location[-87:]))
            self.client_notice.setToolTip(location)
        if busy:
            self.play_notice.setText(self.operation_title + " · See Activity for progress.")
        elif running:
            self.play_notice.setText("WoW is running. Return to the game to continue your adventure.")
        elif not self.realm_path:
            self.play_notice.setText("Open or create a realm to begin.")
        elif realm_error:
            self.play_notice.setText("Reopen the realm: " + realm_error)
        elif phase != "installed":
            self.play_notice.setText("Finish the realm installation in Realm tools → Install / Resume.")
        elif not self.client:
            self.play_notice.setText("Choose your matching Wow.exe to unlock Play." if os.name == "nt" else "Game launching is available on Windows. Realm tools remain available here.")
        elif not realm_address_matches(self.client):
            self.play_notice.setText("Connect this game installation to the local realm to unlock Play.")
        else:
            self.play_button.setEnabled(True)
            self.play_notice.setText("Start the realm if needed, then open WoW. Sign in with your realm account.")
        self.play_button.setText("GAME RUNNING" if running else "PLAY")
        self.play_button.setToolTip(self.play_notice.text())

    def play(self):
        if not self.client or not self.realm_path or self.worker:
            return
        if self.game_process is not None and self.game_process.poll() is None:
            return
        path, client = self.realm_path, self.client
        def launch(verified):
            self.game_process = launch_client(verified)
            self.game_realm_path = path
            self.card_values[2].setText("Ready at " + datetime.now().strftime("%H:%M"))
            self.activity.appendPlainText("WoW launched. Sign in with your realm account. Closing Hearthkeeper leaves the realm running.")
            from PySide6.QtCore import QTimer
            if not hasattr(self, "game_timer"):
                self.game_timer = QTimer(self); self.game_timer.setInterval(1500)
                self.game_timer.timeout.connect(self.game_tick)
            self.game_timer.start()
            self.update_play_state()
        self.run_job("Preparing your adventure", lambda runner: start_for_play(ManagedRealm(path, runner), client.executable, client.locale), launch, cancel_callback_on_stop=True)

    def game_tick(self):
        if self.game_process is not None and self.game_process.poll() is not None:
            exit_code = self.game_process.returncode
            self.activity.appendPlainText("WoW closed." if exit_code == 0 else "WoW exited with code " + str(exit_code) + ". Check the game installation if it closed unexpectedly.")
            self.game_process = None
            self.game_timer.stop()
            self.update_play_state()

    def companion_guide(self):
        dialog = QDialog(self); dialog.setWindowTitle("Your adventuring company"); dialog.resize(610, 420)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label("Bring a companion", "title"))
        layout.addWidget(label("Playerbots is included in the managed Wrath realm. Zero random bots still allows your own alternate characters to join you."))
        layout.addWidget(text_view("1. Create another Alliance character on your account.\n2. Return to your main character.\n3. Replace CompanionName below with the character's name:\n\n.playerbots bot add CompanionName\n/invite CompanionName\n\n/p follow    — follow you\n/p stay      — hold position\n/p attack    — attack your target\n/p help      — available commands"))
        layout.addWidget(label("MultiBot adds in-game controls. Browsing and installing addons from Hearthkeeper is planned.", "muted"))
        row = QDialogButtonBox(QDialogButtonBox.StandardButton.Close); row.rejected.connect(dialog.reject); layout.addWidget(row)
        dialog.exec()

    def build_characters_page(self):
        widget, layout = page("The people of your realm", "Create local game accounts and preserve a character after logging it out.")
        row = QHBoxLayout(); row.addWidget(self.action("Create account…", self.new_account, True))
        row.addWidget(self.action("Load characters", self.load_characters)); row.addWidget(self.action("Archive selected", self.capture_selected)); row.addStretch()
        layout.addLayout(row)
        self.characters = data_table(["GUID", "Name", "Level", "Race", "Class", "Online"], [])
        layout.addWidget(self.characters, 1)
        layout.addWidget(label("Capture uses a SELECT-only database identity. The archive preserves supported rows and reports coverage; it does not yet restore characters.", "muted"))
        self.pages.addWidget(widget)

    def build_archives_page(self):
        widget, layout = page("Your adventures, kept close", "Character records remain readable here while the realm is asleep.")
        row = QHBoxLayout(); row.addWidget(button("Open archive…", self.open_archive, True)); row.addWidget(button("Meet Brindle · demo", self.demo))
        row.addWidget(button("Compare snapshots…", self.compare)); row.addStretch(); layout.addLayout(row)
        self.archive_panel = ArchivePanel(); layout.addWidget(self.archive_panel, 1)
        self.pages.addWidget(widget)

    def build_backups_page(self):
        widget, layout = page("Keep a way back", "Save the realm databases, settings, credentials, and source identities together.")
        layout.addWidget(label("Backup stops auth and world so character state can be saved. They remain stopped afterward. Game assets and Docker images are not included; restoration tooling and recovery testing are still to come.", "status"))
        row = QHBoxLayout(); row.addWidget(self.action("Stop realm & back up", self.make_backup, True))
        row.addWidget(button("Open backup folder", self.open_backups)); row.addStretch(); layout.addLayout(row)
        self.backup_list = text_view("No realm selected."); layout.addWidget(self.backup_list, 1)
        layout.addWidget(label("Backups contain private data and local credentials. They are not encrypted. Keep another copy outside the realm's drive.", "muted"))
        self.pages.addWidget(widget)

    def build_workshop_page(self):
        widget, layout = page("A place of your own", "The future workshop will share this desktop home with your realm and archives.")
        for title, description in (("A town to come home to", "Place a small original settlement on existing terrain, with vendors, dialogue, and quests."),
                                   ("An instance worth mastering", "Design encounters, objectives, loot, and resets using an established asset pipeline."),
                                   ("A region beyond the map", "Shape terrain and travel routes, with matching client assets, collision, and navigation data.")):
            card = QFrame(); card.setObjectName("card"); inside = QVBoxLayout(card); inside.setContentsMargins(20, 18, 20, 18)
            inside.addWidget(label(title, "cardValue")); inside.addWidget(label(description, "muted")); layout.addWidget(card)
        layout.addWidget(label("PLANNED · Authoring tools are not implemented in this preview. Content packs will record identity, version, dependencies, and compatibility so future archives can understand your custom world.", "status"))
        layout.addStretch(); self.pages.addWidget(widget)

    def build_sources_page(self):
        widget, layout = page("A library of Azeroths", "Browse providers, preserve source revisions, and keep downloaded clients and databases together.")
        layout.setSpacing(9)
        self.source_catalog = load_catalog()
        self.source_entries = {entry["id"]: entry for entry in self.source_catalog["offerings"]}
        default_root = str(Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "SourceArchive")
        self.source_root = Path(self.preferences.value("source_archive", default_root) if self.preferences else default_root)
        row = QHBoxLayout()
        self.source_location = label(str(self.source_root), "muted")
        row.addWidget(self.source_location, 1)
        row.addWidget(self.action("Archive location…", self.choose_source_location))
        layout.addLayout(row)
        self.source_tabs = QTabWidget()
        catalog_page = QWidget(); inside = QVBoxLayout(catalog_page)
        filters = QHBoxLayout()
        self.source_provider = QComboBox(); self.source_provider.addItem("All sources", "")
        for provider in self.source_catalog["providers"]:
            self.source_provider.addItem(provider["name"], provider["id"])
        self.source_era = QComboBox(); self.source_era.addItem("All eras", "")
        for era in dict.fromkeys(entry["era"] for entry in self.source_catalog["offerings"]):
            self.source_era.addItem(era, era)
        self.source_search = QLineEdit(); self.source_search.setPlaceholderText("Find a client, core, or build…")
        self.source_search.setClearButtonEnabled(True)
        filters.addWidget(self.source_provider); filters.addWidget(self.source_era); filters.addWidget(self.source_search, 1)
        inside.addLayout(filters)
        self.source_tree = QTreeWidget()
        self.source_tree.setHeaderLabels(["Source / offering", "Type", "Client version", "Obtain"])
        self.source_tree.setAlternatingRowColors(True)
        self.source_tree.setColumnWidth(0, 280); self.source_tree.setColumnWidth(1, 125); self.source_tree.setColumnWidth(2, 125)
        self.source_tree.setMinimumHeight(130)
        inside.addWidget(self.source_tree, 1)
        self.source_summary = label("", "muted")
        inside.addWidget(self.source_summary)
        self.source_detail_text = ""
        controls = QHBoxLayout()
        self.source_detail_button = button("Details…", self.show_source_details)
        self.source_open = self.action("Source page", self.open_source_page)
        self.source_fetch = self.action("Save snapshot", self.fetch_source, True)
        self.source_import = self.action("Import file…", self.import_source_file)
        for action in (self.source_detail_button, self.source_open, self.source_fetch, self.source_import):
            controls.addWidget(action)
        controls.addStretch(); inside.addLayout(controls)
        self.source_tabs.addTab(catalog_page, "Catalog")
        saved_page = QWidget(); saved = QVBoxLayout(saved_page)
        saved.addWidget(label("Saved copies preserve files and provenance. Verification checks that their bytes still match; it does not certify a client build or a playable realm.", "muted"))
        self.source_saved = data_table(["Offering", "Saved (UTC)", "Size", "Acquisition"], [])
        saved.addWidget(self.source_saved, 1)
        self.source_saved_notice = label("", "muted"); saved.addWidget(self.source_saved_notice)
        controls = QHBoxLayout()
        controls.addWidget(self.action("Verify selected copy", self.verify_source_copy, True))
        controls.addWidget(button("Open selected folder", self.open_source_copy))
        controls.addWidget(button("Refresh", self.refresh_source_copies)); controls.addStretch()
        saved.addLayout(controls); self.source_tabs.addTab(saved_page, "Saved copies")
        layout.addWidget(self.source_tabs, 1)
        layout.addWidget(label("Catalog preview · Realm installation still uses the pinned Wrath setup.", "muted"))
        self.pages.addWidget(widget)
        self.source_tree.currentItemChanged.connect(self.source_selection)
        self.source_provider.currentIndexChanged.connect(self.filter_sources)
        self.source_era.currentIndexChanged.connect(self.filter_sources)
        self.source_search.textChanged.connect(self.filter_sources)
        self.filter_sources()
        self.refresh_source_copies()

    def filter_sources(self):
        self.source_tree.clear()
        matches = offerings(self.source_catalog, provider=self.source_provider.currentData(),
                            era=self.source_era.currentData(), query=self.source_search.text().strip())
        first = None
        for provider in self.source_catalog["providers"]:
            entries = [entry for entry in matches if entry["provider"] == provider["id"]]
            if not entries:
                continue
            group = QTreeWidgetItem([provider["name"], "", "", ""])
            group.setToolTip(0, provider["description"])
            self.source_tree.addTopLevelItem(group)
            for entry in entries:
                item = QTreeWidgetItem([entry["name"], entry["kind"], entry["client"]["version"],
                                       "Reference" if entry.get("availability") else
                                       "Source snapshot" if entry["acquisition"] == "github_snapshot" else "Download page"])
                item.setData(0, Qt.ItemDataRole.UserRole, entry["id"])
                for column in range(4):
                    item.setToolTip(column, client_target(entry) + "\n" + entry["notes"])
                group.addChild(item)
                first = first or item
            group.setExpanded(bool(self.source_provider.currentData() or self.source_search.text()
                                   or self.source_era.currentData() or provider["id"] == "chromiecraft"))
        if first:
            self.source_tree.setCurrentItem(first)
        self.source_selection()

    def selected_source(self):
        item = self.source_tree.currentItem()
        return self.source_entries.get(item.data(0, Qt.ItemDataRole.UserRole)) if item else None

    def source_selection(self, *_):
        entry = self.selected_source()
        active = bool(entry) and not self.worker
        self.source_open.setEnabled(active)
        self.source_import.setEnabled(active)
        self.source_fetch.setEnabled(active and entry["acquisition"] == "github_snapshot")
        self.source_detail_button.setEnabled(bool(entry))
        if not entry:
            self.source_summary.setText("Choose an offering beneath a source, or clear the filters.")
            self.source_detail_text = ""
            return
        self.source_summary.setText(client_target(entry) + "\n" +
            (entry.get("availability") or entry["gameplay"]) + " · See Details.")
        self.source_detail_text = (
            f"{entry['name']}\n{entry['era']} · {client_target(entry)}\n"
            f"Installation: {entry['installation']} · Gameplay: {entry['gameplay']}\n"
            f"Source page reviewed: {entry['reviewed_on']}\n\n{entry['notes']}\n\n{entry['page_url']}")

    def show_source_details(self):
        if not self.selected_source():
            return
        dialog = QDialog(self); dialog.setWindowTitle("Source offering details"); dialog.resize(650, 380)
        layout = QVBoxLayout(dialog); layout.addWidget(text_view(self.source_detail_text))
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(dialog.reject); layout.addWidget(close)
        dialog.exec()

    def choose_source_location(self):
        path = QFileDialog.getExistingDirectory(self, "Choose where to preserve source copies", str(self.source_root))
        if path:
            self.source_root = Path(path)
            self.source_location.setText(str(self.source_root))
            if self.preferences:
                self.preferences.setValue("source_archive", str(self.source_root))
            self.refresh_source_copies()

    def open_source_page(self):
        entry = self.selected_source()
        if entry:
            QDesktopServices.openUrl(QUrl(entry["page_url"]))

    def fetch_source(self):
        entry = self.selected_source()
        if not entry or entry["acquisition"] != "github_snapshot":
            return
        root = self.source_root
        self.run_job("Saving " + entry["name"],
            lambda runner: fetch_snapshot(entry, root, stop=runner.stop_after_step, log=runner.log), self.source_saved_complete)

    def import_source_file(self):
        entry = self.selected_source()
        if not entry:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Choose a completed download to copy into the source archive")
        if not path:
            return
        root = self.source_root
        self.run_job("Archiving downloaded file for " + entry["name"],
            lambda runner: import_file(entry, path, root, stop=runner.stop_after_step, log=runner.log), self.source_saved_complete)

    def source_saved_complete(self, destination):
        self.activity.appendPlainText("Source copy saved: " + str(destination))
        self.refresh_source_copies()
        self.source_tabs.setCurrentIndex(1)
        for row, (path, _) in enumerate(self.source_copies):
            if path == destination:
                self.source_saved.selectRow(row)
                break

    def refresh_source_copies(self):
        self.source_copies, errors = list_saved(self.source_root)
        self.source_saved.setRowCount(len(self.source_copies))
        for row, (path, manifest) in enumerate(self.source_copies):
            values = [manifest["offering"]["name"], manifest["saved_utc"][:19].replace("T", " "),
                      f"{manifest['payload']['bytes'] / (1024 ** 2):,.1f} MiB",
                      "Source snapshot" if manifest["acquisition"]["method"] == "github_snapshot" else "Imported file"]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value); item.setToolTip(str(path))
                self.source_saved.setItem(row, column, item)
        self.source_saved_notice.setText(f"{len(self.source_copies)} saved copies. " +
            (f"{len(errors)} unreadable entries; see Activity." if errors else "Choose a copy to verify its recorded checksum."))
        if errors:
            self.activity.appendPlainText("\n".join(errors))

    def selected_source_copy(self):
        row = self.source_saved.currentRow()
        return self.source_copies[row][0] if 0 <= row < len(self.source_copies) else None

    def verify_source_copy(self):
        path = self.selected_source_copy()
        if path:
            self.run_job("Checking saved copy", lambda runner: verify_saved(path, stop=runner.stop_after_step),
                         lambda result: QMessageBox.information(self, "Saved-copy verification", result))

    def open_source_copy(self):
        path = self.selected_source_copy()
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def navigate(self, index):
        self.pages.setCurrentIndex(index)
        for number, item in enumerate(self.nav_buttons):
            item.setChecked(number == index)

    def select_realm(self, path):
        realm = ManagedRealm(path)
        self.realm_path = realm.path
        if self.preferences:
            self.preferences.setValue("last_realm", str(realm.path))
        self.card_values[0].setText(realm.config["name"])
        self.card_values[1].setText("Installed" if realm.config["phase"] == "installed" else realm.config["phase"].replace("-", " ").capitalize())
        self.card_values[2].setText("Not checked")
        self.realm_notice.setText("THIS COMPUTER · Local realm · Wrath 3.3.5a / 12340")
        self.realm_notice.setToolTip(str(realm.path))
        self.client_title.setText("Bring your adventurer home")
        self.client_notice.setText("Choose your original Wrath client: Wow.exe, version 3.3.5a / build 12340.")
        self.load_client_choice()
        self.update_play_state()
        backups = sorted((realm.path / "backups").glob("*/manifest.json"), reverse=True)
        self.backup_list.setPlainText("\n".join(str(path.parent) for path in backups) or "No completed backups yet.")

    def run_job(self, title, function, callback=None, *, cancel_callback_on_stop=False):
        if self.worker:
            QMessageBox.information(self, "Operation in progress", "Let the current operation finish first.")
            return
        self.operation_title = title
        self.activity.appendPlainText("\n" + title)
        self.worker = Worker(function)
        worker = self.worker
        worker.cancel_callback_on_stop = cancel_callback_on_stop
        worker.line.connect(self.activity.appendPlainText)
        worker.finished.connect(lambda: self.job_finished(worker, callback))
        for action in self.actions:
            action.setEnabled(False)
        self.progress.setRange(0, 0)
        self.stop_step.setEnabled(True)
        self.update_play_state()
        worker.start()

    def job_finished(self, worker, callback):
        self.worker = None
        self.progress.setRange(0, 1); self.progress.setValue(1)
        self.stop_step.setEnabled(False)
        for action in self.actions:
            action.setEnabled(True)
        self.source_selection()
        try:
            path = self.pending_path or self.realm_path
            if path and (Path(path) / "realm.json").is_file():
                self.select_realm(path)
            self.pending_path = None
            if worker.error:
                self.activity.appendPlainText("NEEDS ATTENTION · " + worker.error)
                self.card_values[2].setText("Check activity")
                QMessageBox.warning(self, "Operation needs attention", worker.error)
            elif worker.cancel_callback_on_stop and worker.runner.stop_after_step.is_set():
                self.activity.appendPlainText("Game launch cancelled. The realm may still be running.")
            elif callback:
                callback(worker.result)
            elif worker.result is not None:
                self.activity.appendPlainText(str(worker.result))
        except Exception as error:
            self.activity.appendPlainText(str(error))
            QMessageBox.warning(self, "Operation needs attention", str(error))
        self.update_play_state()
        worker.deleteLater()

    def request_stop(self):
        if self.worker:
            self.worker.runner.stop_after_step.set()
            self.stop_step.setEnabled(False)
            self.activity.appendPlainText("Will stop after the current command finishes. Database imports and extraction are not interrupted mid-command.")

    def realm_job(self, title, operation, callback=None):
        if not self.realm_path:
            QMessageBox.information(self, "Choose a realm", "Create or open a Hearthkeeper realm first.")
            return
        path = self.realm_path
        self.run_job(title, lambda runner: operation(ManagedRealm(path, runner)), callback)

    def prerequisites(self):
        self.run_job("Checking local Docker prerequisites", local_docker,
            lambda result: QMessageBox.information(self, "Docker is ready", f"Local Linux context: {result['context']}\nMemory available to Docker: {result['memory_gib']} GiB\nSupply matching game files and check available disk space before installing."))

    def new_realm(self):
        dialog = RealmDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        destination = Path(dialog.destination.text()).resolve()
        values = dialog.values()
        if destination.exists():
            QMessageBox.information(self, "Choose a new folder", "That destination already exists. Open it as a realm to resume, or choose a new folder.")
            return
        self.pending_path = destination
        self.realm_notice.setText("Installing in " + str(destination))
        def install(runner):
            prerequisites = local_docker(runner)
            realm = create_realm(destination, docker_context=prerequisites["context"], **values)
            realm.runner = runner; runner.redactions = list(realm.config["secrets"].values())
            realm.install()
            return "Installation completed. Create an account on Characters, then Start realm."
        self.run_job("Installing your progression realm", install)

    def open_realm(self):
        path = QFileDialog.getExistingDirectory(self, "Open the folder containing realm.json")
        if path:
            try:
                self.select_realm(path)
            except Exception as error:
                QMessageBox.warning(self, "Could not open realm", str(error))

    def refresh_status(self):
        def display(rows):
            self.card_values[2].setText("Ready at " + datetime.now().strftime("%H:%M") if services_ready(rows) else "Not ready at " + datetime.now().strftime("%H:%M"))
            self.activity.appendPlainText("\n".join(row.get("Service", "?") + ": " + row.get("State", "?") + " " + row.get("Health", "") for row in rows) or "No services created")
        self.realm_job("Reading service status", lambda realm: realm.status(), display)

    def new_account(self):
        if not self.realm_path:
            QMessageBox.information(self, "Choose a realm", "Install or open a realm first.")
            return
        dialog = AccountDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username, password, administrator = dialog.username.text(), dialog.password.text(), dialog.admin.isChecked()
            dialog.password.clear(); dialog.confirmation.clear()
            self.realm_job("Creating a local game account", lambda realm: realm.create_account(username, password, administrator))

    def load_characters(self):
        def display(rows):
            self.characters.setRowCount(len(rows))
            for index, row in enumerate(rows):
                values = [row["guid"], row["name"], row["level"], RACES.get(row["race"], row["race"]),
                          CLASSES.get(row["class"], row["class"]), "Yes" if row["online"] else "No"]
                for column, value in enumerate(values):
                    self.characters.setItem(index, column, QTableWidgetItem(str(value)))
        self.realm_job("Loading character list", lambda realm: realm.list_characters(), display)

    def capture_selected(self):
        row = self.characters.currentRow()
        if row < 0:
            QMessageBox.information(self, "Choose a character", "Load characters and select one to archive.")
            return
        guid = int(self.characters.item(row, 0).text())
        self.realm_job("Capturing the selected character", lambda realm: realm.capture(guid), self.show_archive)

    def show_archive(self, path):
        self.archive_panel.load(path); self.navigate(2)

    def open_archive(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open character archive", "", "Hearthkeeper archives (*.hearth)")
        if path:
            try:
                self.show_archive(path)
            except Exception as error:
                QMessageBox.warning(self, "Could not read archive", str(error))

    def demo(self):
        root = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "Demos" / uuid.uuid4().hex
        try:
            database = create_fixture(root / "fictional.sqlite")
            with sqlite_reader(database) as reader:
                snapshot = capture(reader, 7, "copperleaf-demo", demo=True)
            self.show_archive(write_archive(root / "brindle.hearth", snapshot))
        except Exception as error:
            QMessageBox.warning(self, "Demo needs attention", str(error))

    def compare(self):
        first, _ = QFileDialog.getOpenFileName(self, "Choose earlier snapshot", "", "Hearthkeeper archives (*.hearth)")
        if not first:
            return
        second, _ = QFileDialog.getOpenFileName(self, "Choose later snapshot", "", "Hearthkeeper archives (*.hearth)")
        if not second:
            return
        try:
            comparison = compare_archives(first, second)
            dialog = QDialog(self); dialog.setWindowTitle("Snapshot comparison"); dialog.resize(700, 500)
            layout = QVBoxLayout(dialog); layout.addWidget(text_view(json.dumps(comparison, indent=2))); dialog.exec()
        except Exception as error:
            QMessageBox.warning(self, "Cannot compare snapshots", str(error))

    def make_backup(self):
        if QMessageBox.question(self, "Stop and back up?", "This will stop auth and world, save the databases and configuration, and leave gameplay stopped. Continue?") == QMessageBox.StandardButton.Yes:
            self.realm_job("Backing up the realm", lambda realm: realm.backup())

    def open_backups(self):
        if self.realm_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.realm_path / "backups")))

    def realm_settings(self):
        if not self.realm_path:
            QMessageBox.information(self, "Choose a realm", "Create or open a realm first."); return
        config = ManagedRealm(self.realm_path).config
        dialog = QDialog(self); dialog.setWindowTitle("Realm settings")
        layout = QVBoxLayout(dialog); layout.addWidget(label("Stop the realm before changing these settings. Changes apply on the next start."))
        form = QFormLayout(); xp = QSpinBox(); xp.setRange(1, 10); xp.setValue(config["xp_rate"])
        bots = QSpinBox(); bots.setRange(0, 100); bots.setValue(config["random_bots"])
        form.addRow("XP multiplier", xp); form.addRow("Random bots online", bots); layout.addLayout(form)
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(dialog.accept); controls.rejected.connect(dialog.reject); layout.addWidget(controls)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_xp, new_bots = xp.value(), bots.value()
            self.realm_job("Updating realm settings", lambda realm: realm.update_settings(new_xp, new_bots))

    def shortcut(self):
        from .shortcuts import create_shortcut
        try:
            path = create_shortcut()
            QMessageBox.information(self, "Desktop shortcut created", str(path))
        except Exception as error:
            QMessageBox.information(self, "Desktop shortcut", str(error))

    def closeEvent(self, event):
        if self.worker:
            QMessageBox.information(self, "Operation in progress", "Keep Hearthkeeper open until the current operation finishes. You can minimize it, or stop after the current step.")
            event.ignore()
        else:
            event.accept()


def main():
    application = QApplication(sys.argv)
    application.setApplicationName("Hearthkeeper")
    application.setOrganizationName("Hearthkeeper")
    application.setStyleSheet((ASSETS / "desktop.qss").read_text().replace("__ASSETS__", ASSETS.as_posix()))
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        from .desktop_smoke import run
        run(application, sys.argv[2])
        return 0
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
