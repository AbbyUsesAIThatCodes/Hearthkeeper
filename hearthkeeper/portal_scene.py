"""Optional native 3D Home study. Launch/realm operations remain in desktop.py."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from PySide6.QtCore import QEvent, QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame, QGridLayout,
                              QHBoxLayout, QLabel, QMainWindow, QPushButton,
                              QSizePolicy, QVBoxLayout, QWidget)

from .client import services_ready
from .desktop import ASSETS
from .living_hearth import open_detail
from .six_worlds import MainWindow

SCENE = Path(__file__).resolve().parent / "scene"
STYLE = """
QMainWindow { background: #10151a; }
QWidget#sceneOverlay, QWidget#sceneStage { background: transparent; }
QLabel { color: #e9e3d5; background: transparent; border: none; font-size: 13px; }
QLabel#sceneBrand { color: #ead0a0; font-family: Georgia; font-size: 25px; }
QLabel#sceneEyebrow { color: #d4b785; font-size: 11px; font-weight: bold; }
QLabel#sceneValue { font-size: 17px; font-weight: bold; }
QLabel#sceneMuted { color: #bbc7ca; font-size: 12px; }
QFrame#scenePanel { background: rgba(13, 19, 23, 225); border: 1px solid #635744; border-radius: 5px; }
QPushButton { background: #20282c; color: #eee5d3; border: 1px solid #7f7054;
              border-radius: 3px; padding: 5px 12px; font-size: 13px; min-height: 18px; }
QPushButton:hover { background: #36433c; border-color: #d4b785; }
QPushButton:focus { border: 2px solid #f6d58f; }
QPushButton:disabled { color: #a2a4a2; background: #24282a; border-color: #525653; }
QPushButton#portalPlay { background: #45612c; border: 2px solid #b7d979; color: #fff7df;
                        font-size: 21px; font-weight: bold; padding: 14px 30px; }
QPushButton#portalPlay:disabled { background: #252b26; border-color: #737565; color: #bbbbad; }
QComboBox { background: #20282c; color: #eee5d3; border: 1px solid #7f7054; padding: 7px; min-width: 105px; }
QCheckBox { color: #ddd5c5; background: transparent; font-size: 12px; spacing: 6px; }
"""


def scene_pack(path):
    """Only open a prepared pack when all its declared files match the manifest."""
    directory = Path(path).resolve()
    manifest = json.loads((directory / "study.json").read_text(encoding="utf-8"))
    if manifest.get("file_data_id") != 7476464:
        raise ValueError("This camera study expects the housing Dark Portal (7476464).")
    files = manifest.get("files", {})
    entry = manifest.get("entrypoint")
    if not files or entry not in files:
        raise ValueError("Scene pack has no verified entrypoint.")
    for name, digest in files.items():
        file = (directory / name).resolve()
        if not file.is_relative_to(directory) or not file.is_file():
            raise ValueError("Scene pack is incomplete: " + name)
        if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise ValueError("Scene pack has changed: " + name)
    return directory / entry


class PortalRealmWindow(MainWindow):
    """Record actual service-check results for the optional scene's readout."""
    def __init__(self, **kwargs):
        self.service_rows = None
        self.service_checked = None
        self.portal_window = None
        super().__init__(**kwargs)

    def select_realm(self, path):
        self.service_rows = None
        self.service_checked = None
        super().select_realm(path)

    def refresh_status(self):
        def display(rows):
            self.service_rows = rows
            self.service_checked = datetime.now().strftime("%H:%M:%S")
            self.card_values[2].setText(("Ready at " if services_ready(rows) else "Not ready at ") + self.service_checked)
            self.activity.appendPlainText("\n".join(row.get("Service", "?") + ": " + row.get("State", "?") + " " + row.get("Health", "") for row in rows) or "No services created")
        self.realm_job("Reading service status", lambda realm: realm.status(), display)

    def navigate(self, index):
        super().navigate(index)
        if index == 0 and self.portal_window is not None:
            self.portal_window.show_scene()


def text_label(text="", role="", wrap=True):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    if role:
        widget.setObjectName(role)
    return widget


class PortalWindow(QMainWindow):
    def __init__(self, owner, pack, *, remember=True):
        super().__init__()
        self.owner = owner
        self.setWindowTitle("Hearthkeeper · Dark Portal study")
        self.setMinimumSize(980, 640)
        self.resize(1440, 900)
        self.setStyleSheet(STYLE)
        self.preferences = QSettings("Hearthkeeper", "PortalStudy") if remember else None
        self.handed_off = False
        self.was_fullscreen = False
        self.failed = False
        self.started = time.perf_counter()
        self.frame_times = []
        self.quick = QQuickWidget()
        self.quick.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.quick.setSource(QUrl.fromLocalFile(str(SCENE / "PortalHome.qml")))
        if self.quick.status() == QQuickWidget.Status.Error:
            raise RuntimeError("\n".join(error.toString() for error in self.quick.errors()))
        self.scene = self.quick.rootObject()
        self.scene.assetError.connect(self.scene_error)
        # QQuickWidget renders to a texture, so its internal window never swaps.
        self.quick.quickWindow().afterRendering.connect(self.record_frame, Qt.ConnectionType.DirectConnection)
        self.stage = QWidget(); self.stage.setObjectName("sceneStage")
        stage_layout = QGridLayout(self.stage); stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.addWidget(self.quick, 0, 0)
        overlay = QWidget(); overlay.setObjectName("sceneOverlay")
        self.overlay = overlay
        grid = QGridLayout(overlay); grid.setContentsMargins(28, 20, 28, 20)
        grid.setHorizontalSpacing(20); grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1); grid.setRowStretch(1, 1); grid.setRowStretch(2, 1)
        top = QHBoxLayout()
        brand = text_label("HEARTHKEEPER", "sceneBrand", False)
        top.addWidget(brand); top.addStretch()
        self.camera = QComboBox(); self.camera.addItems(["Portal approach", "Fortress overlook"])
        self.camera.setAccessibleName("Camera viewpoint")
        self.camera.currentIndexChanged.connect(lambda index: self.scene.setProperty("cameraIndex", index))
        top.addWidget(self.camera)
        self.motion = QCheckBox("Scene motion")
        self.motion.setChecked(self.preferences.value("motion", True, type=bool) if self.preferences else True)
        self.motion.toggled.connect(self.motion_changed); top.addWidget(self.motion)
        self.fullscreen = self.button("Fullscreen · F11", self.toggle_fullscreen); top.addWidget(self.fullscreen)
        top.addWidget(self.button("Desktop Home", self.desktop_home))
        grid.addLayout(top, 0, 0, 1, 3)

        self.realm_panel, realm_layout = self.panel("YOUR REALM")
        self.realm_name = text_label(role="sceneValue"); realm_layout.addWidget(self.realm_name)
        self.realm_info = text_label(role="sceneMuted"); realm_layout.addWidget(self.realm_info)
        self.install_state = text_label(); realm_layout.addWidget(self.install_state)
        self.open_realm = self.button("Open realm…", owner.open_realm); realm_layout.addWidget(self.open_realm)
        self.tools = self.button("Realm tools…", lambda: open_detail(owner.tools_dialog)); realm_layout.addWidget(self.tools)
        realm_layout.addSpacing(10)
        for index, name in ((1, "Characters"), (2, "Archives"), (3, "Backups")):
            realm_layout.addWidget(self.button(name, lambda checked=False, i=index: self.navigate(i)))
        grid.addWidget(self.realm_panel, 1, 0, 2, 1, Qt.AlignmentFlag.AlignVCenter)

        self.status_panel, status_layout = self.panel("REALM SERVICES")
        self.service_labels = {}
        for key, title in (("database", "Database"), ("auth", "Login"), ("world", "World")):
            value = text_label(title + " · Not checked")
            self.service_labels[key] = value; status_layout.addWidget(value)
        self.checked = text_label("No status check yet", "sceneMuted"); status_layout.addWidget(self.checked)
        self.check_status = self.button("Check services", owner.refresh_status); status_layout.addWidget(self.check_status)
        status_layout.addSpacing(10)
        for index, name in ((4, "Sources"), (5, "Workshop")):
            status_layout.addWidget(self.button(name, lambda checked=False, i=index: self.navigate(i)))
        status_layout.addWidget(self.button("Companions", owner.companion_guide))
        grid.addWidget(self.status_panel, 1, 2, 2, 1, Qt.AlignmentFlag.AlignVCenter)

        self.play = self.button("PLAY", owner.play); self.play.setObjectName("portalPlay")
        self.play.setMinimumWidth(180)
        self.play.setParent(overlay)
        self.play.adjustSize()
        self.scene.actionScreenChanged.connect(self.position_play)

        bottom, bottom_layout = self.panel("YOUR CLIENT", fixed=False)
        client_row = QHBoxLayout()
        self.client_info = text_label(); client_row.addWidget(self.client_info, 1)
        self.choose_client = self.button("Choose client…", owner.choose_client); client_row.addWidget(self.choose_client)
        self.connect_client = self.button("Connect", owner.connect_client); client_row.addWidget(self.connect_client)
        bottom_layout.addLayout(client_row)
        self.play_reason = text_label(role="sceneMuted"); bottom_layout.addWidget(self.play_reason)
        grid.addWidget(bottom, 3, 0, 1, 3)
        self.client_panel = bottom
        activity_row = QHBoxLayout()
        self.activity = text_label(role="sceneMuted"); activity_row.addWidget(self.activity, 1)
        self.cancel = self.button("Stop after step", owner.request_stop); activity_row.addWidget(self.cancel)
        activity_row.addWidget(self.button("Activity…", lambda: open_detail(owner.activity_dialog)))
        grid.addLayout(activity_row, 4, 0, 1, 3)
        stage_layout.addWidget(overlay, 0, 0)
        self.setCentralWidget(self.stage)
        self.quick.sceneGraphError.connect(lambda error, detail: self.scene_error(detail))
        self.scene.setProperty("studySource", QUrl.fromLocalFile(str(scene_pack(pack))))
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, activated=self.escape)
        self.sync_timer = QTimer(self); self.sync_timer.setInterval(250); self.sync_timer.timeout.connect(self.sync)
        self.sync_timer.start()
        QApplication.instance().applicationStateChanged.connect(self.sync_motion)
        owner.installEventFilter(self)
        self.sync()

    def position_play(self):
        if not hasattr(self, "play"):
            return
        point = self.scene.property("actionScreen")
        self.play.adjustSize()
        self.play.move(round(point.x() - self.play.width() / 2),
                       round(point.y() - self.play.height() / 2))
        self.play.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.width() < 1100 or self.height() < 760
        if getattr(self, "compact", None) != compact:
            self.compact = compact
            self.setStyleSheet(STYLE + ("QPushButton { padding: 5px 10px; } QLabel#sceneValue { font-size: 15px; }" if compact else ""))
            if hasattr(self, "realm_panel"):
                self.realm_panel.layout().setSpacing(5 if compact else 6)
                self.status_panel.layout().setSpacing(5 if compact else 6)
        QTimer.singleShot(0, self.position_play)

    def button(self, title, action):
        button = QPushButton(title); button.clicked.connect(action)
        return button

    def panel(self, title, *, fixed=True):
        frame = QFrame(); frame.setObjectName("scenePanel")
        if fixed:
            frame.setFixedWidth(220)
        layout = QVBoxLayout(frame); layout.setContentsMargins(16, 14, 16, 14); layout.setSpacing(6)
        layout.addWidget(text_label(title, "sceneEyebrow"))
        return frame, layout

    def record_frame(self):
        self.frame_times.append(time.perf_counter())
        self.frame_times = self.frame_times[-600:]

    def sync(self):
        owner = self.owner
        self.realm_name.setText(owner.card_values[0].text())
        self.realm_info.setText("This computer\nWrath · 3.3.5a / 12340" if owner.realm_path else "This computer\nNo realm selected")
        self.install_state.setText("Installation · " + owner.card_values[1].text())
        rows = {row.get("Service"): row for row in owner.service_rows or []}
        for key, title in (("database", "Database"), ("auth", "Login"), ("world", "World")):
            row = rows.get(key)
            value = ((row.get("State", "Unknown") + " " + row.get("Health", "")).strip()
                     if row else "Not created" if owner.service_rows is not None else "Not checked")
            self.service_labels[key].setText(title + " · " + value)
        self.checked.setText("Checked " + owner.service_checked if owner.service_checked else "No status check yet")
        busy = owner.worker is not None
        self.check_status.setEnabled(bool(owner.realm_path) and not busy)
        self.open_realm.setEnabled(not busy)
        self.play.setText(owner.play_button.text()); self.play.setEnabled(owner.play_button.isEnabled())
        self.play_reason.setText(owner.play_notice.text())
        client = owner.client
        self.client_info.setText("Wrath 3.3.5a · build 12340 · " + client.locale + "\n" + ("Connected to local realm" if owner.connect_client_button.text() == "Connected locally" else "Connection needs attention")
                                 if client else "No client selected · Choose a matching Wrath 3.3.5a installation")
        self.client_info.setToolTip(str(client.executable) if client else "")
        self.choose_client.setEnabled(owner.choose_client_button.isEnabled())
        self.connect_client.setEnabled(owner.connect_client_button.isEnabled())
        self.connect_client.setText(owner.connect_client_button.text())
        self.cancel.setEnabled(owner.stop_step.isEnabled())
        full_activity = owner.activity_summary.text()
        self.activity.setText(self.activity.fontMetrics().elidedText(full_activity, Qt.TextElideMode.ElideRight,
                                                                   max(100, self.width() - 360)))
        self.activity.setToolTip(full_activity)
        running = owner.game_process is not None and owner.game_process.poll() is None
        if running and not self.handed_off:
            self.handed_off = True
            self.was_fullscreen = self.isFullScreen()
            self.showMinimized()
        elif self.handed_off and not running:
            self.handed_off = False
            if self.was_fullscreen:
                self.showFullScreen()
            else:
                self.showNormal()
            self.activateWindow()
        self.sync_motion()

    def sync_motion(self, *_):
        active = (self.motion.isChecked() and self.isVisible() and not self.isMinimized()
                  and not self.handed_off and not self.failed
                  and QApplication.applicationState() == Qt.ApplicationState.ApplicationActive)
        self.scene.setProperty("sceneActive", active)

    def motion_changed(self, enabled):
        if self.preferences:
            self.preferences.setValue("motion", enabled)
        self.sync_motion()

    def show_scene(self):
        if self.failed:
            return
        self.owner.hide()
        fullscreen = self.preferences.value("fullscreen", True, type=bool) if self.preferences else False
        self.showFullScreen() if fullscreen else self.showNormal()
        self.raise_(); self.activateWindow(); self.sync_motion()

    def toggle_fullscreen(self):
        fullscreen = not self.isFullScreen()
        self.showFullScreen() if fullscreen else self.showNormal()
        if self.preferences:
            self.preferences.setValue("fullscreen", fullscreen)
        self.fullscreen.setText("Windowed · F11" if fullscreen else "Fullscreen · F11")

    def escape(self):
        if self.isFullScreen():
            self.toggle_fullscreen()
        else:
            self.desktop_home()

    def navigate(self, index):
        self.hide(); self.sync_motion()
        self.owner.show(); self.owner.navigate(index); self.owner.raise_(); self.owner.activateWindow()

    def desktop_home(self):
        self.hide(); self.sync_motion()
        # Bypass the scene-return override for an explicit fallback request.
        MainWindow.navigate(self.owner, 0)
        self.owner.show(); self.owner.raise_(); self.owner.activateWindow()

    def scene_error(self, detail):
        self.failed = True
        self.owner.activity.appendPlainText("3D Home unavailable · " + detail)
        self.desktop_home()

    def eventFilter(self, target, event):
        if target is self.owner and event.type() == QEvent.Type.Close:
            QTimer.singleShot(0, self.close_if_owner_closed)
        return False

    def close_if_owner_closed(self):
        if not self.owner.isVisible():
            self.hide(); self.sync_motion()

    def closeEvent(self, event):
        # Use the existing cancellation/close handling if a realm job is active.
        if self.owner.worker is not None:
            self.desktop_home()
            event.ignore()
            return
        else:
            self.owner.close()
        self.sync_timer.stop(); event.accept()

    def changeEvent(self, event):
        super().changeEvent(event)
        if hasattr(self, "scene"):
            self.sync_motion()


def default_pack():
    bundled = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "portal-study"
    return bundled if bundled.is_dir() else Path(__file__).resolve().parents[1] / "var/portal-study"


def main():
    parser = argparse.ArgumentParser(description="Hearthkeeper's optional Dark Portal scene study")
    parser.add_argument("--scene-pack", type=Path, default=default_pack())
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--smoke-test", type=Path)
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("Hearthkeeper"); app.setOrganizationName("Hearthkeeper")
    app.setStyleSheet((ASSETS / "desktop.qss").read_text(encoding="utf-8").replace("__ASSETS__", ASSETS.as_posix()))
    if args.smoke_test:
        from .portal_scene_smoke import run
        return run(app, args.scene_pack, args.smoke_test)
    owner = PortalRealmWindow()
    try:
        window = PortalWindow(owner, args.scene_pack)
        owner.portal_window = window
        return_button = QPushButton("Return to 3D Home")
        return_button.clicked.connect(window.show_scene)
        owner.tools_dialog.layout().addWidget(return_button)
        if args.windowed:
            window.show()
        else:
            window.show_scene()
    except Exception as error:
        owner.activity.appendPlainText("3D study unavailable. Desktop Home remains available.\n" + str(error))
        owner.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
