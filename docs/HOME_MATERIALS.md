# 0.1.0a8 — At the War Table

This pass changes the actual native Home page, not only the concept picture.

## What is implemented

The full bundled 877 × 258 scene is shown with aspect-preserving contain sizing, rather than cropped to cover the banner. Both statues and surrounding scenery remain within the displayed source. The previous dark overlay is removed. All Home lettering, including “The Burning Crusade · Some gates should never close,” is native wrapping text outside the picture; no embedded title can be sliced by resizing.

Stone, aged wood, vellum, parchment map detail, icon medallions, and carved frames are cut from the latest generated concept and packed into one local atlas. The eight non-center regions of each ornamental frame are painted as nine-slice borders; the source's fake status/control text is excluded. Existing status plaques, navigation buttons, client panel, and Play button receive the textures. Qt still owns their signals, real state, focus, keyboard behavior, and accessible text. The disabled Play button remains visibly disabled.

All painters operate only on Home. The other five page scenes/styles and the baseline realm-management and client logic are unchanged. The presentation does not read a live realm, change a realmlist, create an account, start a server, or perform a backup by itself. Actual operations retain their existing explicit controls and confirmations.

## Limits

This is not a pixel-identical copy of the mockup. The existing three truthful status plaques are retained, not the mockup's fictional database and backup status. Decorative desk props and the other five painterly page replacements remain future work. The source concept is 1536 × 1024; the text-free scene crop is 877 × 258, not newly painted full-screen art or an upscale claiming added detail.

## Asset provenance and packaging

`assets/war-table.json` records the original image checksum, source crop rectangles, atlas regions, and exact decoded WebP checksum. Six fixed ASCII base64 pieces preserve the 1024 × 544 atlas through the available repository publishing route. The runtime verifies and decodes them in memory; it makes no network requests or temporary asset files. Invalid or missing material assets fall back to usable ordinary/vector widgets. No font files are bundled.

The original a7 art assets remain for compatibility/provenance and existing regression tests, but new Home painting uses the material atlas.

## Validation

Six new non-GUI tests cover the exact atlas, geometry/contain fitting, provenance, crop regions, missing/corrupt assets, fixed part names, and presentation import boundaries. The existing six a7 asset tests and six theme tests remain. Native CI runs the previous functional suite against the real presentation; all six pages; Home at 1440 × 1280, 1440 × 1000, 1240 × 880, and 980 × 700; full-scene ratio/coverage; complete captions; real material loading; disabled initial Play; responsive arrangement; scroll access; style isolation; and missing-art fallback. Checks repeat inside the Windows executable.

CI publishes normal screenshot/result artifacts and emits a reduced real, fictional-fixture-only Home screenshot to its job log for visual review. Defining these checks is not evidence they passed; use the exact commit's completed workflow status and PR report.

Actual user Windows visual acceptance and live game launch remain separate from tests with fictional realms and mocked services.
