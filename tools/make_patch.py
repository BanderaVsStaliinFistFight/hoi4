"""Build a patch that makes AWXE's Formable Nations work with Kaiserredux.

AWXE's mod is written for the vanilla map, vanilla tags and vanilla
ideologies. This script reads your copy of AWXE's mod and your copy of
Kaiserredux and writes a small patch mod that loads after both and:

  * rewrites every state ID in AWXE's decisions to the matching Kaiserredux
    state(s), every candidate tag to the matching Kaiserredux tag(s), every
    continent check to Kaiserredux's continents and every province ID used for
    victory points and province names (tables in data/, see build_maps.py);
  * points AWXE's state-control check at Kaiserredux's equivalent trigger,
    which Kaiserredux has under another name;
  * gives every formable name and flag a version for each Kaiserredux ideology;
  * merges AWXE's cosmetic tag colours into Kaiserredux's cosmetic.txt instead
    of replacing it;
  * carries AWXE's scripts and flags itself, because Kaiserredux discards
    other mods' files in those folders when it loads after them.

The patch is built from your own copies of both mods, for your own use. Don't
upload the result: AWXE's licence does not allow redistributing its files.

Usage (needs Python 3):
    python3 tools/make_patch.py <AWXE mod folder> <Kaiserredux folder> [--out DIR] [--zip]
"""
import argparse
import collections
import json
import os
import re
import shutil
import sys
import zipfile

import hoi4data as hd
import pdxscript as px

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')

PATCH_FOLDER = 'awxe_krx_compat'
PATCH_NAME = "awxe's Formable Nations - Kaiserredux Compatibility"
PATCH_VERSION = '1.0'
KRX_NAMES = ['Kaiserredux', 'KaiserreduX', 'Kaiserredux: A Kaiserreich Expansion']

# Which vanilla ideology's names and flags each Kaiserredux ideology uses,
# following Kaiserreich's own grouping (socialist / democratic / authoritarian / national populist).
IDEOLOGIES = {
    'totalist': 'communism',
    'syndicalist': 'communism',
    'radical_socialist': 'communism',
    'social_democrat': 'democratic',
    'social_liberal': 'democratic',
    'market_liberal': 'democratic',
    'social_conservative': 'democratic',
    'authoritarian_democrat': 'neutrality',
    'paternal_autocrat': 'neutrality',
    'national_populist': 'fascism',
}
VANILLA_IDEOLOGIES = ('communism', 'democratic', 'fascism', 'neutrality')
NAME_SUFFIXES = ('', '_DEF', '_ADJ')
FLAG_DIRS = ('gfx/flags', 'gfx/flags/medium', 'gfx/flags/small')

TRIGGER_BLOCKS = {
    'visible', 'available', 'allowed', 'limit', 'trigger', 'potential', 'highlight_states',
    'highlight_states_trigger', 'target_trigger', 'target_root_trigger', 'ai_will_do',
    'custom_trigger_tooltip', 'count_triggers', 'cancel_trigger', 'remove_trigger',
}
EFFECT_BLOCKS = {
    'complete_effect', 'remove_effect', 'timeout_effect', 'cancel_effect', 'effect', 'immediate',
    'hidden_effect', 'option',
}
TAG_TRIGGERS = {'original_tag', 'tag', 'is_subject_of', 'country_exists'}
STATE_TRIGGERS = {'controls_state', 'owns_state', 'has_full_control_of_state'}
STATE_EFFECTS = {'add_state_core', 'add_state_claim', 'remove_state_core', 'remove_state_claim', 'transfer_state'}
PROVINCE_BLOCKS = {'set_victory_points': 'province', 'set_province_name': 'id'}
LIST_PARENTS = {'OR', 'highlight_state_targets'}
NUM_RE = re.compile(r'\d+$')
TAG_RE = re.compile(r'[A-Z][A-Z0-9]{2}$')


