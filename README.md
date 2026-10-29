# Formable Nations: Kaiserredux

A Hearts of Iron IV submod that adds **207 decision-based formable nations to Kaiserredux**, covering every nation in AWXE's *Formable Nations* except one joke entry. They range from regional unions (the Nordic Union, Danubian Federation, Gran Colombia, United States of Africa) to restored empires (Rome, Byzantium, the Ottomans, the Mughals, the Mali Empire, the Golden Horde, the Qing) and "Greater" states (Greater Finland, Greater Greece, Greater Armenia). There are also colonial empires (Spanish, Portuguese, Dutch) and continent-spanning ones, up to a single world government.

AWXE's mod is built for vanilla tags, states and ideologies, which Kaiserredux replaces, so it can't simply be loaded on top. This submod was written from scratch against Kaiserredux's own data:

- **Tags**: every candidate nation is a real Kaiserredux tag (`SRI`, `NFA`, `GAL`, `MAF`, `LEP`, ...).
- **States**: every state ID comes from Kaiserredux's `history/states` and map. Kaiserredux's map differs from vanilla (for example Vienna is state 1137 and Prague is 1129).
- **Ideologies**: each nation has its own name, and where needed its own adjective, for every one of the 10 Kaiserredux ideologies. The names follow Kaiserredux's conventions: "People's Republic" for totalists, communes and councils for syndicalists, "State" for national populists. Real historical names are used where one exists. Yugoslavia, for example, is the *Federal People's Republic*, the *Union of Yugoslav Communes*, the *Socialist Federal Republic*, *Democratic Federal Yugoslavia* or the *Kingdom of Serbs, Croats and Slovenes*, depending on who rules it. Iran can be the *Guarded Domains of Iran*, and a socialist Holy Roman Empire calls itself the *Central European People's Republic*. [FORMABLES.md](FORMABLES.md) lists every name.
- **Steps aside for Kaiserredux content**: many Kaiserredux paths already form their own versions of these nations (Kalmar Union, Golden Horde, North Sea Empire, Great Qing, Ottoman Caliphate, Polish-Lithuanian Commonwealth, ...). A decision is hidden when your country already has the matching Kaiserredux cosmetic tag, or already is the matching Kaiserredux tag (for example `CEN` for Central America or `INC` for Indochina).
- **Nothing on day one**: no decision can be taken at the 1936 start. Each one needs land the country doesn't yet hold. The German, Dutch and other colonial empires also require their colonies to be ruled directly, not through puppets.
- **No vanilla or Kaiserredux files are overwritten**: everything uses the `FNKX_` prefix and the `fnkx` event namespace.

See **[FORMABLES.md](FORMABLES.md)** for the full list: who can proclaim each nation, required states, cost and territory.

## How it plays

A **Formable Nations** category appears in the decisions tab. A decision becomes available once you own and control its key states, either yourself or through a subject. You must also be independent, not capitulated and not in a civil war. Proclaiming a nation:

1. annexes any of your subjects that belong to it (for example a puppet Croatia when you proclaim Yugoslavia),
2. renames you and changes your flag (a cosmetic tag, so your focus tree and events stay the same),
3. gives you cores on every state of the new nation you own and claims on the rest,
4. grants *Euphoria of Unification* (+10% stability, +5% war support, +10% political power for one year),
5. announces it to the world in a news event, if you have Kaiserredux world news switched on.

Each nation can be proclaimed once per game, by one country.

### Game rules

Both rules sit in the **Formable Nations** group of the game rules screen.

| Rule | Options |
|---|---|
| Formable Nations | **Historical Candidates** (default): only the listed nations. **Historical and Regional**: also any nation whose capital lies in the territory. **Disabled**. |
| AI Formable Nations | **Allowed** (default) or **Players Only**. |

## Installing

The submod needs **Kaiserredux** and targets HOI4 **1.19.x**, the version the current Kaiserredux supports.

1. Copy the `formable_nations_krx` folder into `Documents/Paradox Interactive/Hearts of Iron IV/mod/`.
2. Next to it, create `formable_nations_krx.mod` with:
   ```
   name="Formable Nations: Kaiserredux"
   path="mod/formable_nations_krx"
   supported_version="1.19.*"
   dependencies={
   	"Kaiserredux"
   	"KaiserreduX"
   	"Kaiserredux: A Kaiserreich Expansion"
   }
   ```
3. In the launcher, add it to the same playset as Kaiserredux and drag it **below Kaiserredux**, so it loads after it.

### If the decisions don't appear

Every country should see at least the **Proclaim a World Government** decision in a **Formable Nations** category. If there is no such category:

1. **Check the game rules screen** when starting a game. If there is no **Formable Nations** group, the submod's scripts are not loaded.
2. **Check the load order.** Kaiserredux replaces the whole decisions, scripted triggers, events and game rules folders of every mod loaded *before* it. The submod must sit **below** Kaiserredux in the playset. The dependency list above makes the launcher sort it automatically, but only if one of the names matches the name your launcher shows for Kaiserredux exactly. If yours differs, add that name to the dependencies in both `.mod` files and drag the submod below Kaiserredux by hand.
3. **Check the folder layout.** `mod/formable_nations_krx.mod` and `mod/formable_nations_krx/descriptor.mod` must both exist. If you see `mod/formable_nations_krx/formable_nations_krx/`, the ZIP was extracted one level too deep.
4. **Check the path.** If the launcher doesn't list the submod at all, change `path=` in `formable_nations_krx.mod` to the full path, for example `path="C:/Users/<you>/Documents/Paradox Interactive/Hearts of Iron IV/mod/formable_nations_krx"`.
5. **Check the error log.** `Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log` lists every script problem; lines mentioning `FNKX` point at this submod.

## Editing and updating

Everything in `formable_nations_krx/` except `descriptor.mod` is generated, so don't edit it by hand:

```
tools/formables.json      the nations: names, eligible tags, required states, territory, flags
tools/krx_state_names.json  Kaiserredux state names, used for comments and docs
tools/generate.py         writes the mod (script, localisation, flags, thumbnail) and FORMABLES.md
tools/validate.py         checks the generated mod against a Kaiserredux install
```

After changing `formables.json`, regenerate (needs Python 3 and Pillow):

```bash
python3 tools/generate.py
```

**After every Kaiserredux update**, validate against your Kaiserredux folder (the Workshop folder `steamapps/workshop/content/394360/<id>` or a git clone):

```bash
python3 tools/validate.py "/path/to/Kaiserredux"
```

It flags state IDs and tags that no longer exist, states that were renamed (often a sign of renumbering), missing localisation or flags, Kaiserredux cosmetic tags that have disappeared, ideology changes, and unbalanced braces.

## Credits

The idea of decision-based formables, and the list of nations to cover, come from AWXE's *Formable Nations* (and TRt56's original). This submod contains none of their files. AWXE's licence forbids reusing any part of their mod, so every decision, requirement, territory, name, description and flag here was written independently for Kaiserredux, and the flags are simple generated designs. If you publish it on the Workshop, credit AWXE for the concept and don't use their name, title or assets without permission. Kaiserredux is by the Kaiserredux team.
