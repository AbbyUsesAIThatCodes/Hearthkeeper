"""Optional Chromium checks; run directly after installing Playwright + Chromium."""
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright
from hearthkeeper.archive import write_archive
from hearthkeeper.database import capture, sqlite_reader
from hearthkeeper.demo import create_fixture
from hearthkeeper.viewer import render_archive


def main():
    screenshots = ROOT / "var" / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        database = create_fixture(directory / "fictional.sqlite")
        with sqlite_reader(database) as reader:
            snapshot = capture(reader, 7, "copperleaf-demo", demo=True)
        archive = write_archive(directory / "sample.hearth", snapshot)
        document = render_archive(archive, directory / "sample.html")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
            errors, requests = [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: requests.append(request.url))
            page.goto(document.as_uri())
            page.screenshot(path=str(screenshots / "overview.png"), full_page=True)
            page.get_by_role("tab", name="Equipment & bags").click()
            page.locator("#search").fill("Lantern")
            assert page.locator("#inventory tbody tr:visible").count() == 2
            page.locator("#search").fill("")
            assert page.locator("#inventory table").first.locator("tbody tr:visible").count() == 6
            page.screenshot(path=str(screenshots / "inventory.png"), full_page=True)
            page.get_by_role("tab", name="Module data").click()
            page.get_by_text("hearthkeeper.demo.progression", exact=True).click()
            assert "completed_tier" in page.locator("#modules pre:visible").first.inner_text()
            page.get_by_role("tab", name="Coverage", exact=True).click()
            assert page.get_by_text("characters.custom_town_citizenship", exact=True).count() == 1
            page.set_viewport_size({"width": 390, "height": 844})
            page.get_by_role("tab", name="Overview", exact=True).click()
            page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert not errors, errors
            assert all(url.startswith("file:") for url in requests), requests
            # Render hostile archived text in a real browser, with a matching valid manifest.
            snapshot["tables"]["characters.characters"]["rows"][0]["name"] = '<img src="https://example.invalid/x" onerror="window.injected=true">'
            hostile = write_archive(directory / "hostile.hearth", snapshot)
            hostile_html = render_archive(hostile, directory / "hostile.html")
            page.goto(hostile_html.as_uri())
            assert page.locator("img").count() == 0
            assert page.evaluate("window.injected === undefined")
            assert all(url.startswith("file:") for url in requests), requests
            assert not errors, errors
            browser.close()
    print("Browser checks passed: tabs, search, module data, coverage, mobile layout, escaped content, zero remote requests.")


if __name__ == "__main__":
    main()
