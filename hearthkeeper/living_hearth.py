"""Compact native Home and optional motion. No realm operations live here."""
from PySide6.QtCore import QElapsedTimer, QEvent, QObject, Qt, QTimer
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame, QHBoxLayout,
                              QLabel, QLayout, QPushButton, QScrollArea, QSizePolicy,
                              QVBoxLayout, QWidget)


class ElidedLabel(QLabel):
    """Keep full native text accessible and in a tooltip while limiting its footprint."""
    def __init__(self, source, parent=None):
        super().__init__(source.text(), parent)
        self.setObjectName(source.objectName())
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)
        self.setWordWrap(False)

    def setText(self, text):
        super().setText(text)
        self.setToolTip(text)
        self.setAccessibleName(text)

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().windowText().color())
        painter.drawText(self.contentsRect(), Qt.AlignmentFlag.AlignVCenter,
                         self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideRight,
                                                      self.contentsRect().width()))
        painter.end()


class HomePresentation(QObject):
    def __init__(self, window, content):
        super().__init__(window)
        self.window = window
        self.content = content
        self.header = window.scene_headers[0]
        self.viewport = window.pages.widget(0).viewport()
        self.viewport.installEventFilter(self)
        content.installEventFilter(self)
        self.header.installEventFilter(self)
        window.installEventFilter(self)
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.fit)
        self.clock = QElapsedTimer()
        self.clock.start()
        self.motion_timer = QTimer(self)
        self.motion_timer.setInterval(50)  # 20 fps; no rendering when hidden or inactive.
        self.motion_timer.timeout.connect(self.animate)
        QApplication.instance().applicationStateChanged.connect(self.sync_motion)
        self.fit()

    def eventFilter(self, target, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.LayoutRequest):
            self.resize_timer.start(0)
        if event.type() in (QEvent.Type.Show, QEvent.Type.Hide, QEvent.Type.WindowStateChange):
            QTimer.singleShot(0, self.sync_motion)
        return False

    def fit(self):
        # Measure the controls at their actual width: selected client paths and
        # readiness messages can wrap differently from the empty startup state.
        layout = self.content.layout()
        needed = layout.totalHeightForWidth(self.viewport.width())
        if needed < 0:
            needed = layout.sizeHint().height()
        controls = needed - self.header.height()
        height = max(170, min(350, self.viewport.height() - controls - 4))
        if self.header.height() != height:
            self.header.setFixedHeight(height)
        self.sync_motion()

    def sync_motion(self, *_):
        enabled = self.window.motion_toggle.isChecked() and not self.header.painting.isNull()
        self.header.motion_enabled = enabled
        active = (enabled and self.header.isVisible() and not self.window.isMinimized()
                  and QApplication.applicationState() == Qt.ApplicationState.ApplicationActive)
        if active and not self.motion_timer.isActive():
            self.clock.restart()
            self.motion_timer.start()
        elif not active:
            self.motion_timer.stop()
        self.header.update()

    def animate(self):
        self.header.motion_phase += self.clock.restart() / 1000
        self.header.update()

    def set_motion(self, enabled):
        if self.window.preferences is not None:
            self.window.preferences.setValue("living_hearth/motion", enabled)
        self.sync_motion()


def detail_window(window, title):
    dialog = QDialog(window)
    dialog.setWindowTitle(title + " · Hearthkeeper")
    dialog.resize(760, 440)
    dialog.setMinimumSize(540, 320)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(18, 18, 18, 18)
    return dialog


def open_detail(dialog):
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()


