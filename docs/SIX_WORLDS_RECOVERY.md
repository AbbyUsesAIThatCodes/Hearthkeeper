# Six Worlds, One Hearth — recovery checkpoint

Historical checkpoint from before the a6 reconstruction. That reconstruction and
the a8 follow-up are now preserved; see the [current recovery record](RECOVERY.md).

This branch starts at the verified a5 merge `57d3800d340511b2283721d46ffb87420632e5ef` on `feature/source-catalog`. It reconstructs the interrupted a6 interface work; it is not a recovery of the original unpublished source or artwork.

## Approved design

| Page | Visual theme | Purpose |
| --- | --- | --- |
| Home | The Burning Crusade | A portal into adventure |
| Characters | Legion | Class halls, heraldry, arcane light |
| Archives | Mists of Pandaria | Scrolls, jade, tranquil libraries |
| Backups | Wrath of the Lich King | Runic stone, icy vaults |
| Sources | Warlords of Draenor | Expedition maps, copper and iron |
| Workshop | Cataclysm | Forges, molten metal, reshaping a world |

Large scenic headers and ornate frames should sit above quiet readable panels. Navigation and familiar controls must remain usable. Every theme is decorative: the managed realm remains the original Wrath 3.3.5a/build 12340 setup. No theme changes server selection or claims another era is playable.

## Safety and continuity

- Do not alter the user's live realm, accounts, characters, databases, client files, or settings to deliver this visual update.
- Preserve the a5 Play safeguards, backup confirmations, cancellation behavior, and disabled-state distinctions.
- Publish incremental work on this branch. Verify remote commit IDs before calling anything backed up.
- Keep source and changes separate from generated previews and private realm data.
- Original reported a6 tests (47 passes and one Windows-only skip) are historical reports, not evidence for this reconstruction.

## Status at initial checkpoint

The design is saved; reconstruction and fresh validation are pending. The previous source/artwork and previous a6 commit were not recovered. This branch does not migrate anything to Luna. The next milestones remain Luna migration, acquisition automation, other eras, and the content workshop.