def child_context(key, ctx):
    if key in TRIGGER_BLOCKS or (key or '').startswith(('any_', 'all_')):
        return 'trigger'
    if key in EFFECT_BLOCKS:
        return 'effect'
    return ctx


def indent_at(src, pos):
    line_start = src.rfind('\n', 0, pos) + 1
    lead = src[line_start:pos]
    return '\n' + lead if lead.strip() == '' else ' '


class Rewriter:
    """Rewrites vanilla references in AWXE's scripts to Kaiserredux ones."""

    def __init__(self, maps, krx):
        self.states = {int(k): v for k, v in maps['states']['states'].items()}
        self.unmapped = set(maps['states']['unmapped'])
        self.provinces = {int(k): v for k, v in maps['provinces'].items()}
        self.continents = maps['continents']
        self.tags = maps['tags']
        self.krx = krx
        self.stats = collections.Counter()
        self.notes = collections.defaultdict(set)

    # -- lookups -------------------------------------------------------------
    def states_for(self, sid):
        if sid in self.states:
            return [k for k in self.states[sid]['to'] if k in self.krx['states']]
        if sid not in self.unmapped:
            self.notes['state IDs that are not vanilla states (dropped)'].add(sid)
        else:
            self.notes['vanilla states not on the Kaiserredux map (dropped)'].add(sid)
        return []

    def capital_for(self, sid):
        cap = self.states.get(sid, {}).get('capital')
        if cap not in self.krx['states']:
            self.notes['capitals with no Kaiserredux state (left unchanged)'].add(sid)
            return sid
        return cap

    def tags_for(self, tag):
        if tag in self.tags:
            mapped = [t for t in self.tags[tag] if t in self.krx['tags']]
        else:
            mapped = [tag] if tag in self.krx['tags'] else []
        if not mapped:
            self.notes['tags with no Kaiserredux counterpart (never match)'].add(tag)
        return mapped

    # -- rewriting -----------------------------------------------------------
    def rewrite(self, src):
        nodes = px.parse(src)
        return self.sequence(src, nodes, 0, len(src), None, None)

    def sequence(self, src, nodes, start, end, ctx, parent):
        out, cur = [], start
        seen = set() if parent in LIST_PARENTS else None
        for n in nodes:
            pieces = self.node(src, n, ctx, parent)
            if seen is not None and not n.is_block:
                texts = [src[n.start:n.end]] if pieces is None else pieces
                kept = []
                for t in texts:
                    norm = ' '.join(t.split())
                    if norm not in seen:
                        seen.add(norm)
                        kept.append(t)
                if pieces is None and len(kept) == 1:
                    continue
                pieces = kept
            if pieces is None:
                continue
            out.append(src[cur:n.start])
            out.append(indent_at(src, n.start).join(pieces))
            cur = n.end
        out.append(src[cur:end])
        return ''.join(out)

    def node(self, src, n, ctx, parent):
        """Replacement text for a node (a list of sibling pieces), or None to keep it."""
        key = n.key
        if n.is_block:
            if key in PROVINCE_BLOCKS:
                for c in n.value:
                    if c.key == PROVINCE_BLOCKS[key] and NUM_RE.match(str(c.value)) \
                            and int(c.value) not in self.provinces:
                        self.stats['province effects dropped'] += 1
                        return []
            body = self.sequence(src, n.value, n.open, n.close, child_context(key, ctx), key)
            if key and NUM_RE.match(key) and n.op == '=':
                ks = self.states_for(int(key))
                if ks != [int(key)]:
                    return self.state_scope(ks, body, ctx)
            if body == src[n.open:n.close]:
                return None
            return [src[n.start:n.open] + body]

        value = n.value
        if key is None or n.op != '=':
            return None
        if key == self.krx['trigger_from']:
            self.stats['state-control checks renamed'] += 1
            return [f'{self.krx["trigger_to"]} = {value}']
        if key == 'state' and NUM_RE.match(value):
            sid = int(value)
            if parent == 'set_capital':
                cap = self.capital_for(sid)
                self.stats['capitals moved'] += cap != sid
                return None if cap == sid else [f'state = {cap}']
            ks = self.states_for(sid)
            if ks == [sid]:
                return None
            self.stats['state references remapped'] += 1
            items = [f'state = {k}' for k in ks]
            if parent in LIST_PARENTS:
                return items
            if not items:
                return [] if ctx == 'effect' else ['always = no']
            return items if len(items) == 1 else ['OR = { ' + ' '.join(items) + ' }']
        if key in STATE_TRIGGERS and NUM_RE.match(value):
            ks = self.states_for(int(value))
            if ks == [int(value)]:
                return None
            self.stats['state references remapped'] += 1
            items = [f'{key} = {k}' for k in ks]
            return items if len(items) <= 1 else ['AND = { ' + ' '.join(items) + ' }']
        if key in STATE_EFFECTS and NUM_RE.match(value):
            ks = self.states_for(int(value))
            if ks == [int(value)]:
                return None
            self.stats['state references remapped'] += 1
            return [f'{key} = {k}' for k in ks]
        if key in TAG_TRIGGERS and TAG_RE.match(value):
            ts = self.tags_for(value)
            if ts == [value]:
                return None
            self.stats['tag checks remapped'] += 1
            items = [f'{key} = {t}' for t in ts] or ['always = no']
            return items if parent == 'OR' or len(items) == 1 else ['OR = { ' + ' '.join(items) + ' }']
        if key == 'is_on_continent' and value in self.continents:
            return self.continent(value)
        if parent in PROVINCE_BLOCKS and key == PROVINCE_BLOCKS[parent] and NUM_RE.match(value):
            kp = self.provinces[int(value)]
            self.stats['provinces remapped'] += kp != int(value)
            return None if kp == int(value) else [f'{key} = {kp}']
        return None

    def state_scope(self, ks, body, ctx):
        self.stats['state scopes remapped'] += 1
        parts = [f'{k} = {body}' for k in ks]
        if ctx == 'effect' or len(parts) <= 1:
            return parts
        return ['AND = { ' + ' '.join(parts) + ' }']

    def continent(self, name):
        c = self.continents[name]
        if c['continents'] == [name] and not c['add'] and not c['remove']:
            return None
        self.stats['continent checks remapped'] += 1
        expr = ' '.join(f'is_on_continent = {k}' for k in c['continents'])
        if len(c['continents']) > 1:
            expr = f'OR = {{ {expr} }}'
        if c['remove']:
            expr = f'AND = {{ {expr} NOT = {{ OR = {{ {" ".join(f"state = {s}" for s in c["remove"])} }} }} }}'
        if c['add']:
            expr = f'OR = {{ {expr} {" ".join(f"state = {s}" for s in c["add"])} }}'
        return [expr]


