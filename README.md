# AWXE's Formable Nations × Kaiserredux compatibility patch

This makes **[awxe's Formable Nations](https://steamcommunity.com/sharedfiles/filedetails/?id=3677761082)** run correctly on **Kaiserredux**. You still play AWXE's own mod, with all of its decisions, names, flags, icons and game rules. The patch only fixes what breaks when the two are loaded together.

AWXE's licence doesn't allow its files to be redistributed, so this repository doesn't ship a ready-made patch. It contains a script that builds the patch on your computer from your own copies of both mods.

## Why the two mods don't work together as they are

| Problem | Effect in game |
|---|---|
| Kaiserredux discards the decision, scripted trigger, game rule, on_action, country and flag files of any mod loaded **before** it | AWXE's decisions and game rules disappear completely |
| AWXE's decisions use vanilla state IDs. Kaiserredux's map is different (Vienna is 1137 and Prague is 1129) | Requirements, highlighted areas, cores and capitals point at the wrong places |
| AWXE uses vanilla tags. Some don't exist in Kaiserredux (`SOV`, `RAJ`, `YUG`, ...) and some mean a different country (`MAL` is Mali, `MAD` is the Kingdom of India, `SIC` is the Two Sicilies) | The wrong countries can form a nation, or no country can |
| AWXE checks control with vanilla's `controls_or_subject_of` trigger, which Kaiserredux doesn't have (it has `is_controlled_by_ROOT_or_subject`) | Every territorial requirement fails |
| Names and flags exist only for the 4 vanilla ideologies. Kaiserredux has 10 | Formed nations show raw keys like `FORM_BEN_syndicalist` and the wrong flag |
| AWXE's `cosmetic.txt` replaces Kaiserredux's | Kaiserredux's own cosmetic tags lose their map colours |
| Kaiserredux adds the `india` and `central_america` continents and moves some states to other continents | Continent-wide formables (Africa, Asia, the Americas, ...) check the wrong areas |

## What the patch does

- **Rewrites state IDs** by comparing the two maps pixel by pixel, not by ID or colour, because Kaiserredux reuses some of both for different places. When a vanilla state is split into several Kaiserredux states, you must control all of them. Capitals move to the Kaiserredux state with the main city.
- **Rewrites tags**. A tag stays the same where Kaiserredux has the same country. Otherwise it is replaced by the Kaiserredux country or countries that take its place: `SOV` becomes the Russian successor states, `RAJ` the Indian ones, `YUG` Serbia, `MAL` Malaya, and so on. Tags with no counterpart, such as Pakistan or Saxony, simply never match.
- **Rewrites continent checks** so they cover exactly the states vanilla puts on that continent, and moves victory points and province names to the matching Kaiserredux provinces.
- **Uses Kaiserredux's state-control trigger** in place of the missing vanilla one.
- **Adds names and flags for every Kaiserredux ideology**, reusing AWXE's own names and flags:

  | Kaiserredux ideology | Uses AWXE's |
  |---|---|
  | Totalist, Syndicalist, Radical Socialist | communist name and flag |
  | Social Democrat, Social Liberal, Market Liberal, Social Conservative | democratic name and flag |
  | Authoritarian Democrat, Paternal Autocrat | non-aligned name and flag |
  | National Populist | fascist name and flag |

- **Merges** AWXE's cosmetic tag colours into Kaiserredux's `cosmetic.txt`.
- **Carries AWXE's scripts and flags itself**, so it works whether AWXE is above or below Kaiserredux in the playset.

Everything else (decision icons, localisation, the main menu banner, the completion sound) still comes from AWXE's mod.

## Building and installing the patch

You need **Python 3** ([python.org](https://www.python.org/downloads/); on Windows, tick "Add Python to PATH"). No extra packages are needed.

1. Subscribe to **Kaiserredux** and **awxe's Formable Nations** on the Steam Workshop. You can also use local copies.
2. Download this repository (green **Code** button, then **Download ZIP**) and extract it.
3. Open a terminal in the extracted folder and run the script. Give it AWXE's folder, Kaiserredux's folder and your HOI4 `mod` folder. On Windows with the default Steam location:

   ```bash
   python tools/make_patch.py "C:/Program Files (x86)/Steam/steamapps/workshop/content/394360/3677761082" "C:/Program Files (x86)/Steam/steamapps/workshop/content/394360/2206134307" --out "C:/Users/YOUR_NAME/Documents/Paradox Interactive/Hearts of Iron IV/mod"
   ```

   Replace `YOUR_NAME` with your Windows user name. `3677761082` is AWXE's mod and `2206134307` is Kaiserredux. On Linux or macOS use `python3` and your own paths. The script writes `awxe_krx_compat/` and `awxe_krx_compat.mod` into the `mod` folder and prints a summary of what it changed.
4. In the launcher, put all three in one playset in this order, with the patch **at the bottom**:
   1. Kaiserredux
   2. awxe's Formable Nations
   3. awxe's Formable Nations - Kaiserredux Compatibility

**Run the script again whenever either mod updates.** It always reads your current copies, and it skips states and tags that a newer Kaiserredux no longer has.

### If something doesn't work

- **No Formable Nations decisions:** check that the patch is the last mod in the playset and that the game rules screen has AWXE's *Formable Nations* group.
- **The launcher doesn't list the patch:** open `mod/awxe_krx_compat.mod` and set `path=` to the full path of the `awxe_krx_compat` folder.
- **Script errors:** `Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log` lists every problem. Lines mentioning `awxe_form_nations` point at AWXE's decisions.

## Differences from playing AWXE on vanilla

- The world at the start differs, so some formables are easier or harder. In Kaiserredux, Bengal starts with all the land the *Bengal Empire* asks for and can proclaim it on day one. Hungary starts with all the land for the *Kingdom of Hungary* but, as Austria's subject, can only proclaim it once independent (or right away with AWXE's puppet game rule on).
- Candidates that don't exist in Kaiserredux can't form anything, but every formable keeps at least one Kaiserredux candidate. Kerguelen isn't on Kaiserredux's map, so it is left out of the formables that include it.
- Where Kaiserredux splits a vanilla state, you need the whole area, not just part of it.

## For maintainers

```
tools/make_patch.py     builds the patch from AWXE's mod and Kaiserredux (no extra packages)
tools/build_maps.py     rebuilds data/ from a vanilla HOI4 install and Kaiserredux (needs numpy and Pillow)
tools/tag_overrides.py  hand-checked tag mappings that build_maps.py can't work out itself
tools/pdxscript.py      HOI4 script parser that keeps comments and formatting
tools/hoi4data.py       readers for map, state, tag and country data
data/statemap.json      vanilla state -> Kaiserredux states and capital
data/provincemap.json   vanilla province -> Kaiserredux province
data/continentmap.json  vanilla continent -> Kaiserredux continents, plus states to add and remove
data/tagmap.json        vanilla tag -> Kaiserredux tags
```

When Kaiserredux changes its map or tags, rebuild the tables:

```bash
python3 tools/build_maps.py "/path/to/Hearts of Iron IV" "/path/to/Kaiserredux"
```

The current tables were built from vanilla 1.19.4 and the Kaiserredux development version of 28 October 2026.

## Licence and credits

*awxe's Formable Nations* is by AWXE and is licensed CC BY-NC-ND 4.0. Its terms forbid reuploading, redistributing or publishing edited versions without written permission. This repository contains none of AWXE's files, only the patch script and map tables. The patch you build contains modified copies of AWXE's files, so **keep it for your own use and don't upload it** to the Workshop or anywhere else unless AWXE gives permission. Kaiserredux is by the Kaiserredux team.
