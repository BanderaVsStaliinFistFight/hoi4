#!/usr/bin/env python3
"""Check the generated submod against a Kaiserredux checkout or install.

Usage:  python3 tools/validate.py /path/to/Kaiserredux

The Kaiserredux path is the folder holding its descriptor.mod: a Steam Workshop
folder (steamapps/workshop/content/394360/<id>) or a git clone. Run this after
every Kaiserredux update. State IDs and tags change between versions, and a
stale ID silently makes a decision impossible to take.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'formable_nations_krx')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from generate import IDEOLOGY_GROUPS, PREFIX, SIZES  # noqa: E402

errors, warnings = [], []


def read(path):
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        return f.read()


def strip_comments(text):
    return re.sub(r'#[^\n]*', '', text)


def load_loc(paths):
    loc = {}
    for path in paths:
        for line in read(path).splitlines():
            m = re.match(r'\s*([A-Za-z0-9_.\-]+):\d*\s*"', line)
            if m:
                loc.setdefault(m.group(1), path)
    return loc


def main(krx):
    if not os.path.isfile(os.path.join(krx, 'descriptor.mod')):
        sys.exit(f'{krx} does not look like a mod folder (no descriptor.mod)')

    spec = json.load(open(os.path.join(ROOT, 'tools', 'formables.json'), encoding='utf-8'))['formables']
    names = json.load(open(os.path.join(ROOT, 'tools', 'krx_state_names.json'), encoding='utf-8'))

    # ---- Kaiserredux data
    tags = set()
    for path in glob.glob(os.path.join(krx, 'common', 'country_tags', '*.txt')):
        tags |= set(re.findall(r'^\s*([A-Z0-9]{3})\s*=', strip_comments(read(path)), re.M))
    states = {}
    for path in glob.glob(os.path.join(krx, 'history', 'states', '*.txt')):
        text = strip_comments(read(path))
        m = re.search(r'\bid\s*=\s*(\d+)', text)
        if m:
            states[int(m.group(1))] = path
    ideologies = set(re.findall(r'^\t([a-z_]+) = \{', read(os.path.join(krx, 'common', 'ideologies', '00_ideologies.txt')), re.M))
    krx_loc = load_loc(glob.glob(os.path.join(krx, 'localisation', '**', '*.yml'), recursive=True))
    krx_state_loc = {}
    for path in glob.glob(os.path.join(krx, 'localisation', '**', '*.yml'), recursive=True):
        for m in re.finditer(r'^\s*STATE_(\d+):\d*\s*"([^"]*)"', read(path), re.M):
            krx_state_loc.setdefault(int(m.group(1)), m.group(2))

    print(f'Kaiserredux: {len(tags)} tags, {len(states)} states, ideologies: {", ".join(sorted(ideologies))}')

    ours = {i for group in IDEOLOGY_GROUPS.values() for i in group}
    for i in sorted(ideologies - ours):
        errors.append(f'Kaiserredux ideology "{i}" has no cosmetic name group in generate.py')
    for i in sorted(ours - ideologies):
        errors.append(f'ideology "{i}" in generate.py does not exist in Kaiserredux')

    # ---- generated script
    script_files = glob.glob(os.path.join(MOD, '**', '*.txt'), recursive=True)
    defined_triggers, defined_effects = set(), set()
    for path in script_files:
        text = strip_comments(read(path))
        text_no_strings = re.sub(r'"[^"\n]*"', '""', text)
        depth = 0
        for ch in text_no_strings:
            depth += ch == '{'
            depth -= ch == '}'
            if depth < 0:
                break
        if depth != 0:
            errors.append(f'{os.path.relpath(path, ROOT)}: unbalanced braces ({depth:+d})')
        top = set(re.findall(r'^([A-Za-z0-9_]+) = \{', text, re.M))
        if '/scripted_triggers/' in path.replace(os.sep, '/'):
            defined_triggers |= top
        if '/scripted_effects/' in path.replace(os.sep, '/'):
            defined_effects |= top

    all_script = '\n'.join(strip_comments(read(p)) for p in script_files)
    for ref in sorted(set(re.findall(r'\b(FNKX_[A-Za-z0-9_]+) = yes', all_script))):
        if ref not in defined_triggers and ref not in defined_effects:
            errors.append(f'scripted trigger/effect {ref} is used but never defined')
    for ref in sorted(set(re.findall(r'^\s*(?:original_tag|tag) = ([A-Z0-9]{3})\b', all_script, re.M))):
        if ref not in tags:
            errors.append(f'tag {ref} does not exist in Kaiserredux')
    used_states = {int(s) for s in re.findall(r'\bstate = (\d+)', all_script)}
    used_states |= {int(s) for s in re.findall(r'^\s*(\d+) = \{', all_script, re.M)}
    for s in sorted(used_states - set(states)):
        errors.append(f'state {s} ({names.get(str(s), "?")}) does not exist in Kaiserredux')

    # Same ID, different name: Kaiserredux probably renumbered or split a state.
    for sid, recorded in sorted(names.items(), key=lambda kv: int(kv[0])):
        current = krx_state_loc.get(int(sid))
        if current and not current.startswith('$') and current != recorded:
            warnings.append(f'state {sid} was "{recorded}", Kaiserredux now calls it "{current}" - check the regions using it')

    # ---- localisation
    loc_path = os.path.join(MOD, 'localisation', 'english', 'FNKX_l_english.yml')
    with open(loc_path, 'rb') as f:
        if not f.read(3) == b'\xef\xbb\xbf':
            errors.append('FNKX_l_english.yml must be UTF-8 with BOM')
    loc_lines = read(loc_path).splitlines()
    if loc_lines[0].strip() != 'l_english:':
        errors.append('FNKX_l_english.yml must start with l_english:')
    our_loc = {}
    for line in loc_lines[1:]:
        m = re.match(r'\s*([A-Za-z0-9_.\-]+):\d*\s*"(.*)"\s*$', line)
        if m:
            if m.group(1) in our_loc:
                errors.append(f'duplicate localisation key {m.group(1)}')
            our_loc[m.group(1)] = m.group(2)
        elif line.strip() and not line.strip().startswith('#'):
            errors.append(f'unparseable localisation line: {line!r}')
    for key in our_loc:
        if key in krx_loc and not key.startswith('RULE_GROUP_'):
            warnings.append(f'localisation key {key} is also defined by Kaiserredux ({os.path.relpath(krx_loc[key], krx)})')

    needed = {f'{PREFIX}_formable_nations', f'{PREFIX}_held_by_ROOT_tt', f'{PREFIX}_region_cores_tt',
              f'{PREFIX}_unification_spirit', 'fnkx.1.t', 'fnkx.1.d', 'fnkx.1.a', 'fnkx.1.b'}
    needed |= set(re.findall(r'"(RULE_[A-Z0-9_]+)"', all_script))
    for f in spec:
        cos = f'{PREFIX}_{f["id"]}'
        needed |= {f'{PREFIX}_form_{f["id"]}', f'{PREFIX}_form_{f["id"]}_desc', cos, cos + '_DEF', cos + '_ADJ'}
        for i in ideologies:
            needed |= {f'{cos}_{i}', f'{cos}_{i}_DEF', f'{cos}_{i}_ADJ'}
        for folder in SIZES:
            if not os.path.isfile(os.path.join(MOD, 'gfx', 'flags', folder, cos + '.tga')):
                errors.append(f'missing flag gfx/flags/{folder + "/" if folder else ""}{cos}.tga')
        for c in f['hide_cosmetics']:
            if not any(k == c or k.startswith(c + '_') for k in krx_loc):
                warnings.append(f'{f["id"]}: Kaiserredux cosmetic tag {c} not found in its localisation (renamed?)')
        for t in f['hide_tags']:
            if t not in tags:
                errors.append(f'{f["id"]}: hide_tags entry {t} does not exist in Kaiserredux')
    for key in sorted(needed - set(our_loc)):
        errors.append(f'missing localisation key {key}')

    # ---- sprites that must come from Kaiserredux itself (vanilla ones are not checked)
    gfx = '\n'.join(read(p) for p in glob.glob(os.path.join(krx, 'interface', '*.gfx')))
    for sprite in ['GFX_decision_cat_picture_unification_conference', 'GFX_news_event_ITA_big_crowd']:
        if sprite not in gfx:
            errors.append(f'sprite {sprite} is no longer defined by Kaiserredux')

    # ---- Kaiserredux scripted triggers the submod relies on
    krx_script = glob.glob(os.path.join(krx, 'common', '**', '*.txt'), recursive=True)
    krx_triggers = '\n'.join(read(p) for p in krx_script if '/scripted_triggers/' in p.replace(os.sep, '/'))
    for trigger in ['wants_world_news']:
        if not re.search(rf'^{trigger} = \{{', krx_triggers, re.M):
            errors.append(f'Kaiserredux no longer defines the scripted trigger {trigger}')

    # ---- clashes with Kaiserredux's own script
    for path in krx_script:
        if re.search(r'\bFNKX_', read(path)):
            warnings.append(f'Kaiserredux file {os.path.relpath(path, krx)} mentions FNKX_ (name clash?)')

    for w in warnings:
        print('WARNING:', w)
    for e in errors:
        print('ERROR:', e)
    print(f'{len(spec)} formables checked: {len(errors)} error(s), {len(warnings)} warning(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