# -- Kaiserredux data ---------------------------------------------------------
def read_descriptor(folder):
    path = os.path.join(folder, 'descriptor.mod')
    text = hd.read_text(path) if os.path.exists(path) else ''
    field = lambda k: (re.search(rf'^\s*{k}\s*=\s*"([^"]*)"', text, re.M) or [None, None])[1]
    return dict(name=field('name'), version=field('version'), supported_version=field('supported_version'),
                replace_paths=set(re.findall(r'replace_path\s*=\s*"([^"]*)"', text)))


def defined_keys(folder, sub):
    keys = set()
    for root, _, files in os.walk(os.path.join(folder, sub)):
        for f in files:
            if f.endswith('.txt'):
                text = hd.strip_comments(hd.read_text(os.path.join(root, f)))
                keys |= set(re.findall(r'^([A-Za-z_][\w.]*)\s*=\s*\{', text, re.M))
    return keys


def read_krx(folder):
    info = read_descriptor(folder)
    info['tags'] = hd.read_country_tags(folder)
    info['states'] = set(hd.read_states(folder))
    info['provinces'] = set(hd.read_definitions(folder))
    ideologies = []
    for root, _, files in os.walk(os.path.join(folder, 'common', 'ideologies')):
        for f in sorted(files):
            for n in px.parse(hd.read_text(os.path.join(root, f))):
                if n.key == 'ideologies' and n.is_block:
                    ideologies += [c.key for c in n.value if c.is_block]
    info['ideologies'] = ideologies
    triggers = defined_keys(folder, os.path.join('common', 'scripted_triggers'))
    # AWXE uses vanilla's controls_or_subject_of, which Kaiserredux has as is_controlled_by_ROOT_or_subject.
    info['trigger_from'] = info['trigger_to'] = None
    if 'controls_or_subject_of' not in triggers and 'is_controlled_by_ROOT_or_subject' in triggers:
        info['trigger_from'], info['trigger_to'] = 'controls_or_subject_of', 'is_controlled_by_ROOT_or_subject'
    info['define_trigger'] = not triggers & {'controls_or_subject_of', 'is_controlled_by_ROOT_or_subject'}
    return info


