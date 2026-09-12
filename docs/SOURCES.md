# Source notes

Reviewed 2026-09-12. The exact candidate source revisions are stored in
`hearthkeeper/data/realm.lock.json`; use them instead of silently tracking moving
branches. No matching-stack build or gameplay certification is implied.

- [AzerothCore client setup](https://www.azerothcore.org/wiki/client-setup)
  and [build numbers](https://www.azerothcore.org/wiki/realmlist): original 3.3.5a / 12340.
- [Playerbots README](https://github.com/mod-playerbots/mod-playerbots): requires
  its AzerothCore fork's Playerbot branch; standard AzerothCore is not the module's target.
- [Individual Progression](https://github.com/ZhengPeiRu21/mod-individual-progression),
  [installation](https://github.com/ZhengPeiRu21/mod-individual-progression/wiki/How-to-Install),
  and [configuration](https://github.com/ZhengPeiRu21/mod-individual-progression/blob/977e2005bacf97f35e506eb27b8af6b2ea1136af/conf/individualProgression.conf.dist):
  personal progression, persisted player settings, optional DBC/client patches.
- [AzerothCore PlayerDump source](https://github.com/azerothcore/azerothcore-wotlk/blob/master/src/server/game/Tools/PlayerDump.cpp):
  reviewed fixed table list omits character_settings. This is a source observation,
  not a live pdump test of every fork or a promise that upstream will never change.
- [character_settings](https://www.azerothcore.org/wiki/character_settings),
  [item_instance](https://www.azerothcore.org/wiki/item_instance),
  [item_template](https://www.azerothcore.org/wiki/item_template), and
  [quest_template](https://www.azerothcore.org/wiki/quest_template): adapter references.
- [Pinned character schemas](https://github.com/mod-playerbots/azerothcore-wotlk/tree/06234df3d5ab26c93f4f1f06f3edb828b73ecd3c/data/sql/base/db_characters):
  checked pet/mail identifier relationships. The small SQLite fixture is authored
  test data and is not a complete copy of these schemas.
- [WoWee](https://github.com/Kelsidavis/WoWee),
  [build guide](https://github.com/Kelsidavis/WoWee/blob/master/BUILD_INSTRUCTIONS.md),
  [expansion guide](https://github.com/Kelsidavis/WoWee/blob/master/EXPANSION_GUIDE.md), and
  [changelog](https://github.com/Kelsidavis/WoWee/blob/master/CHANGELOG.md): native
  experimental client, WotLK profile, extracted assets, evolving addon compatibility,
  and an experimental editor whose formats still need evaluation.
- [PyMySQL](https://pypi.org/project/PyMySQL/) and
  [connection options](https://pymysql.readthedocs.io/en/latest/modules/connections.html):
  optional 1.2.0 connector, read-only SQL session and verified TLS configuration.
- [OpenAI sandbox guidance](https://learn.chatgpt.com/docs/sandboxing): use enforced
  task boundaries; available controls depend on the execution environment.

Hearthkeeper's architecture, fictional content, preservation policies, and roadmap
are proposals for this project, not capabilities attributed to the upstream projects.
