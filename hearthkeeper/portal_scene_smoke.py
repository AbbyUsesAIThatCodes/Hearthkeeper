"""Render the actual scene and exercise its native controls without Docker or WoW."""
import json
import os
from pathlib import Path
import platform
import tempfile
import time
from unittest.mock import Mock, patch

from PySide6.QtCore import QPoint, Qt, qInstallMessageHandler
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox

from .client import EXPECTED_VERSION, inspect_client, prepare_realmlist
from .portal_scene import PortalRealmWindow, PortalWindow, scene_pack
from .server.manager import ManagedRealm, create_realm


def run(app, pack, output):
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=True)
    app.setQuitOnLastWindowClosed(False)
    messages = []
    previous = qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    started = time.perf_counter()
    owner = PortalRealmWindow(remember=False)
    window = PortalWindow(owner, pack, remember=False)
    owner.portal_window = window
    window.show(); window.activateWindow()

    def settle(ms=100):
        QTest.qWait(ms); app.processEvents()

    def worker_finished():
        deadline = time.monotonic() + 10
        while owner.worker and time.monotonic() < deadline:
            settle(10)
        assert owner.worker is None, "Realm operation did not finish"
        window.sync(); settle()

    def capture(name):
        window.grab().save(str(output / (name + ".png")))

    try:
        settle(1800)
        assert window.scene.property("modelReady"), "The real Portal did not load"
        startup_ms = (window.frame_times[0] - started) * 1000 if window.frame_times else None
        assert not window.play.isEnabled()
        assert "Open or create" in window.play_reason.text()
        capture("portal-empty")
        # Pixel evidence distinguishes a working animation from an advancing clock.
        first = window.quick.grabFramebuffer()
        before = window.scene.property("sceneSeconds")
        settle(700)
        second = window.quick.grabFramebuffer()
        assert window.scene.property("sceneSeconds") > before, "Motion clock is stopped"
        changed_bytes = sum(a != b for a, b in zip(bytes(first.bits()), bytes(second.bits())))
        assert changed_bytes > 1000, "Portal effects did not visibly animate"
        window.motion.setChecked(False); settle(100)
        still = window.scene.property("sceneSeconds"); settle(250)
        assert window.scene.property("sceneSeconds") == still, "Reduced motion did not pause"
        window.motion.setChecked(True)
        with tempfile.TemporaryDirectory(prefix="hearthkeeper-portal-test-") as temporary:
            temporary = Path(temporary)
            game = temporary / "fictional-client"
            (game / "Data/enUS").mkdir(parents=True)
            for name in ("Wow.exe", "Data/lichking.MPQ", "Data/patch-3.MPQ"):
                (game / name).write_bytes(b"Fictional test fixture; never execute")
            realm = create_realm(temporary / "realm", name="First Campfire - demo",
                                 data_path=str(game), data_kind="client", docker_context="default")
            realm.config["phase"] = "installed"; realm.save()
            ready = [{"Service": name, "State": "running", "Health": "healthy"}
                     for name in ("database", "auth", "world")]
            with patch("hearthkeeper.client.windows_file_version", return_value=EXPECTED_VERSION):
                owner.select_realm(realm.path)
                with patch.object(QFileDialog, "getOpenFileName", return_value=(str(game / "Wow.exe"), "")):
                    owner.choose_client()
                prepare_realmlist(owner.client)
                owner.update_play_state(); window.sync()
                assert window.play.isEnabled()
                with patch.object(ManagedRealm, "status", return_value=ready):
                    window.check_status.click(); worker_finished()
                assert all("running healthy" in label.text() for label in window.service_labels.values())
                assert window.checked.text().startswith("Checked ")
                sizes = []
                for width, height in ((1920, 1080), (1440, 900), (1280, 720), (980, 640)):
                    window.resize(width, height); settle(140)
                    assert window.size().width() == width and window.size().height() == height, "Layout grew past the requested size"
                    for item in (window.realm_panel, window.status_panel, window.client_panel, window.play):
                        rect = item.rect().translated(item.mapTo(window.stage, QPoint(0, 0)))
                        assert window.stage.rect().contains(rect), "Controls extend beyond the window"
                    for item in window.overlay.findChildren(QLabel):
                        if item.wordWrap():
                            assert item.height() >= item.heightForWidth(item.width()), f"Text is clipped ({width}x{height}; {item.width()}x{item.height()} needs {item.heightForWidth(item.width())}): " + item.text()
                    for panel in (window.realm_panel, window.status_panel, window.client_panel):
                        assert not window.play.geometry().intersects(panel.geometry()), "Play overlaps a status panel"
                    capture(f"portal-approach-{width}x{height}")
                    sizes.append({"width": width, "height": height, "device_pixel_ratio": window.devicePixelRatioF()})
                window.resize(1440, 900)
                window.camera.setCurrentIndex(1); settle(400)
                capture("portal-overlook")
                assert window.scene.property("cameraIndex") == 1
                window.camera.setCurrentIndex(0); settle(100)
                window.toggle_fullscreen(); settle(100)
                assert window.isFullScreen()
                window.escape(); settle(100)
                assert not window.isFullScreen()
                window.navigate(2); settle(100)
                assert owner.isVisible() and owner.pages.currentIndex() == 2
                assert not window.scene.property("sceneActive")
                owner.navigate(0); settle(100)
                assert window.isVisible() and not owner.isVisible()
                # Play remains the existing async workflow. Verify both handoff and failure.
                process = Mock(); process.poll.return_value = None
                with patch.object(ManagedRealm, "status", return_value=ready), patch("hearthkeeper.desktop.launch_client", return_value=process) as launch:
                    window.play.click(); owner.play(); worker_finished()
                    launch.assert_called_once()
                    assert window.handed_off and window.isMinimized()
                    assert not window.scene.property("sceneActive")
                    process.poll.return_value = 0; process.returncode = 0
                    owner.game_tick(); window.sync(); settle()
                    assert not window.handed_off and not window.isMinimized()
                with patch.object(ManagedRealm, "status", side_effect=RuntimeError("Fictional Docker failure")), patch("hearthkeeper.desktop.launch_client") as launch, patch.object(QMessageBox, "warning") as warning:
                    window.play.click(); worker_finished()
                    launch.assert_not_called(); warning.assert_called_once()
                    assert not window.handed_off and not window.isMinimized()
                    assert window.play.isEnabled()
                owner.client = None; owner.realm_path = None; owner.update_play_state()
        # Runtime resource errors return to a usable native Home.
        window.scene_error("Intentional missing asset check"); settle()
        assert owner.isVisible() and not window.isVisible()
        assert not window.scene.property("sceneActive")
        with tempfile.TemporaryDirectory() as empty:
            try:
                scene_pack(empty)
            except FileNotFoundError:
                pass
            else:
                raise AssertionError("Missing pack accepted")
        frames = window.frame_times
        deltas = [b-a for a, b in zip(frames, frames[1:]) if 0 < b-a < .1]
        result = {
            "passed": True, "platform": platform.platform(),
            "graphics_api": str(window.quick.quickWindow().rendererInterface().graphicsApi()),
            "first_frame_ms": round(startup_ms) if startup_ms is not None else None,
            "render_interval_median_ms": round(sorted(deltas)[len(deltas)//2] * 1000, 2) if deltas else None,
            "animation_changed_bytes": changed_bytes, "sizes": sizes,
            "checks": ["actual housing Portal", "visible animated effects", "motion-off freeze", "both cameras",
                       "visible realm/client/service facts", "no control overlap", "fullscreen escape", "six-worlds navigation",
                       "async Play handoff", "duplicate Play blocked", "failed Play keeps Home", "restore on process exit", "asset error fallback"],
            "limitations": "No actual WoW process or Docker server launched; native GPU and user-machine performance still need testing.",
            "qt_messages": messages,
        }
        errors = [m for m in messages if any(token in m.lower() for token in ("failed to compile", "failed to parse shader", "referenceerror", "typeerror", "cannot assign", "error loading"))]
        assert not errors, "Qt renderer errors: " + "\n".join(errors)
        (output / "portal-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({key: result[key] for key in ("passed", "graphics_api", "animation_changed_bytes", "render_interval_median_ms")}))
        return 0
    except Exception:
        import traceback
        capture("portal-failure")
        (output / "portal-error.txt").write_text(traceback.format_exc() + "\n\n" + "\n".join(messages), encoding="utf-8")
        raise
    finally:
        window.close(); owner.close(); app.processEvents()
        qInstallMessageHandler(previous)