def load_maps():
    def load(name):
        with open(os.path.join(DATA, name), encoding='utf-8') as f:
            return json.load(f)
    return dict(states=load('statemap.json'), provinces=load('provincemap.json'),
                continents=load('continentmap.json'), tags=load('tagmap.json'))


# -- output -------------------------------------------------------------------
def write(path, text, bom=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='\n') as f:
        f.write(text)


def merge_cosmetics(krx_text, awxe_text):
    """Kaiserredux's cosmetic.txt plus AWXE's entries for tags Kaiserredux doesn't define."""
    krx_keys = {n.key for n in px.parse(krx_text)}
    extra = [awxe_text[n.start:n.end] for n in px.parse(awxe_text) if n.key and n.key not in krx_keys]
    return krx_text.rstrip() + '\n\n# Added by the AWXE Formable Nations compatibility patch\n' + '\n'.join(extra) + '\n', len(extra)


def cosmetic_tags(awxe, scripts, krx_tags):
    found = set()
    for text in scripts.values():
        found |= set(re.findall(r'\bset_cosmetic_tag\s*=\s*([A-Za-z0-9_]+)', hd.strip_comments(text)))
    flag_dir = os.path.join(awxe, 'gfx', 'flags')
    if os.path.isdir(flag_dir):
        for f in os.listdir(flag_dir):
            m = re.match(r'(.+?)(?:_(?:%s))?\.tga$' % '|'.join(VANILLA_IDEOLOGIES), f)
            if m:
                found.add(m.group(1))
    return sorted(t for t in found if t not in krx_tags)


def localisation(awxe, cosmetics, ideologies):
    """Per language, Kaiserredux-ideology name keys that reuse AWXE's vanilla-ideology names."""
    keys = collections.defaultdict(set)
    for root, _, files in os.walk(os.path.join(awxe, 'localisation')):
        for f in files:
            m = re.search(r'_l_(\w+)\.yml$', f)
            if m:
                text = hd.read_text(os.path.join(root, f))
                keys[m.group(1)] |= set(re.findall(r'^\s*([A-Za-z0-9_.\-]+):\d*\s*"', text, re.M))
    out = {}
    for lang, have in sorted(keys.items()):
        lines = [f'l_{lang}:']
        for cos in cosmetics:
            for suffix in NAME_SUFFIXES:
                for krx_ideology in ideologies:
                    preferred = IDEOLOGIES.get(krx_ideology, 'neutrality')
                    for van in (preferred,) + VANILLA_IDEOLOGIES:
                        if f'{cos}_{van}{suffix}' in have:
                            lines.append(f' {cos}_{krx_ideology}{suffix}:0 "${cos}_{van}{suffix}$"')
                            break
        if len(lines) > 1:
            out[lang] = '\n'.join(lines) + '\n'
    return out