def prepare(window, content):
    window.setMinimumSize(980, 640)
    layout = content.layout()
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    # Gather the existing widgets before rearranging them; callbacks remain connected.
    cards = layout.itemAt(1).layout()
    open_row = layout.itemAt(3).layout()
    shortcuts = layout.itemAt(5).layout()
    tools = content.findChild(QWidget, "realmTools")
    for item in (window.realm_notice, window.realm_tools_toggle, tools):
        layout.removeWidget(item)
    layout.removeItem(open_row)
    layout.removeItem(shortcuts)
    while layout.count() and layout.itemAt(layout.count()-1).spacerItem():
        layout.takeAt(layout.count()-1)

    # The original three status values remain the authoritative state targets.
    for index, source in enumerate(window.card_values):
        replacement = ElidedLabel(source)
        source.parentWidget().layout().replaceWidget(source, replacement)
        source.hide()
        source.deleteLater()
        window.card_values[index] = replacement
        replacement.setText(replacement.text())
    host = QFrame(content)
    host.setObjectName("card")
    host_layout = QVBoxLayout(host)
    title = QLabel("HOST"); title.setObjectName("cardTitle")
    value = QLabel("This computer"); value.setObjectName("cardValue")
    window.host_value = ElidedLabel(value)
    value.deleteLater()
    window.host_value.setText("This computer")
    window.host_value.setToolTip("Local realm services. Luna migration is a future milestone.")
    host_layout.addWidget(title)
    host_layout.addWidget(window.host_value)
    cards.addWidget(host, 1)

    window.tools_dialog = detail_window(window, "Realm tools")
    tool_content = QWidget()
    tool_layout = QVBoxLayout(tool_content)
    tool_layout.addWidget(window.realm_notice)
    tool_layout.addWidget(tools)
    tool_layout.addLayout(shortcuts)
    tool_layout.addStretch()
    tools.show()
    scroller = QScrollArea()
    scroller.setWidgetResizable(True)
    scroller.setWidget(tool_content)
    window.tools_dialog.layout().addWidget(scroller)
    window.realm_tools_toggle.toggled.disconnect()
    window.realm_tools_toggle.setText("Realm tools…")
    window.realm_tools_toggle.toggled.connect(
        lambda checked: open_detail(window.tools_dialog) if checked else window.tools_dialog.hide())
    window.tools_dialog.finished.connect(lambda _: window.realm_tools_toggle.setChecked(False))

    toolbar = QHBoxLayout()
    while open_row.count():
        item = open_row.takeAt(0)
        if item.widget():
            toolbar.addWidget(item.widget())
    toolbar.addWidget(window.realm_tools_toggle)
    toolbar.addStretch()
    window.motion_toggle = QCheckBox("Scene motion")
    window.motion_toggle.setToolTip("Turn off for a still scene and reduced motion.")
    enabled = window.preferences.value("living_hearth/motion", True, type=bool) if window.preferences is not None else True
    window.motion_toggle.setChecked(enabled)
    toolbar.addWidget(window.motion_toggle)
    layout.addLayout(toolbar)
    layout.addStretch(1)

    # Preserve the live log and cancellation controls in an independently scrollable window.
    right = window.pages.parentWidget()
    activity_panel = window.activity.parentWidget()
    window.activity_dialog = detail_window(window, "Activity")
    window.activity_dialog.layout().addWidget(activity_panel)
    column = QWidget()
    column_layout = QVBoxLayout(column)
    column_layout.setContentsMargins(0, 0, 0, 0)
    column_layout.setSpacing(0)
    column_layout.addWidget(window.pages, 1)
    footer = QFrame(); footer.setObjectName("hearthFooter")
    footer_layout = QHBoxLayout(footer)
    footer_layout.setContentsMargins(16, 5, 16, 6)
    window.activity_summary = ElidedLabel(QLabel("Ready"))
    window.activity_summary.setObjectName("activitySummary")
    footer_layout.addWidget(window.activity_summary, 1)
    window.progress.setFixedWidth(80)
    footer_layout.addWidget(window.progress)
    window.activity_button = QPushButton("Activity…")
    window.activity_button.clicked.connect(lambda: open_detail(window.activity_dialog))
    footer_layout.addWidget(window.activity_button)
    column_layout.addWidget(footer)
    root_layout = window.centralWidget().layout()
    root_layout.removeWidget(right)
    right.deleteLater()
    root_layout.addWidget(column, 1)

    def summarize_activity():
        line = window.activity.document().lastBlock().text()
        window.activity_summary.setText(line or "Ready")
    window.activity.textChanged.connect(summarize_activity)
    summarize_activity()
    window.home_presentation = HomePresentation(window, content)
    window.motion_toggle.toggled.connect(window.home_presentation.set_motion)
