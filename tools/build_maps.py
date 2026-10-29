"""Build the vanilla -> Kaiserredux mapping tables in data/.

AWXE's Formable Nations is written for the vanilla map and vanilla tags. This
script compares the vanilla game with Kaiserredux and records, for every
vanilla state, province, continent and tag, what it corresponds to in
Kaiserredux. make_patch.py then uses the tables to rewrite AWXE's scripts.

States and provinces are matched by pixel overlap on map/provinces.bmp, so
renumbered and redrawn states are handled; IDs and colours alone are not
reliable because Kaiserredux reuses some of them for different places.

Usage (needs Python 3, numpy and Pillow):
    python3 tools/build_maps.py <vanilla HOI4 folder> <Kaiserredux folder>
"""
import collections
import json
import os
import re
import sys

import numpy as np

import hoi4data as hd
from tag_overrides import OVERRIDES

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')

# The share of a vanilla province that must lie inside one Kaiserredux province
# before victory points and province names are carried over to it.
PROVINCE_MATCH = 0.3

# Small islands that the two maps draw in different places, matched by hand.
MANUAL_STATES = {
    650: [1273],   # Attu Island
    713: [],       # Kerguelen (not on the Kaiserredux map)
    914: [1146],   # Jan Mayen
    948: [270],    # Easter Island
    1065: [999],   # Penang -> Northwestern Malaya
}


def province_lookup(defs, states):
    colour = {rgb[0] << 16 | rgb[1] << 8 | rgb[2]: pid for pid, (rgb, kind, cont) in defs.items()}
    state_of = {p: sid for sid, s in states.items() for p in s['provinces']}
    return colour, state_of


def majority(counter):
    return max(sorted(counter), key=counter.get) if counter else None