def flags(awxe, out_mod, cosmetics, ideologies):
    copied = 0
    for sub in FLAG_DIRS:
        src_dir = os.path.join(awxe, *sub.split('/'))
        if not os.path.isdir(src_dir):
            continue
        dst_dir = os.path.join(out_mod, *sub.split('/'))
        os.makedirs(dst_dir, exist_ok=True)
        present = set(os.listdir(src_dir))
        for cos in cosmetics:
            if f'{cos}.tga' in present:
                shutil.copyfile(os.path.join(src_dir, f'{cos}.tga'), os.path.join(dst_dir, f'{cos}.tga'))
                copied += 1
            for krx_ideology in ideologies:
                preferred = IDEOLOGIES.get(krx_ideology, 'neutrality')
                for van in (preferred,) + VANILLA_IDEOLOGIES:
                    if f'{cos}_{van}.tga' in present:
                        shutil.copyfile(os.path.join(src_dir, f'{cos}_{van}.tga'),
                                        os.path.join(dst_dir, f'{cos}_{krx_ideology}.tga'))
                        copied += 1
                        break
    return copied


CONTROLS_OR_SUBJECT_OF = """# Vanilla's controls_or_subject_of, which AWXE's decisions use and Kaiserredux lacks.
controls_or_subject_of = {
\tcontroller = {
\t\tOR = {
\t\t\ttag = ROOT
\t\t\tis_subject_of = ROOT
\t\t}
\t}
}
"""


