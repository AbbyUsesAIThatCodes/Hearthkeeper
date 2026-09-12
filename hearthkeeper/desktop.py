"""Native Qt desktop application. No web view or local HTTP server."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

from PySide6.QtCore import Qt, QSettings, QStandardPaths, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QScrollArea, QSpinBox, QSplitter, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from . import CODENAME, __version__
from .archive import compare_archives, read_archive, write_archive
from .database import capture, sqlite_reader
from .demo import create_fixture
from .model import normalized, records, RACES, CLASSES
from .server.manager import ManagedRealm, RealmError, Runner, create_realm, local_docker

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
        self.pages = QStackedWidget()
        root = QWidget(); root_layout = QHBoxLayout(root); root_layout.setContentsMargins(0, 0, 0, 0); root_layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(212)
        navigation = QVBoxLayout(sidebar); navigation.setContentsMargins(18, 28, 18, 22); navigation.setSpacing(9)
        emblem = QLabel(); emblem.setPixmap(QIcon(str(ASSETS / "hearthkeeper.svg")).pixmap(64, 64))
        navigation.addWidget(emblem); navigation.addWidget(label("Hearthkeeper", "brand"))
        navigation.addWidget(label("YOUR OWN AZEROTH", "brandSub")); navigation.addSpacing(28)
        self.nav_buttons = []
        for index, title in enumerate(("Realm", "Characters", "Archives", "Backups", "Workshop")):
            item = QPushButton(title); item.setObjectName("nav"); item.setCheckable(True)
            item.clicked.connect(lambda checked=False, index=index: self.navigate(index))
            navigation.addWidget(item); self.nav_buttons.append(item)
        navigation.addStretch()
        navigation.addWidget(label("First Campfire\n" + __version__, "brandSub"))
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
        right.addWidget(activity); right.setSizes([650, 190]); root_layout.addWidget(right, 1)
        self.setCentralWidget(root)
        self.build_realm_page(); self.build_characters_page(); self.build_archives_page(); self.build_backups_page(); self.build_workshop_page()
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
        widget, layout = page("A home for your Azeroth.", "Install your progression realm, keep it running, and make room for the adventures ahead.")
        self.realm_notice = label("Start with a new realm, or reopen one Hearthkeeper has already created.", "status")
        layout.addWidget(self.realm_notice)
        cards = QHBoxLayout()
        self.card_values = []
        for title, value in (("YOUR REALM", "No realm selected"), ("INSTALLATION", "Not started"), ("SERVICES", "Not checked")):
            card = QFrame(); card.setObjectName("card"); inside = QVBoxLayout(card); inside.setContentsMargins(18, 18, 18, 18)
            inside.addWidget(label(title, "cardTitle")); content = label(value, "cardValue"); inside.addWidget(content)
            cards.addWidget(card); self.card_values.append(content)
        layout.addLayout(cards)
        row = QHBoxLayout()
        row.addWidget(self.action("New realm…", self.new_realm, True))
        row.addWidget(self.action("Open realm…", self.open_realm))
        row.addWidget(self.action("Check prerequisites", self.prerequisites))
        row.addStretch(); layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(self.action("Install / Resume", lambda: self.realm_job("Installing realm", lambda realm: realm.install()), True))
        row.addWidget(self.action("Start realm", lambda: self.realm_job("Starting realm", lambda realm: realm.start())))
        row.addWidget(self.action("Stop realm", lambda: self.realm_job("Stopping realm", lambda realm: realm.stop())))
        row.addWidget(self.action("Refresh status", self.refresh_status))
        row.addStretch(); layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(self.action("Realm settings…", self.realm_settings))
        row.addWidget(self.action("Show server logs", lambda: self.realm_job("Reading server logs", lambda realm: realm.compose("logs", "--tail", "120", "auth", "world"))))
        row.addStretch(); layout.addLayout(row)
        layout.addWidget(label("CONNECT FROM THIS COMPUTER", "eyebrow"))
        layout.addWidget(label("Use an original 3.3.5a / build 12340 client and a realm account created here. Set its realmlist to 127.0.0.1. WoWee installation and client-file patching are later steps.", "muted"))
        layout.addWidget(button("Docker Desktop setup guide", lambda: QDesktopServices.openUrl(QUrl("https://docs.docker.com/desktop/setup/install/windows-install/"))))
        layout.addStretch()
        self.pages.addWidget(widget)

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
        self.realm_notice.setText(str(realm.path) + "\nLocal-only realm · original 3.3.5a · in-game verification required")
        backups = sorted((realm.path / "backups").glob("*/manifest.json"), reverse=True)
        self.backup_list.setPlainText("\n".join(str(path.parent) for path in backups) or "No completed backups yet.")

    def run_job(self, title, function, callback=None):
        if self.worker:
            QMessageBox.information(self, "Operation in progress", "Let the current operation finish first.")
            return
        self.activity.appendPlainText("\n" + title)
        self.worker = Worker(function)
        worker = self.worker
        worker.line.connect(self.activity.appendPlainText)
        worker.finished.connect(lambda: self.job_finished(worker, callback))
        for action in self.actions:
            action.setEnabled(False)
        self.progress.setRange(0, 0)
        self.stop_step.setEnabled(True)
        worker.start()

    def job_finished(self, worker, callback):
        self.worker = None
        self.progress.setRange(0, 1); self.progress.setValue(1)
        self.stop_step.setEnabled(False)
        for action in self.actions:
            action.setEnabled(True)
        try:
            path = self.pending_path or self.realm_path
            if path and (Path(path) / "realm.json").is_file():
                self.select_realm(path)
            self.pending_path = None
            if worker.error:
                self.activity.appendPlainText("NEEDS ATTENTION · " + worker.error)
                self.card_values[2].setText("Check activity")
                QMessageBox.warning(self, "Operation needs attention", worker.error)
            elif callback:
                callback(worker.result)
            elif worker.result is not None:
                self.activity.appendPlainText(str(worker.result))
        except Exception as error:
            self.activity.appendPlainText(str(error))
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
            lambda result: QMessageBox.information(self, "Docker is ready", f"Local Linux context: {result['context']}\nMemory available to Docker: {result['memory_gib']} GiB\nGame files and disk space are checked separately."))

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
            self.card_values[2].setText(" · ".join(row.get("Service", "?") + ": " + row.get("Health", "") + " " + row.get("State", "?") for row in rows) or "No services created")
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
    application.setStyleSheet((ASSETS / "desktop.qss").read_text())
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        from .desktop_smoke import run
        run(application, sys.argv[2])
        return 0
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
