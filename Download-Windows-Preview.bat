@echo off
setlocal
echo Opening Hearthkeeper's Native desktop builds in your browser.
echo Sign into the same GitHub account you use in GitHub Desktop.
echo Open a successful run for feature/desktop-realm-manager and scroll to Artifacts.
echo Download Hearthkeeper-0.1.0a2-Windows, extract the WHOLE ZIP, then run Hearthkeeper.exe.
echo This download route does not need Python. GitHub artifacts expire after 30 days.
start "" "https://github.com/AbbyUsesAIThatCodes/Hearthkeeper/actions/workflows/desktop.yml?query=branch%%3Afeature%%2Fdesktop-realm-manager"