def validate(text, krx):
    """References in a rewritten script that Kaiserredux doesn't have."""
    problems = collections.defaultdict(set)
    for n in px.walk(px.parse(text)):
        v = n.value if not n.is_block else None
        if n.key and NUM_RE.match(n.key) and n.is_block and int(n.key) not in krx['states']:
            problems['states'].add(int(n.key))
        if v and NUM_RE.match(v) and n.key in ({'state'} | STATE_TRIGGERS | STATE_EFFECTS) \
                and int(v) not in krx['states']:
            problems['states'].add(int(v))
        if v and TAG_RE.match(v) and n.key in TAG_TRIGGERS and v not in krx['tags']:
            problems['tags'].add(v)
        if n.is_block and n.key in PROVINCE_BLOCKS:
            for c in n.value:
                if c.key == PROVINCE_BLOCKS[n.key] and NUM_RE.match(str(c.value)) \
                        and int(c.value) not in krx['provinces']:
                    problems['provinces'].add(int(c.value))
        if n.is_block and n.key and TAG_RE.match(n.key) and n.key not in krx['tags'] \
                and n.key not in ('AND', 'NOT'):
            problems['tag scopes'].add(n.key)
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('awxe', help="folder of awxe's Formable Nations (the one with descriptor.mod)")
    ap.add_argument('krx', help='folder of Kaiserredux (the one with descriptor.mod)')
    ap.add_argument('--out', default='build', help='where to write the patch (default: ./build)')
    ap.add_argument('--zip', action='store_true', help='also pack the patch into a ZIP')
    args = ap.parse_args()

    for folder, what in ((args.awxe, 'AWXE'), (args.krx, 'Kaiserredux')):
        if not os.path.exists(os.path.join(folder, 'descriptor.mod')):
            sys.exit(f'{what} folder {folder!r} has no descriptor.mod')
    awxe_info = read_descriptor(args.awxe)
    krx = read_krx(args.krx)
    unknown = [i for i in krx['ideologies'] if i not in IDEOLOGIES]
    if unknown:
        print('note: unknown Kaiserredux ideologies use the non-aligned names:', ' '.join(unknown))

    out_mod = os.path.join(args.out, PATCH_FOLDER)
    if os.path.exists(out_mod):
        shutil.rmtree(out_mod)
    os.makedirs(out_mod)

    # AWXE's scripts, rewritten. All of them go into the patch, because the
    # folders they live in are ones Kaiserredux clears when it loads later.
    rw = Rewriter(load_maps(), krx)
    scripts, report = {}, []
    for root, _, files in os.walk(os.path.join(args.awxe, 'common')):
        for f in sorted(files):
            if not f.endswith('.txt'):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, args.awxe).replace(os.sep, '/')
            scripts[rel] = hd.read_text(path)
    for rel, text in sorted(scripts.items()):
        if rel == 'common/countries/cosmetic.txt':
            krx_cos = os.path.join(args.krx, 'common', 'countries', 'cosmetic.txt')
            merged, n = merge_cosmetics(hd.read_text(krx_cos) if os.path.exists(krx_cos) else '', text)
            write(os.path.join(out_mod, rel), merged, bom=True)
            report.append(f'cosmetic.txt: Kaiserredux colours kept, {n} AWXE entries added')
            continue
        new = rw.rewrite(text)
        problems = validate(new, krx)
        for kind, items in sorted(problems.items()):
            report.append(f'WARNING {rel}: unknown {kind}: {" ".join(map(str, sorted(items)))}')
        write(os.path.join(out_mod, rel), new, bom=text.startswith('﻿') or True)

    if krx['define_trigger']:
        write(os.path.join(out_mod, 'common', 'scripted_triggers', 'awxe_krx_compat_triggers.txt'),
              CONTROLS_OR_SUBJECT_OF, bom=True)
        report.append('controls_or_subject_of: defined by the patch')

    cosmetics = cosmetic_tags(args.awxe, scripts, krx['tags'])
    ideologies = krx['ideologies'] or list(IDEOLOGIES)
    for lang, text in localisation(args.awxe, cosmetics, ideologies).items():
        write(os.path.join(out_mod, 'localisation', f'awxe_krx_compat_l_{lang}.yml'), text, bom=True)
    n_flags = flags(args.awxe, out_mod, cosmetics, ideologies)

    # Files of AWXE's that replace a Kaiserredux file outright.
    for root, _, files in os.walk(args.awxe):
        if '.git' in root.split(os.sep):
            continue
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), args.awxe).replace(os.sep, '/')
            if '/' in rel and not rel.startswith(('common/', 'gfx/flags/')) \
                    and os.path.exists(os.path.join(args.krx, rel)):
                report.append(f'WARNING {rel} replaces the Kaiserredux file of the same name')

    deps = [awxe_info['name'] or "awxe's Formable Nations"] + KRX_NAMES
    if krx['name'] and krx['name'] not in deps:
        deps.append(krx['name'])
    descriptor = (f'version="{PATCH_VERSION} (AWXE {awxe_info["version"] or "?"})"\n'
                  'tags={\n\t"Alternative History"\n\t"Gameplay"\n\t"Utilities"\n}\n'
                  f'name="{PATCH_NAME}"\n'
                  f'supported_version="{krx["supported_version"] or awxe_info["supported_version"] or "1.*"}"\n'
                  'dependencies={\n' + ''.join(f'\t"{d}"\n' for d in deps) + '}\n')
    write(os.path.join(out_mod, 'descriptor.mod'), descriptor)
    write(os.path.join(args.out, PATCH_FOLDER + '.mod'), descriptor + f'path="mod/{PATCH_FOLDER}"\n')

    print(f'Patch written to {os.path.abspath(out_mod)}')
    print(f'  {len(scripts)} AWXE script files, {len(cosmetics)} formable cosmetic tags, '
          f'{len(ideologies)} Kaiserredux ideologies, {n_flags} flag files')
    for k, v in sorted(rw.stats.items()):
        print(f'  {k}: {v}')
    for k, v in sorted(rw.notes.items()):
        print(f'  {k}: {" ".join(map(str, sorted(v)))}')
    for line in report:
        print('  ' + line)

    if args.zip:
        zpath = os.path.join(args.out, PATCH_FOLDER + '.zip')
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(os.path.join(args.out, PATCH_FOLDER + '.mod'), PATCH_FOLDER + '.mod')
            for root, _, files in os.walk(out_mod):
                for f in sorted(files):
                    p = os.path.join(root, f)
                    z.write(p, os.path.relpath(p, args.out))
        print(f'ZIP written to {os.path.abspath(zpath)}')


if __name__ == '__main__':
    main()
