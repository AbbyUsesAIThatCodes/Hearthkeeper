# Publishing a Windows preview

Users get executables from **Releases**. Actions is the build and test workspace.
`main` is the shared source branch; feature branches are temporary development work.

1. Merge the reviewed change into main. Update `hearthkeeper/__init__.py` and
   `pyproject.toml` together when the application version changes. Update the
   changelog and current-version links in README.md and the Windows launchers.
2. Wait for **Hearthkeeper checks** and **Native desktop** to succeed on the same
   main commit. The Windows artifact name is derived from the application version.
3. Download that exact run's `Hearthkeeper-<version>-Windows` artifact. Confirm
   `result.json`, `six-worlds-result.json`, and `home-art-result.json` in the
   screenshot artifact all report success. Record the full source commit and run URL.
4. Package the complete app directory as `Hearthkeeper-<version>-Windows.zip`,
   including `_internal` and licenses, and calculate a SHA-256 checksum. Preserve
   every packaged file, including hidden files; verify the ZIP against the input.
5. Create a version tag on the tested source commit and a GitHub **prerelease**
   with the Windows ZIP, `SHA256SUMS.txt`, and notes naming the build, what changed,
   how to run it, and any remaining acceptance work. Do not replace an existing
   release's assets with different bytes under the same version.
6. Verify the published download/checksum and the README link. Users should see
   the version, a direct Windows download, and **Extract All → Hearthkeeper.exe**.

GitHub's automatic source ZIP/tar downloads do not contain the Windows app.
Prereleases are intentionally labeled as previews; link their explicit versioned
release/download URLs rather than relying on `/releases/latest`.

The a8 recovery release promotes the previously tested `9fc68b7` artifact unchanged;
its notes retain that provenance separately from the repository documentation repair.