def main(vanilla, krx):
    vdefs, kdefs = hd.read_definitions(vanilla), hd.read_definitions(krx)
    vstates, kstates = hd.read_states(vanilla), hd.read_states(krx)
    vcol, vstate_of = province_lookup(vdefs, vstates)
    kcol, kstate_of = province_lookup(kdefs, kstates)

    print('comparing province maps...')
    vbmp, kbmp = hd.read_province_bitmap(vanilla), hd.read_province_bitmap(krx)
    if vbmp.shape != kbmp.shape:
        sys.exit('the two provinces.bmp files have different sizes')
    pairs, counts = np.unique(vbmp.astype(np.uint64) << np.uint64(24) | kbmp.astype(np.uint64), return_counts=True)

    prov_overlap = collections.defaultdict(collections.Counter)    # vanilla province -> KRX province -> pixels
    state_overlap = collections.defaultdict(collections.Counter)   # vanilla state -> KRX state -> pixels
    owner_votes = collections.defaultdict(collections.Counter)     # KRX state -> vanilla state -> pixels
    for pair, n in zip(pairs.tolist(), counts.tolist()):
        vp, kp = vcol.get(pair >> 24), kcol.get(pair & 0xFFFFFF)
        if vp is None or kp is None:
            continue
        prov_overlap[vp][kp] += n
        vs, ks = vstate_of.get(vp), kstate_of.get(kp)
        if vs is not None and ks is not None:
            state_overlap[vs][ks] += n
            owner_votes[ks][vs] += n

    # Every Kaiserredux state belongs to the vanilla state it overlaps most.
    owner = {ks: majority(v) for ks, v in owner_votes.items()}

    provinces = {}
    for vp, ov in prov_overlap.items():
        kp = majority(ov)
        if ov[kp] >= PROVINCE_MATCH * sum(ov.values()):
            provinces[vp] = kp

    states, unmapped_states = {}, []
    for vs, s in sorted(vstates.items()):
        ov = state_overlap.get(vs)
        if vs in MANUAL_STATES:
            to = MANUAL_STATES[vs]
            if to:
                states[str(vs)] = dict(name=s['name'], to=to, capital=to[0], krx_names=[kstates[k]['name'] for k in to])
            else:
                unmapped_states.append(vs)
            continue
        if not ov:
            unmapped_states.append(vs)
            continue
        # A vanilla state too small to be the main part of any Kaiserredux state
        # maps to the Kaiserredux state it overlaps most.
        to = sorted(ks for ks, o in owner.items() if o == vs) or [majority(ov)]
        # The capital is the part with Kaiserredux's biggest city; ties go to the
        # part that covers more of the vanilla state's own main city.
        main_city = prov_overlap.get(max(s['vps'], key=lambda x: x[1])[0], {}) if s['vps'] else {}
        city_share = collections.Counter()
        for kp, n in main_city.items():
            city_share[kstate_of.get(kp)] += n

        def capital_rank(ks):
            return (max((v for _, v in kstates[ks]['vps']), default=0), city_share[ks], ov[ks])
        capital = max(to, key=capital_rank)
        states[str(vs)] = dict(name=s['name'], to=to, capital=capital,
                               krx_names=[kstates[k]['name'] for k in to])

    # Continents: what Kaiserredux continents (plus exceptions) cover each vanilla continent.
    vconts, kconts = hd.read_continents(vanilla), hd.read_continents(krx)

    def state_continent(states_, defs, names):
        out = {}
        for sid, s in states_.items():
            c = collections.Counter(defs[p][2] for p in s['provinces'] if p in defs and defs[p][1] == 'land')
            if c:
                out[sid] = names[majority(c)]
        return out

    vcont_of, kcont_of = state_continent(vstates, vdefs, vconts), state_continent(kstates, kdefs, kconts)
    as_vanilla = {ks: vcont_of.get(owner.get(ks)) for ks in kcont_of}
    continents = {}
    for name in vconts[1:]:
        base = []
        for kc in kconts[1:]:
            members = [ks for ks, c in kcont_of.items() if c == kc]
            if members and sum(as_vanilla[ks] == name for ks in members) * 2 > len(members):
                base.append(kc)
        continents[name] = dict(
            continents=base,
            add=sorted(ks for ks, c in kcont_of.items() if as_vanilla[ks] == name and c not in base),
            remove=sorted(ks for ks, c in kcont_of.items() if c in base and as_vanilla[ks] not in (name, None)),
        )

    # Tags: keep the tag where Kaiserredux has it, otherwise use the Kaiserredux
    # tags based in the same capital; tag_overrides.py corrects the rest.
    vtags, ktags = hd.read_country_tags(vanilla), hd.read_country_tags(krx)
    vcap, kcap = hd.read_capitals(vanilla), hd.read_capitals(krx)
    tags = {}
    for t in sorted(vtags | set(OVERRIDES)):
        if t in OVERRIDES:
            tags[t] = OVERRIDES[t]
        elif t in ktags:
            tags[t] = [t]
        else:
            area = set(states.get(str(vcap.get(t)), {}).get('to', []))
            tags[t] = sorted(k for k, c in kcap.items()
                             if c in area and k in ktags and not re.fullmatch(r'D\d\d', k))
    bad = sorted({k for v in tags.values() for k in v} - ktags)
    if bad:
        print('warning: tag_overrides.py names tags Kaiserredux does not have:', ' '.join(bad))

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, 'statemap.json'), 'w') as f:
        json.dump(dict(states=states, unmapped=unmapped_states), f, indent=1, ensure_ascii=False)
    with open(os.path.join(DATA, 'provincemap.json'), 'w') as f:
        json.dump({str(k): v for k, v in sorted(provinces.items())}, f, separators=(',', ':'))
    with open(os.path.join(DATA, 'continentmap.json'), 'w') as f:
        json.dump(continents, f, indent=1)
    with open(os.path.join(DATA, 'tagmap.json'), 'w') as f:
        json.dump(tags, f, indent=1)

    sizes = collections.Counter(len(v['to']) for v in states.values())
    print(f'{len(states)} vanilla states mapped ({dict(sorted(sizes.items()))} Kaiserredux states each), '
          f'{len(unmapped_states)} without land overlap: {unmapped_states}')
    print(f'{len(set(owner))} of {len(kstates)} Kaiserredux states covered, {len(provinces)} provinces matched')
    for name, c in continents.items():
        print(f'  {name}: {c["continents"]} +{len(c["add"])} -{len(c["remove"])}')
    print(f'{len(tags)} vanilla tags, {sum(1 for v in tags.values() if not v)} without a Kaiserredux counterpart')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
