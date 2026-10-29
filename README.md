# Formable Nations: Kaiserredux

A Hearts of Iron IV submod that adds **34 decision-based formable nations to Kaiserredux**, in the style of AWXE's *Formable Nations*. Examples are the Nordic/Kalmar Union, the Danubian Federation, Yugoslavia, the Holy Roman Empire, the Roman and Byzantine Empires, the Arab Federation, Turan, Gran Colombia, Tawantinsuyu and the United States of Africa.

AWXE's mod is built for vanilla tags, states and ideologies, which Kaiserredux replaces, so it can't simply be loaded on top. This submod was written from scratch against Kaiserredux's own data:

- **Tags**: every candidate nation is a real Kaiserredux tag (`SRI`, `NFA`, `GAL`, `MAF`, `LEP`, ...).
- **States**: every state ID comes from Kaiserredux's `history/states` and map. Kaiserredux's map differs from vanilla (for example Vienna is state 1137 and Prague is 1129).
- **Ideologies**: each nation gets names for all 10 Kaiserredux ideologies, from totalist to national populist. A totalist Danubian state is the *Danubian Union of Councils*, a paternal autocrat one the *Danubian Monarchy*.
- **No overlap with Kaiserredux content**: several Kaiserredux paths already form their own versions of these nations (Kalmar Union, Transcaucasia, Polish-Lithuanian Commonwealth, Peru-Bolivian Confederation, ...). A decision is hidden when your country already has the matching Kaiserredux cosmetic tag. The submod also leaves out plain national reunifications that Kaiserredux handles in depth (Italy, Germany, China, India, Central America and the United States).
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
   }
   ```
3. In the launcher, add it to your playset **below Kaiserredux**.

`descriptor.mod` lists Kaiserredux as a dependency by its mod name, `Kaiserredux`. If your copy of Kaiserredux shows a different name in the launcher, change the dependency to match.

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

The idea of decision-based formables comes from AWXE's *Formable Nations* (and TRt56's original). This submod contains none of their files. The decisions, localisation and flags here are new, and the flags are simple generated designs. If you publish it on the Workshop, credit AWXE for the concept and don't use their name, title or assets without permission. Kaiserredux is by the Kaiserredux team.
