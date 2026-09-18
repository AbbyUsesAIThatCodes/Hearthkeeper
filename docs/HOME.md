# The Living Hearth — Home and Play

Version 0.1.0a9 refines the original a5 Play flow in native Qt. See
[The Living Hearth](LIVING_HEARTH.md) for layout, motion, and validation details.

![Home with fictional realm and client fixtures](images/living-hearth.jpg)

## Start an adventure

1. Open **Home → Open realm** and select the existing folder containing `realm.json`.
2. Choose **Wow.exe** from the original Windows 3.3.5a / build 12340 installation.
   If it has multiple language folders, select the language you use in that client.
3. If the installation is not pointed at the local realm, click **Connect to this realm**.
   Confirm the displayed file path. Its exact previous bytes are saved beside it as
   `realmlist.wtf.hearthkeeper-<timestamp>.bak` before the local address is written.
4. Click **Play**. Hearthkeeper checks the client again, starts the realm when
   needed, waits for all three services to be healthy, and opens the game.
5. Sign in with the account you already created for this realm.

The app remembers the executable and locale for each realm. It reads the Windows
executable version resource without running the file. It checks the two required
expansion archive paths and language folder, but does not verify every game file
or claim that arbitrary patched executables are authentic. Missing, moved, or
wrong-version installations must be selected again.

## What to expect

- **Services: Not checked** is deliberate until a check is performed. A ready status
  includes the local check time. Play always checks services before launch.
- **Play unavailable** has an adjacent explanation: choose a realm, finish installation,
  choose a game, connect it, or wait for the current operation.
- Starting a stopped realm may take time. Activity shows actual progress; a failed
  or cancelled operation never proceeds to launch the game.
- An app-launched running game disables another Play request. When it exits, Play
  becomes available. Games launched elsewhere or by a previous app session are not tracked.
- Choosing a file does not alter it. Connection setup is a separate explicit action.
  A game installation shared by other realms shares its realmlist too. To restore
  its previous destination, close the game and copy the desired dated backup over
  `realmlist.wtf`.
- The app does not store or insert a game-account password. Creating accounts is
  still available under **Characters**.
- Closing Hearthkeeper leaves the game and running realm alone. Use **Realm tools →
  Stop realm** for a deliberate shutdown.
- Home fits without scrolling at the tested work areas down to 980 × 640.
  **Realm tools…** and **Activity…** open separate windows. Other pages retain
  scrolling for their lists and content.
- **Scene motion** remembers whether to show the subtle portal animation. Turn
  it off for a still scene. The complete a8 artwork and local SVG fallback remain.

**Realm tools → Companion guide** supplies basic Playerbots commands. Addon/module installation,
Luna deployment, torrent integration, and other-era game launching remain future work.
Windows is the supported game-launch platform; Linux still supports realm/archive operations.

## Validation boundary

The home screenshot uses an explicitly fictional realm and client. Unit and native
widget tests cover the new orchestration; Windows CI tests both source and packaged
UI and the executable-version API. The developer environment does not contain WoW
or a running realm, so the real-client Play path needs a Windows user playtest.
The existing user-reported successful login was in the previous local build.
